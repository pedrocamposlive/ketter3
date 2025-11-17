/* -------------------------------------------------------------------------
   API helpers and shared clients
---------------------------------------------------------------------------- */
export class ApiError extends Error {
  constructor(message, statusCode = 0) {
    super(message)
    this.name = 'ApiError'
    this.statusCode = statusCode
  }
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const DEFAULT_HEADERS = {
  'X-Ketter-Client': 'UI',
}

function hasJsonContentType(headers) {
  return Object.keys(headers).some((key) => key.toLowerCase() === 'content-type')
}

function buildQueryString(params = {}) {
  const parts = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)

  return parts.length ? `?${parts.join('&')}` : ''
}

function buildUrl(path, params = {}) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${normalizedPath}${buildQueryString(params)}`
}

async function secureFetchRaw(path, options = {}) {
  const headers = {
    ...DEFAULT_HEADERS,
    ...(options.headers || {}),
  }

  const shouldSerializeBody =
    options.body && typeof options.body === 'object' && !(options.body instanceof FormData)

  if (shouldSerializeBody && !hasJsonContentType(headers)) {
    headers['Content-Type'] = 'application/json'
  }

  const fetchOptions = {
    ...options,
    headers,
    body: shouldSerializeBody ? JSON.stringify(options.body) : options.body,
  }

  const url = `${API_BASE}${path}`

  try {
    return await fetch(url, fetchOptions)
  } catch (error) {
    throw new ApiError(error?.message || 'Network request failed', 0)
  }
}

async function secureFetch(path, options = {}) {
  const response = await secureFetchRaw(path, options)

  if (!response.ok) {
    let errorMessage = response.statusText || 'API request failed'
    try {
      const text = await response.text()
      if (text) {
        const parsed = JSON.parse(text)
        errorMessage = parsed.detail || parsed.message || parsed.error || text
      }
    } catch (ignored) {
      // Ignore parse failures, keep original errorMessage
    }

    throw new ApiError(errorMessage, response.status)
  }

  if (response.status === 204) {
    return null
  }

  const text = await response.text()
  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch (error) {
    return text
  }
}

function getFileNameFromDisposition(value) {
  if (!value) return null
  const match = /filename="?([^";]+)"?/i.exec(value)
  return match ? match[1] : null
}

/* -------------------------------------------------------------------------
   Transfer helpers
---------------------------------------------------------------------------- */
export async function createTransfer(payload) {
  return secureFetch('/transfers', {
    method: 'POST',
    body: payload,
  })
}

export async function getTransfers({ status, limit = 100, offset = 0 } = {}) {
  const params = { limit, offset }
  if (status) {
    params.status = status
  }
  return secureFetch(buildUrl('/transfers', params))
}

export async function getTransfer(transferId) {
  return secureFetch(`/transfers/${transferId}`)
}

export async function getTransferChecksums(transferId) {
  return secureFetch(`/transfers/${transferId}/checksums`)
}

export async function getTransferLogs(transferId) {
  return secureFetch(`/transfers/${transferId}/logs`)
}

export async function deleteTransfer(transferId) {
  return secureFetch(`/transfers/${transferId}`, {
    method: 'DELETE',
  })
}

export async function downloadTransferReport(transferId) {
  const response = await secureFetchRaw(`/transfers/${transferId}/report`, {
    headers: {
      Accept: 'application/pdf',
    },
  })

  if (!response.ok) {
    throw new ApiError('Failed to download transfer report', response.status)
  }

  const blob = await response.blob()
  const filename =
    getFileNameFromDisposition(response.headers.get('Content-Disposition')) ||
    `transfer-${transferId}-report.pdf`
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 3000)
}

export async function getRecentTransfers({ days = 30 } = {}) {
  return secureFetch(buildUrl('/transfers/history/recent', { days }))
}

export async function pauseWatchMode(transferId) {
  return secureFetch(`/transfers/${transferId}/pause-watch`, {
    method: 'POST',
  })
}

export async function resumeWatchMode(transferId) {
  return secureFetch(`/transfers/${transferId}/resume-watch`, {
    method: 'POST',
  })
}

export async function getWatchHistory(transferId, { limit = 100, offset = 0 } = {}) {
  return secureFetch(buildUrl(`/transfers/${transferId}/watch-history`, { limit, offset }))
}

export async function cancelTransfer(transferId) {
  return secureFetch(`/transfers/${transferId}/cancel`, {
    method: 'POST',
  })
}

const ALERT_STATUS_TONES = {
  failed: 'critical',
  cancelled: 'warning',
  validating: 'warning',
  copying: 'warning',
  verifying: 'warning',
  pending: 'info',
  completed: 'success',
}

export async function getAlerts({ limit = 6 } = {}) {
  const payload = await getTransfers({ limit })
  const items = Array.isArray(payload?.items) ? payload.items : []
  const filtered = items.filter((transfer) => transfer.status !== undefined)
  return filtered.slice(0, limit).map((transfer) => ({
    id: `transfer-alert-${transfer.id}`,
    tone: ALERT_STATUS_TONES[transfer.status] || 'info',
    title: `${transfer.file_name} · ${transfer.status?.toUpperCase()}`,
    detail: transfer.error_message || `Transfer ${transfer.status}`,
    timestamp: transfer.updated_at || transfer.completed_at || transfer.created_at,
  }))
}

export async function getAuditLogs({ days = 1, limit = 200 } = {}) {
  const payload = await getRecentTransfers({ days })
  const items = Array.isArray(payload?.items) ? payload.items : []
  return items.slice(0, limit).map((transfer) => ({
    timestamp: transfer.completed_at || transfer.updated_at || transfer.created_at,
    status: transfer.status?.toUpperCase() || 'UNKNOWN',
    detail: transfer.error_message || `${transfer.file_name} · ${transfer.status}`,
  }))
}

/* -------------------------------------------------------------------------
   Status / health
---------------------------------------------------------------------------- */
export async function getStatus() {
  return secureFetch('/status')
}

export async function getSystemHealth() {
  return secureFetch('/health')
}

/* -------------------------------------------------------------------------
   Volume management
---------------------------------------------------------------------------- */
export async function getVolumes() {
  return secureFetch('/volumes')
}

export async function getAvailableVolumes() {
  return secureFetch('/volumes/available')
}

export async function reloadVolumes() {
  return secureFetch('/volumes/reload', {
    method: 'POST',
  })
}

export async function validateVolumePath(path) {
  if (!path) {
    throw new ApiError('Path is required for validation', 400)
  }
  return secureFetch(buildUrl('/volumes/validate', { path }))
}
