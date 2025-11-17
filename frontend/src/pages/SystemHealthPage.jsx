import React from 'react'

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

function SystemHealthPage({ systemHealth, systemStatus }) {
  const healthMetrics = [
    { label: 'Service', value: systemHealth?.service || 'ketter-api', detail: systemHealth?.version ? `Version ${systemHealth.version}` : 'Version unknown' },
    { label: 'Health Status', value: systemHealth?.status || 'Unknown', detail: 'Reports from /health' },
    { label: 'Environment', value: systemHealth?.environment || 'development', detail: 'Configured environment' },
    { label: 'Last Sync', value: formatTimestamp(systemHealth?.timestamp), detail: 'Automation node heartbeat' },
  ]

  const statusList = [
    { label: 'API', status: systemStatus?.api || 'Unknown' },
    { label: 'Database', status: systemStatus?.database || 'Unknown' },
    { label: 'Redis', status: systemStatus?.redis || 'Unknown' },
    { label: 'Workers', status: systemStatus?.worker || 'Unknown' },
  ]

  const statusTone = (value) => {
    if (!value) return 'unknown'
    const normalized = value.toLowerCase()
    if (normalized.includes('healthy') || normalized.includes('ok') || normalized.includes('connected')) {
      return 'success'
    }
    if (normalized.includes('warn') || normalized.includes('pending') || normalized.includes('degraded')) {
      return 'warning'
    }
    if (normalized.includes('error') || normalized.includes('fail') || normalized.includes('unreachable')) {
      return 'danger'
    }
    return 'default'
  }

  return (
    <div id="system-health" className="system-health-page">
      <section className="section card-panel system-health-grid system-health-panel">
        <div className="system-health-metrics">
          <header>
            <p className="system-health-subtitle">Automation Node</p>
            <h2>Infrastructure Health</h2>
          </header>
          <div className="health-summary-grid">
            {healthMetrics.map((metric) => (
              <article key={metric.label} className="health-summary-card">
                <span className="health-summary-label">{metric.label}</span>
                <strong className="health-summary-value">{metric.value}</strong>
                <p className="health-summary-detail">{metric.detail}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="system-health-status">
          <header>
            <p className="system-health-subtitle">Status Watch</p>
            <h3>Service Status</h3>
          </header>
          <div className="status-matrix">
            {statusList.map((item) => {
              const tone = statusTone(item.status)
              return (
                <article key={item.label} className={`latency-item latency-${tone}`}>
                  <span className="latency-label">{item.label}</span>
                  <strong className="latency-value">{item.status}</strong>
                  <span className="latency-detail">Realtime heartbeat</span>
                </article>
              )
            })}
          </div>
        </div>
      </section>
    </div>
  )
}

export default SystemHealthPage
