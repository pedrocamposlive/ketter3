import { useState, useEffect } from 'react'
import { getRecentTransfers, getTransferLogs, deleteTransfer, cancelTransfer, downloadTransferReport } from '../services/api'

/**
 * TransferHistory Component
 * Shows BOTH active and completed transfers from last 30 days
 *
 * MRC: Simple history view with audit trail access
 * Week 5: Shows folder and watch mode indicators
 * Week 6: Auto-refresh every 10s, shows active transfers first
 */
function TransferHistory() {
  const [transfers, setTransfers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTransfer, setSelectedTransfer] = useState(null)
  const [logs, setLogs] = useState(null)

  // Week 6: Multi-select functionality
  const [selectedTransfers, setSelectedTransfers] = useState(new Set())
  const [selectAll, setSelectAll] = useState(false)

  useEffect(() => {
    loadHistory()
    // Auto-refresh every 10 seconds to show real-time updates
    const interval = setInterval(loadHistory, 10000)
    return () => clearInterval(interval)
  }, [])

  async function loadHistory() {
    try {
      const result = await getRecentTransfers(30)
      // Show BOTH active and completed transfers
      // Active: pending, copying, validating, or continuous watch
      // Completed: completed, failed, cancelled
      const allTransfers = result.items.sort((a, b) => {
        // Active transfers first, then completed
        const aActive = ['pending', 'copying', 'validating'].includes(a.status) || a.is_continuous_watch
        const bActive = ['pending', 'copying', 'validating'].includes(b.status) || b.is_continuous_watch
        if (aActive === bActive) {
          // Same status type, sort by date (newest first)
          return new Date(b.created_at) - new Date(a.created_at)
        }
        // Active transfers first
        return aActive ? -1 : 1
      })
      setTransfers(allTransfers)
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

  async function handleCancel(transferId, status) {
    const message = status === 'copying' || status === 'pending' || status === 'verifying'
      ? `⏸ Cancelar transferência #${transferId}? Isto vai parar o trabalho em progresso.`
      : ` Operação não suportada para status: ${status}`

    if (!confirm(message)) {
      return
    }

    try {
      await cancelTransfer(transferId)
      // Refresh history
      loadHistory()
    } catch (err) {
      alert(`Failed to cancel transfer: ${err.message}`)
    }
  }

  async function handleDelete(transferId, status) {
    // Se está em progresso, sugerir cancelar primeiro
    if (status === 'copying' || status === 'pending' || status === 'verifying') {
      const confirmCancel = confirm(
        ` Esta transferência ainda está em progresso!\n\n` +
        `Opções:\n` +
        `- OK: Cancelar E deletar (recomendado)\n` +
        `- Cancelar: Voltar\n\n` +
        `A transferência será interrompida e todos os registos serão removidos.`
      )

      if (!confirmCancel) {
        return
      }
    } else {
      // Para transferências completas, confirmação simples
      if (!confirm('Tem certeza que quer deletar este registro de transferência?')) {
        return
      }
    }

    try {
      await deleteTransfer(transferId)
      // Refresh history
      loadHistory()
    } catch (err) {
      alert(`Failed to delete transfer: ${err.message}`)
    }
  }

  async function handleDownloadReport(transferId) {
    try {
      await downloadTransferReport(transferId)
    } catch (err) {
      alert(`Failed to download report: ${err.message}`)
    }
  }

  // Toggle individual transfer selection
  function toggleSelectTransfer(transferId) {
    const newSelected = new Set(selectedTransfers)
    if (newSelected.has(transferId)) {
      newSelected.delete(transferId)
    } else {
      newSelected.add(transferId)
    }
    setSelectedTransfers(newSelected)
  }

  // Toggle select all
  function handleSelectAll(e) {
    if (e.target.checked) {
      const allIds = new Set(transfers.map(t => t.id))
      setSelectedTransfers(allIds)
      setSelectAll(true)
    } else {
      setSelectedTransfers(new Set())
      setSelectAll(false)
    }
  }

  // Delete multiple transfers
  async function handleDeleteMultiple() {
    if (selectedTransfers.size === 0) {
      alert('Por favor, selecione pelo menos uma transferência')
      return
    }

    const count = selectedTransfers.size
    if (!confirm(`Deletar ${count} transferência(s)? Isto vai cancelar e deletar todos os registos selecionados.`)) {
      return
    }

    let deleted = 0
    let failed = 0

    for (const transferId of selectedTransfers) {
      try {
        await deleteTransfer(transferId)
        deleted++
      } catch (err) {
        console.error(`Failed to delete transfer ${transferId}:`, err)
        failed++
      }
    }

    alert(`Resultado: ${deleted} deletada(s), ${failed} falhada(s)`)
    setSelectedTransfers(new Set())
    setSelectAll(false)
    loadHistory()
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
      {/* Selection toolbar */}
      <div className="selection-toolbar">
        <div className="selection-controls">
          <label className="select-all-checkbox">
            <input
              type="checkbox"
              checked={selectAll}
              onChange={handleSelectAll}
            />
            <span>Select All ({transfers.length})</span>
          </label>
          {selectedTransfers.size > 0 && (
            <div className="selection-info">
              <span className="selected-count">
                {selectedTransfers.size} transferência(s) selecionada(s)
              </span>
              <button
                className="btn btn-small btn-danger"
                onClick={handleDeleteMultiple}
              >
                Delete Selected
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="history-list">
        {transfers.map(transfer => (
          <div
            key={transfer.id}
            className={`transfer-card ${transfer.status} ${selectedTransfers.has(transfer.id) ? 'selected' : ''}`}
          >
            <div className="transfer-header">
              <div className="transfer-checkbox">
                <input
                  type="checkbox"
                  checked={selectedTransfers.has(transfer.id)}
                  onChange={() => toggleSelectTransfer(transfer.id)}
                />
              </div>
              <h3>{transfer.file_name}</h3>
              <div className="badge-group">
                {transfer.is_continuous_watch && (
                  <span className="badge badge-continuous" title="Continuous watch mode - monitoring folder indefinitely">
                    Continuous Watch
                  </span>
                )}
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
                {transfer.operation_mode === 'move' && (
                  <span className="badge badge-move" title="MOVE mode - deletes originals after transfer">
                    MOVE
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
              {transfer.is_continuous_watch && (
                <>
                  <div className="info-row">
                    <span className="label">Files Transferred:</span>
                    <span className="value">{transfer.continuous_files_transferred}</span>
                  </div>
                  {transfer.last_watch_check_at && (
                    <div className="info-row">
                      <span className="label">Last Check:</span>
                      <span className="value">{formatDate(transfer.last_watch_check_at)}</span>
                    </div>
                  )}
                </>
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
                className="btn btn-small"
                onClick={() => handleDownloadReport(transfer.id)}
              >
                Download Report
              </button>
              <button
                className="btn btn-small"
                onClick={() => showLogs(transfer.id)}
              >
                View Audit Trail
              </button>
              {/* Show cancel button for in-progress transfers */}
              {['pending', 'copying', 'verifying'].includes(transfer.status) && (
                <button
                  className="btn btn-small btn-warning"
                  onClick={() => handleCancel(transfer.id, transfer.status)}
                  title="Stop the transfer and allow deletion"
                >
                  Cancel
                </button>
              )}
              <button
                className="btn btn-small btn-danger"
                onClick={() => handleDelete(transfer.id, transfer.status)}
                title={['pending', 'copying', 'verifying'].includes(transfer.status)
                  ? 'Cancel and delete this transfer'
                  : 'Delete this transfer record'
                }
              >
                Delete
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
