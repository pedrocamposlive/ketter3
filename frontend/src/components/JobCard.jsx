import React from 'react'

const STATUS_TONES = {
  queued: 'warning',
  validating: 'warning',
  copying: 'healthy',
  completed: 'healthy',
  failed: 'error',
}

function JobCard({ title, status, eta, detail }) {
  const tone = STATUS_TONES[status.toLowerCase()] || 'warning'
  return (
    <article className={`job-card job-card-${tone}`}>
      <div className="job-card-main">
        <strong>{title}</strong>
        <p>{detail}</p>
      </div>
      <div className="job-card-meta">
        <span className="job-card-status">{status}</span>
        <span className="job-card-eta">{eta}</span>
      </div>
    </article>
  )
}

export default JobCard
