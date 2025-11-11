/**
 * Ketter 3.0 - API Service
 * Simple API client for backend communication
 *
 * MRC: Simple fetch-based API client
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Create a new transfer
 * Week 5: Supports ZIP Smart + Watch Mode
 * Week 6: Supports Operation Mode (COPY/MOVE) + Continuous Watch Mode
 */
export async function createTransfer(
  sourcePath,
  destinationPath,
  watchMode = false,
  settleTime = 30,
  operationMode = 'copy',      // NOVO
  isContinuousWatch = false    // NOVO Week 6
) {
  const response = await fetch(`${API_BASE_URL}/transfers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      source_path: sourcePath,
      destination_path: destinationPath,
      watch_mode_enabled: watchMode,
      settle_time_seconds: settleTime,
      operation_mode: operationMode,        // NOVO
      is_continuous_watch: isContinuousWatch // NOVO Week 6
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create transfer');
  }

  return response.json();
}

/**
 * Get all transfers
 */
export async function getTransfers(status = null, limit = 100) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit);

  const response = await fetch(`${API_BASE_URL}/transfers?${params}`);

  if (!response.ok) {
    throw new Error('Failed to fetch transfers');
  }

  return response.json();
}

/**
 * Get transfer by ID
 */
export async function getTransfer(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}`);

  if (!response.ok) {
    throw new Error('Transfer not found');
  }

  return response.json();
}

/**
 * Get transfer checksums
 */
export async function getTransferChecksums(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}/checksums`);

  if (!response.ok) {
    throw new Error('Failed to fetch checksums');
  }

  return response.json();
}

/**
 * Get transfer audit logs
 */
export async function getTransferLogs(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}/logs`);

  if (!response.ok) {
    throw new Error('Failed to fetch logs');
  }

  return response.json();
}

/**
 * Get recent transfer history
 */
export async function getRecentTransfers(days = 30) {
  const response = await fetch(`${API_BASE_URL}/transfers/history/recent?days=${days}`);

  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }

  return response.json();
}

/**
 * Cancel a transfer in progress
 * Week 6: Cancel any transfer (pending, copying, verifying)
 */
export async function cancelTransfer(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}/cancel`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel transfer');
  }

  return response.json();
}

/**
 * Stop continuous watch monitoring for a transfer
 * Week 6: Stop continuous watch job
 */
export async function stopContinuousWatch(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}/stop-watch`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop continuous watch');
  }

  return response.json();
}

/**
 * Delete transfer (cancels job if active)
 * Week 6: Can delete any transfer (will cancel in progress ones)
 */
export async function deleteTransfer(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete transfer');
  }

  return response.ok;
}

/**
 * Download PDF report for transfer
 */
export async function downloadTransferReport(id) {
  const response = await fetch(`${API_BASE_URL}/transfers/${id}/report`);

  if (!response.ok) {
    throw new Error('Failed to generate PDF report');
  }

  // Get filename from Content-Disposition header
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = `ketter_report_transfer_${id}.pdf`;

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }

  // Get blob and trigger download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Get system status
 */
export async function getStatus() {
  const response = await fetch(`${API_BASE_URL}/status`);

  if (!response.ok) {
    throw new Error('Failed to fetch status');
  }

  return response.json();
}

/**
 * Get all configured volumes
 */
export async function getVolumes() {
  const response = await fetch(`${API_BASE_URL}/volumes`);

  if (!response.ok) {
    throw new Error('Failed to fetch volumes');
  }

  return response.json();
}

/**
 * Get only available (mounted) volumes
 */
export async function getAvailableVolumes() {
  const response = await fetch(`${API_BASE_URL}/volumes/available`);

  if (!response.ok) {
    throw new Error('Failed to fetch available volumes');
  }

  return response.json();
}
