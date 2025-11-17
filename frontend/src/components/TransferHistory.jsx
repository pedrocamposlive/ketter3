import { useState, useEffect } from 'react'
import { getRecentTransfers, getTransferLogs, deleteTransfer, downloadTransferReport } from '../services/api'

/**
 * TransferHistory Component
 * Shows completed/failed transfers from last 30 days
 *
 * MRC: Simple history view with audit trail access
 * Week 5: Shows folder and watch mode indicators
 */
function TransferHistory() {
  const [transfers, setTransfers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTransfer, setSelectedTransfer] = useState(null)
  const [logs, setLogs] = useState(null)

  useEffect(() => {
    loadHistory()
  }, [])

  async function loadHistory() {
    try {
      const result = await getRecentTransfers(30)
      // Filter for completed/failed only
      const completed = result.items.filter(t =>
        ['completed', 'failed', 'cancelled'].includes(t.status)
      )
      setTransfers(completed)
      setIsLoading(false)
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
    }
  }

  async function showLogs(transferId) {
    try {
      const result = await getTransferLogs(transferId)
      setLogs(result)
      setSelectedTransfer(transferId)
    } catch (err) {
      console.error('Failed to load logs:', err)
    }
  }

  async function handleDelete(transferId, fileName) {
    if (!confirm(`Delete from history: ${fileName}?\n\nThis removes the transfer record from history (files are not affected).`)) {
      return
    }

    try {
      await deleteTransfer(transferId)
      loadHistory()
    } catch (err) {
      alert(`Failed to delete from history: ${err.message}`)
    }
  }

  async function handleDownloadReport(transferId) {
    try {
      await downloadTransferReport(transferId)
    } catch (err) {
      alert(`Failed to download report: ${err.message}`)
    }
  }

  if (isLoading) {
    return <div className="loading">Loading transfer history...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  if (transfers.length === 0) {
    return (
      <div className="empty-state">
        <p>No transfer history available.</p>
        <p className="hint">Completed transfers will appear here.</p>
      </div>
    )
  }

  return (
    <div className="transfer-history">
      <div className="info-box info-history">
        <p>Transfer history from the last 30 days. Use <strong>View Audit Trail</strong> to check logs, <strong>Download Report</strong> to get a PDF, or <strong>Delete from History</strong> to remove from records (files are not affected).</p>
      </div>
      <div className="history-list">
        {transfers.map(transfer => (
          <div key={transfer.id} className={`transfer-card ${transfer.status}`}>
            <div className="transfer-header">
              <h3>{transfer.file_name}</h3>
              <div className="badge-group">
                {transfer.is_folder_transfer && (
                  <span className="badge badge-folder" title="Folder transfer with ZIP Smart">
                     Folder ({transfer.file_count || '?'} files)
                  </span>
                )}
                {transfer.watch_mode_enabled && (
                  <span className="badge badge-watch" title={`Used watch mode with ${transfer.settle_time_seconds}s settle time`}>
                     Watch Mode
                  </span>
                )}
                <span className={`status-badge status-${transfer.status}`}>
                  {transfer.status.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="transfer-info">
              <div className="info-row">
                <span className="label">Source:</span>
                <span className="value">{transfer.source_path}</span>
              </div>
              <div className="info-row">
                <span className="label">Destination:</span>
                <span className="value">{transfer.destination_path}</span>
              </div>
              <div className="info-row">
                <span className="label">Size:</span>
                <span className="value">{formatBytes(transfer.file_size)}</span>
              </div>
              <div className="info-row">
                <span className="label">Created:</span>
                <span className="value">{formatDate(transfer.created_at)}</span>
              </div>
              {transfer.completed_at && (
                <div className="info-row">
                  <span className="label">Completed:</span>
                  <span className="value">{formatDate(transfer.completed_at)}</span>
                </div>
              )}
              {transfer.watch_mode_enabled && transfer.watch_started_at && transfer.watch_triggered_at && (
                <div className="info-row">
                  <span className="label">Watch Duration:</span>
                  <span className="value">
                    {formatWatchDuration(transfer.watch_started_at, transfer.watch_triggered_at)}
                  </span>
                </div>
              )}
              {transfer.error_message && (
                <div className="info-row error-row">
                  <span className="label">Error:</span>
                  <span className="value error-text">{transfer.error_message}</span>
                </div>
              )}
            </div>

            <div className="transfer-actions">
              <button
                className="btn btn-icon"
                onClick={() => handleDownloadReport(transfer.id)}
                title="Download PDF report"
              >
                 Download Report
              </button>
              <button
                className="btn btn-icon"
                onClick={() => showLogs(transfer.id)}
                title="View audit trail"
              >
                View Audit Trail
              </button>
              <button
                className="btn btn-icon btn-danger-icon"
                onClick={() => handleDelete(transfer.id, transfer.file_name)}
                title="Delete from history (files not affected)"
              >
                Delete from History
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedTransfer && logs && (
        <AuditLogModal
          logs={logs}
          onClose={() => {
            setSelectedTransfer(null)
            setLogs(null)
          }}
        />
      )}
    </div>
  )
}

/**
 * Audit Log Modal Component
 */
function AuditLogModal({ logs, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Audit Trail (Transfer #{logs.transfer_id})</h3>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="audit-log-list">
          {logs.items.map((log, index) => (
            <div key={log.id} className="audit-log-item">
              <div className="log-number">{index + 1}</div>
              <div className="log-content">
                <div className="log-event">
                  <span className={`event-badge event-${log.event_type}`}>
                    {log.event_type.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <div className="log-message">{log.message}</div>
                <div className="log-timestamp">{formatDate(log.created_at)}</div>
                {log.event_metadata && (
                  <details className="log-metadata">
                    <summary>Metadata</summary>
                    <pre>{JSON.stringify(log.event_metadata, null, 2)}</pre>
                  </details>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <div className="log-summary">
            Total events: {logs.total}
          </div>
          <button className="btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * Format watch duration between two timestamps
 * Week 5: Shows how long watch mode waited
 */
function formatWatchDuration(startedAt, triggeredAt) {
  const start = new Date(startedAt)
  const end = new Date(triggeredAt)
  const durationMs = end - start
  const durationSeconds = Math.floor(durationMs / 1000)

  if (durationSeconds < 60) {
    return `${durationSeconds}s`
  } else if (durationSeconds < 3600) {
    const minutes = Math.floor(durationSeconds / 60)
    const seconds = durationSeconds % 60
    return `${minutes}m ${seconds}s`
  } else {
    const hours = Math.floor(durationSeconds / 3600)
    const minutes = Math.floor((durationSeconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }
}

export default TransferHistory
