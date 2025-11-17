import React from 'react'

/**
 * Simple ThroughputChart emulating a smooth line graph.
 * Not depending on external libs to keep repository lean.
 */
function ThroughputChart({ title = 'Throughput 24h', unit = 'MB/s', data = [] }) {
  const baseData = data.length ? data : [60, 70, 84, 90, 88, 91, 95, 88, 82, 76, 80, 85]
  const max = Math.max(...baseData)
  const points = baseData
    .map((value, index) => {
      const x = (index / (baseData.length - 1)) * 100
      const y = 100 - (value / max) * 100
      return `${x},${y}`
    })
    .join(' ')

  return (
    <article className="throughput-card">
      <div className="throughput-card-header">
        <div>
          <span className="throughput-title">{title}</span>
          <p className="throughput-subtext">Últimas 24 horas · Valor médio {Math.round(baseData.reduce((a, b) => a + b, 0) / baseData.length)} {unit}</p>
        </div>
        <span className="throughput-unit">{unit}</span>
      </div>
      <svg className="throughput-chart" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline points={points} />
      </svg>
      <div className="throughput-legend">
        {['00h', '06h', '12h', '18h', '24h'].map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
    </article>
  )
}

export default ThroughputChart
