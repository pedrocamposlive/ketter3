import React from 'react'

const HEALTH_MAP = {
  operational: 'healthy',
  healthy: 'healthy',
  ok: 'healthy',
  warning: 'warning',
  warn: 'warning',
  degraded: 'warning',
  error: 'error',
  failed: 'error',
}

function StatusIndicator({ label, status, detail }) {
  const normalized = status ? status.toLowerCase() : 'unknown'
  const tone = HEALTH_MAP[normalized] || (normalized.includes('warn') ? 'warning' : normalized.includes('error') ? 'error' : 'healthy')

  return (
    <div className={`status-indicator status-indicator-${tone}`}>
      <span className={`status-dot status-dot-${tone}`}></span>
      <div className="status-copy">
        <span className="status-label">{label}</span>
        <span className="status-detail">{detail || status || 'Unknown'}</span>
      </div>
    </div>
  )
}

export default StatusIndicator
