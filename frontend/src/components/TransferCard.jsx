import React from 'react'
import PropTypes from 'prop-types'

const STATUS_TONES = {
  pending: 'warning',
  queuing: 'warning',
  validating: 'warning',
  copying: 'info',
  running: 'info',
  verifying: 'info',
  completed: 'success',
  failed: 'danger',
  canceled: 'danger',
}

function TransferCard({ transfer, onSelect, isSelected }) {
  const tone = STATUS_TONES[transfer.status?.toLowerCase()] || 'info'
  const handleClick = () => onSelect?.(transfer)

  const badgeLabel = transfer.status ? transfer.status.toUpperCase() : 'UNKNOWN'

  return (
    <button
      type="button"
      className={`transfer-card-row transfer-card-${tone} ${isSelected ? 'transfer-card-selected' : ''}`}
      onClick={handleClick}
      onKeyDown={(event) => event.key === 'Enter' && handleClick()}
      aria-pressed={isSelected}
    >
      <div className="transfer-card-heading">
        <strong>{transfer.file_name || transfer.title || 'Unnamed transfer'}</strong>
        <span className="transfer-card-status-badge">{badgeLabel}</span>
      </div>
      <p className="transfer-card-description">
        {transfer.detail || transfer.status_description || 'Awaiting dispatch'}
      </p>
      <div className="transfer-card-meta">
        <div>
          <span className="transfer-card-meta-label">Source</span>
          <span className="transfer-card-meta-value">{transfer.source_path || transfer.source || '—'}</span>
        </div>
        <div>
          <span className="transfer-card-meta-label">Destination</span>
          <span className="transfer-card-meta-value">
            {transfer.destination_path || transfer.destination || '—'}
          </span>
        </div>
        <div>
          <span className="transfer-card-meta-label">ETA</span>
          <span className="transfer-card-meta-value">{transfer.eta || transfer.eta_text || 'TBD'}</span>
        </div>
      </div>
    </button>
  )
}

TransferCard.propTypes = {
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
  }).isRequired,
  onSelect: PropTypes.func,
  isSelected: PropTypes.bool,
}

TransferCard.defaultProps = {
  onSelect: undefined,
  isSelected: false,
}

export default TransferCard
