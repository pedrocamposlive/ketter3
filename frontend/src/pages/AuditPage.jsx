import React, { useState, useEffect } from 'react'
import LogsViewer from '../components/LogsViewer'
import { getAuditLogs } from '../services/api'
import { startPolling } from '../services/pollingService'

const AUDIT_LOGS = [
  { timestamp: '13:32:15', status: 'INFO', detail: 'Transfer job 292 verified checksum successfully' },
  { timestamp: '12:47:08', status: 'WARN', detail: 'Volume /Volumes/Nexis approaching 80% usage' },
  { timestamp: '12:01:52', status: 'INFO', detail: 'Automation node started scheduled validation batch' },
  { timestamp: '11:55:34', status: 'ERROR', detail: 'Job 288 failed: mismatch 1.2% SHA-256' },
  { timestamp: '11:20:40', status: 'INFO', detail: 'Audit log rotation completed (24h window)' },
]

/**
 * Audit page listing recent events and alerts.
 */
function AuditPage() {
  const [logs, setLogs] = useState(AUDIT_LOGS)
  const [syncStatus, setSyncStatus] = useState('Syncing audit logs...')

  useEffect(() => {
    let active = true
    const stop = startPolling({
      label: 'audit-logs',
      fetcher: () => getAuditLogs(),
      interval: 6000,
      fallbackInterval: 18000,
      onSuccess: (payload) => {
        if (!active) return
        if (Array.isArray(payload) && payload.length) {
          setLogs(payload)
          setSyncStatus('Synced')
        }
      },
      onError: () => {
        if (!active) return
        setSyncStatus('Audit offline')
      },
    })

    return () => {
      active = false
      stop()
    }
  }, [])

  return (
    <div id="audit" className="audit-page">
      <section className="section card-panel audit-hero">
        <div>
          <h2>Audit & Compliance</h2>
          <p className="audit-hero-note">
            Immutable log stream synchronized with Automation Node. All events keep SHA-256 digests and
            severity tags.
          </p>
        </div>
        <div className="audit-hero-status">
          <span>Logs synced</span>
          <strong>{syncStatus}</strong>
        </div>
      </section>

      <section className="section card-panel audit-filters">
        <div className="filter-pill">
          <span>Severity:&nbsp;</span>
          <strong>All</strong>
        </div>
        <div className="filter-pill">
          <span>Target:&nbsp;</span>
          <strong>Transfers</strong>
        </div>
        <div className="filter-pill">
          <span>Time window:&nbsp;</span>
          <strong>Last 24h</strong>
        </div>
      </section>

      <section className="section card-panel audit-logs-section">
        <div className="audit-log-list">
          {logs.map((log) => (
            <article
              key={`${log.timestamp}-${log.status}`}
              className={`audit-log-entry audit-log-entry-${log.status.toLowerCase()}`}
            >
              <div className="audit-log-marker">
                <span className="audit-log-dot" aria-hidden="true"></span>
              </div>
              <div className="audit-log-content">
                <time className="audit-log-time">{log.timestamp}</time>
                <span className="audit-log-status">{log.status}</span>
                <p className="audit-log-detail">{log.detail}</p>
              </div>
            </article>
          ))}
        </div>
        <div className="audit-log-viewer-card">
          <LogsViewer />
        </div>
      </section>
    </div>
  )
}

export default AuditPage
