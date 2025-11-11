import { useState, useEffect } from 'react'
import { getTransfers, deleteTransfer, stopContinuousWatch, getTransferLogs } from '../services/api'

/**
 * ActiveTransfers Component
 * Shows active transfers (pending, copying, continuous watch)
 * Allows user to delete/cancel active transfers
 *
 * Week 6: Display continuous watch transfers with delete button
 */
function ActiveTransfers({ onActiveTransfersChange }) {
  const [transfers, setTransfers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedLogs, setSelectedLogs] = useState(null)
  const [expandedTransferId, setExpandedTransferId] = useState(null)

  // Auto-refresh every 10 seconds (reduced to prevent resource exhaustion)
  useEffect(() => {
    loadActiveTransfers()
    const interval = setInterval(loadActiveTransfers, 10000)
    return () => clearInterval(interval)
  }, [])

  async function loadActiveTransfers() {
    try {
      const result = await getTransfers(null, 100)
      // Filter for ACTIVE transfers only (pending, copying, validating)
      const active = result.items.filter(t =>
        ['pending', 'copying', 'validating'].includes(t.status) ||
        t.is_continuous_watch === true
      )
      setTransfers(active)
      setError(null)

      // Notify parent if count changed
      if (onActiveTransfersChange) {
        onActiveTransfersChange(active.length)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleDeleteTransfer(transferId, isContinuousWatch) {
    const message = isContinuousWatch
      ? `Delete continuous watch transfer #${transferId}? This will stop monitoring and remove the record.`
      : `Delete transfer #${transferId}?`

    if (!confirm(message)) {
      return
    }

    try {
      await deleteTransfer(transferId)
      // Refresh the list
      loadActiveTransfers()
    } catch (err) {
      alert(`Failed to delete transfer: ${err.message}`)
    }
  }

  async function handleStopWatch(transferId) {
    if (!confirm(`Stop continuous watch for transfer #${transferId}?`)) {
      return
    }

    try {
      await stopContinuousWatch(transferId)
      // Refresh the list
      loadActiveTransfers()
    } catch (err) {
      alert(`Failed to stop watch: ${err.message}`)
    }
  }

  async function showLogs(transferId) {
    try {
      const result = await getTransferLogs(transferId)
      setSelectedLogs(result)
      setExpandedTransferId(expandedTransferId === transferId ? null : transferId)
    } catch (err) {
      console.error('Failed to load logs:', err)
      alert('Failed to load logs')
    }
  }

  if (isLoading) {
    return <div className="loading">Loading active transfers...</div>
  }

  if (transfers.length === 0) {
    return (
      <div className="empty-state">
        <p> No active transfers</p>
        <p className="hint">All transfers are completed or idle.</p>
      </div>
    )
  }

  return (
    <div className="active-transfers">
      <h2>Active Transfers ({transfers.length})</h2>
      {error && <div className="error-banner">{error}</div>}

      <div className="transfers-container">
        {transfers.map(transfer => (
          <div key={transfer.id} className={`transfer-card active ${transfer.status}`}>
            <div className="transfer-header">
              <div className="transfer-title">
                <h3>#{transfer.id} - {transfer.file_name}</h3>
                <div className="status-badges">
                  <span className={`badge status-${transfer.status}`}>
                    {transfer.status.toUpperCase()}
                  </span>
                  {transfer.is_continuous_watch && (
                    <span className="badge badge-continuous">
                       Continuous Watch
                    </span>
                  )}
                  {transfer.operation_mode === 'move' && (
                    <span className="badge badge-move" title="MOVE mode - deletes originals">
                      ↔ MOVE
                    </span>
                  )}
                  {transfer.operation_mode === 'copy' && (
                    <span className="badge badge-copy" title="COPY mode - keeps originals">
                       COPY
                    </span>
                  )}
                </div>
              </div>

              <div className="transfer-paths">
                <p><strong>Source:</strong> {transfer.source_path}</p>
                <p><strong>Destination:</strong> {transfer.destination_path}</p>
              </div>

              {transfer.is_continuous_watch && (
                <div className="continuous-watch-stats">
                  <p>
                    <strong>Files Transferred:</strong> {transfer.continuous_files_transferred}
                  </p>
                  <p>
                    <strong>Last Check:</strong>{' '}
                    {transfer.last_watch_check_at
                      ? new Date(transfer.last_watch_check_at).toLocaleTimeString()
                      : 'Never'}
                  </p>
                </div>
              )}
            </div>

            <div className="transfer-actions">
              <button
                className="btn btn-secondary"
                onClick={() => showLogs(transfer.id)}
              >
                 Logs
              </button>

              {transfer.is_continuous_watch && (
                <button
                  className="btn btn-warning"
                  onClick={() => handleStopWatch(transfer.id)}
                  title="Stop continuous monitoring"
                >
                  ⏹ Stop Watch
                </button>
              )}

              <button
                className="btn btn-danger"
                onClick={() => handleDeleteTransfer(transfer.id, transfer.is_continuous_watch)}
                title={transfer.is_continuous_watch ? 'Cancel and delete continuous watch' : 'Delete transfer'}
              >
                 Delete
              </button>
            </div>

            {/* Expandable Logs Section */}
            {expandedTransferId === transfer.id && selectedLogs && (
              <div className="logs-section">
                <h4>Audit Logs</h4>
                <div className="logs-list">
                  {selectedLogs.items && selectedLogs.items.length > 0 ? (
                    selectedLogs.items.slice(-10).map((log, idx) => (
                      <div key={idx} className="log-entry">
                        <span className="log-time">
                          {new Date(log.created_at).toLocaleTimeString()}
                        </span>
                        <span className={`log-type ${log.event_type}`}>
                          {log.event_type}
                        </span>
                        <span className="log-message">{log.message}</span>
                      </div>
                    ))
                  ) : (
                    <p>No logs available</p>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ActiveTransfers
