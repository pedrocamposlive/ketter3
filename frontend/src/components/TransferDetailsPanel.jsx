import React from 'react'
import PropTypes from 'prop-types'

const formatTimestamp = (value) => {
  if (!value) return 'Awaiting sync'
  try {
    return new Date(value).toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return value
  }
}

function TransferDetailsPanel({ transfer }) {
  if (!transfer) {
    return (
      <div className="transfer-details-panel empty">
        <h3>Transfer Details</h3>
        <p>Select a queued job to inspect metadata and path hierarchy.</p>
      </div>
    )
  }

  const rows = [
    { label: 'Source', value: transfer.source_path || transfer.source || '—' },
    { label: 'Destination', value: transfer.destination_path || transfer.destination || '—' },
    { label: 'Status', value: transfer.status || 'Unknown' },
    { label: 'ETA', value: transfer.eta || transfer.eta_text || 'TBD' },
    { label: 'Files', value: transfer.file_count ? `${transfer.file_count} files` : 'Single file' },
    { label: 'Settle Time', value: transfer.settle_time_seconds ? `${transfer.settle_time_seconds}s` : 'Auto' },
    {
      label: 'Updated',
      value: formatTimestamp(transfer.updated_at || transfer.completed_at || transfer.created_at),
    },
    {
      label: 'Notes',
      value: transfer.detail || transfer.status_description || 'Operational transfer',
    },
  ]

  return (
    <div className="transfer-details-panel">
      <header className="transfer-details-header">
        <span className="transfer-details-eyebrow">Transfer Details</span>
        <h3>{transfer.file_name || transfer.title || 'Queued transfer'}</h3>
        <span className="transfer-details-status-chip">{transfer.status || 'unknown'}</span>
      </header>
      <div className="transfer-details-grid">
        {rows.map((row) => (
          <article key={row.label} className="transfer-details-row">
            <span className="transfer-details-label">{row.label}</span>
            <span className="transfer-details-value">{row.value}</span>
          </article>
        ))}
      </div>
    </div>
  )
}

TransferDetailsPanel.propTypes = {
  transfer: PropTypes.shape({
    file_name: PropTypes.string,
    title: PropTypes.string,
    status: PropTypes.string,
    detail: PropTypes.string,
    status_description: PropTypes.string,
    source_path: PropTypes.string,
    destination_path: PropTypes.string,
    eta: PropTypes.string,
    eta_text: PropTypes.string,
    source: PropTypes.string,
    destination: PropTypes.string,
    file_count: PropTypes.number,
    settle_time_seconds: PropTypes.number,
    updated_at: PropTypes.string,
    completed_at: PropTypes.string,
    created_at: PropTypes.string,
  }),
}

TransferDetailsPanel.defaultProps = {
  transfer: null,
}

export default TransferDetailsPanel
