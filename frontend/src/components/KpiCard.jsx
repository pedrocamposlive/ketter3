import React from 'react'
import PropTypes from 'prop-types'

/**
 * KPI Card component used throughout the dashboard.
 * Presents a title, value, note, optional trend and a tiny graph.
 */
function KpiCard({ title, value, note, status = 'info', trend, miniGraphData = [] }) {
  const normalizedStatus = `kpi-card-${status}`
  const graphValues = miniGraphData.length ? miniGraphData : [40, 45, 42, 48, 46, 50]

  return (
    <article className={`kpi-card ${normalizedStatus}`}>
      <div className="kpi-card-header">
        <span className="kpi-card-title">{title}</span>
        {trend && <span className="kpi-card-trend">{trend}</span>}
      </div>
      <strong className="kpi-card-value">{value}</strong>
      {note && <p className="kpi-card-note">{note}</p>}
      <div className="kpi-card-mini-graph" aria-label={`${title} mini chart`}>
        {graphValues.map((point, index) => {
          const height = Math.min(100, Math.max(12, point))
          return (
            <span
              key={`${title}-${index}`}
              style={{ height: `${height}%` }}
              aria-hidden="true"
            ></span>
          )
        })}
      </div>
    </article>
  )
}

KpiCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  note: PropTypes.string,
  status: PropTypes.oneOf(['info', 'success', 'warning', 'danger']),
  trend: PropTypes.string,
  miniGraphData: PropTypes.arrayOf(PropTypes.number),
}

export default KpiCard
