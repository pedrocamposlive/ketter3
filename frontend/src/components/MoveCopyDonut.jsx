import React from 'react'

/**
 * Simple donut chart showing MOVE vs COPY distribution.
 */
function MoveCopyDonut({ move = 35, copy = 65 }) {
  const total = move + copy || 100
  const moveValue = (move / total) * 100
  const copyValue = 100 - moveValue
  const circumference = 2 * Math.PI * 30
  const moveOffset = circumference - (moveValue / 100) * circumference

  return (
    <article className="donut-card">
      <div className="donut-card-header">
        <span>Operation Mode Split</span>
        <strong>{Math.round(moveValue)}% MOVE</strong>
      </div>
      <svg className="donut-chart" viewBox="0 0 120 120" role="img" aria-label="MOVE vs COPY distribution">
        <circle className="donut-track" cx="60" cy="60" r="30" />
        <circle
          className="donut-move"
          cx="60"
          cy="60"
          r="30"
          strokeDasharray={circumference}
          strokeDashoffset={moveOffset}
        />
        <text x="60" y="60" textAnchor="middle" className="donut-center-text">
          {Math.round(moveValue)}%
        </text>
      </svg>
      <div className="donut-legend">
        <span className="legend-item">
          <span className="legend-color legend-move"></span>
          MOVE · {move} jobs
        </span>
        <span className="legend-item">
          <span className="legend-color legend-copy"></span>
          COPY · {copy} jobs
        </span>
      </div>
    </article>
  )
}

export default MoveCopyDonut
