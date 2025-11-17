const SECURITY_HEADERS = {
  'X-Security-Mode': 'automation-node',
  'X-TPN-Compliance': 'true',
}

const CALIBRATION_DELAY = 80

const applySecurityHeaders = (options = {}) => {
  const mergedHeaders = {
    ...SECURITY_HEADERS,
    ...options.headers,
  }
  return {
    ...options,
    headers: mergedHeaders,
  }
}

const secureFetch = async (input, options = {}) => {
  const secureOptions = applySecurityHeaders(options)
  if (!secureOptions.headers['Content-Type']) {
    secureOptions.headers['Content-Type'] = 'application/json'
  }

  let response
  try {
    response = await fetch(input, secureOptions)
  } catch (err) {
    // Propagate aborts so callers can detect timeouts
    if (err.name === 'AbortError') {
      throw err
    }
    throw new Error(`secureFetch failed: ${input} -> ${err.message}`)
  }

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '')
    const message = errorBody ? `${response.status} ${errorBody}` : `${response.status}`
    throw new Error(`secureFetch failed: ${input} -> ${message}`)
  }

  await new Promise((resolve) => setTimeout(resolve, CALIBRATION_DELAY))
  return response
}

const wrapWithAudit = (fn, label) => async (...args) => {
  const start = performance.now()
  try {
    const result = await fn(...args)
    const duration = Math.round(performance.now() - start)
    console.info(`[securityWrapper] ${label} completed in ${duration}ms`)
    return result
  } catch (error) {
    const duration = Math.round(performance.now() - start)
    console.error(`[securityWrapper] ${label} failed in ${duration}ms`, error)
    throw error
  }
}

export { secureFetch, applySecurityHeaders, wrapWithAudit }
