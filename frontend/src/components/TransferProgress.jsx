import { useState } from 'react'
import { getTransferChecksums } from '../services/api'

/**
 * TransferProgress Component
 * Shows active transfers and allows checksum inspection.
 */
function TransferProgress({ transfers = [], isLoading = false, error = null, onCancel }) {
  const [selectedTransfer, setSelectedTransfer] = useState(null)
  const [checksums, setChecksums] = useState(null)

  const activeTransfers = transfers.filter((t) =>
    ['pending', 'validating', 'copying', 'verifying'].includes(t.status)
  )

  async function handleStopTransfer(transfer) {
    if (
      !window.confirm(`Stop transfer: ${transfer.file_name}?\n\nThis will cancel the active transfer and move it to history.`)
    ) {
      return
    }

    await onCancel?.(transfer.id)
  }

  async function showChecksums(transferId) {
    try {
      const result = await getTransferChecksums(transferId)
      setChecksums(result)
      setSelectedTransfer(transferId)
    } catch (err) {
      console.error('Failed to load checksums:', err)
    }
  }

  if (isLoading) {
    return <div className="loading">Loading active transfers...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  if (activeTransfers.length === 0) {
    return (
      <div className="empty-state">
        <p>No active transfers at the moment.</p>
        <p className="hint">Create a new transfer above to get started.</p>
      </div>
    )
  }

  return (
    <div className="transfer-progress">
      <div className="info-box info-active-transfers">
        <p>
          These transfers are in progress. Use <strong>Stop Transfer</strong> to pause an active transfer (it will move to
          History). Click <strong>View Audit Trail</strong> to see detailed logs.
        </p>
      </div>
      {activeTransfers.map((transfer) => (
        <div key={transfer.id} className="transfer-card active">
          <div className="transfer-header">
            <h3>{transfer.file_name}</h3>
            <div className="badge-group">
              {transfer.is_folder_transfer && (
                <span className="badge badge-folder" title="Folder transfer with ZIP Smart">
                  Folder ({transfer.file_count || '?'} files)
                </span>
              )}
              {transfer.watch_mode_enabled && (
                <span className="badge badge-watch" title={`Watching for ${transfer.settle_time_seconds}s settle time`}>
                  Watching ({transfer.settle_time_seconds}s)
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
          </div>

          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${transfer.progress_percent}%` }}>
              <span className="progress-text">{transfer.progress_percent}%</span>
            </div>
          </div>

          <div className="transfer-actions">
            <button className="btn btn-icon" onClick={() => showChecksums(transfer.id)} title="View SHA-256 checksums">
              View Checksums
            </button>
            {['pending', 'validating', 'copying', 'verifying'].includes(transfer.status) && (
              <button
                className="btn btn-icon btn-danger-icon"
                onClick={() => handleStopTransfer(transfer)}
                title="Stop this active transfer and move to history"
              >
                Stop Transfer
              </button>
            )}
          </div>
        </div>
      ))}

      {selectedTransfer && checksums && (
        <ChecksumModal
          checksums={checksums}
          onClose={() => {
            setSelectedTransfer(null)
            setChecksums(null)
          }}
        />
      )}
    </div>
  )
}

/**
 * Checksum Modal Component
 */
function ChecksumModal({ checksums, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Triple SHA-256 Checksums</h3>
          <button className="btn-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="checksum-list">
          {checksums.items.map((checksum) => (
            <div key={checksum.id} className="checksum-item">
              <div className="checksum-type">{checksum.checksum_type.toUpperCase()}</div>
              <div className="checksum-value">{checksum.checksum_value}</div>
              <div className="checksum-meta">Calculated in {checksum.calculation_duration_seconds}s</div>
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <button className="btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

export default TransferProgress
