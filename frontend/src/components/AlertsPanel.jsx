import React, { useState, useEffect } from 'react'
import { getAlerts } from '../services/api'
import { startPolling } from '../services/pollingService'

const severityMap = {
  critical: 'badge-danger',
  warning: 'badge-warning',
  info: 'badge-info',
  success: 'badge-success',
  rollback: 'badge-warning',
  failure: 'badge-danger',
  hash: 'badge-info',
}

const FALLBACK_ALERTS = [
  { id: 'alert-1', tone: 'critical', title: 'Volume /mnt/backup low on space', detail: '80% used, watch mode paused' },
  { id: 'alert-2', tone: 'warning', title: 'Job 304 waiting', detail: 'Checksum pending across 22 files' },
  { id: 'alert-3', tone: 'info', title: 'Audit logs rotated', detail: '24h retention active' },
]

function AlertsPanel() {
  const [alerts, setAlerts] = useState(FALLBACK_ALERTS)
  const [status, setStatus] = useState('Sincronizando...')

  useEffect(() => {
    let active = true
    const stop = startPolling({
      label: 'alerts-panel',
      fetcher: () => getAlerts(),
      interval: 6000,
      fallbackInterval: 16000,
      onSuccess: (payload) => {
        if (!active) return
        if (Array.isArray(payload) && payload.length) {
          setAlerts(payload.slice(0, 6))
          setStatus('Atualizado')
        } else {
          setStatus('Sem novos alerts')
        }
      },
      onError: () => {
        if (!active) return
        setStatus('Offline')
      },
    })

    return () => {
      active = false
      stop()
    }
  }, [])

  return (
    <div className="alerts-panel alerts-siem">
      <header className="alerts-panel-header">
        <div>
          <h3>Operational Alerts</h3>
          <p className="alerts-status">{status}</p>
        </div>
        <span className="alerts-count">{alerts.length} eventos</span>
      </header>
      <ul className="alerts-siem-list">
        {alerts.map((alert) => (
          <li key={alert.id} className="alerts-siem-row">
            <div className="alerts-siem-row-left">
              <span className={`alerts-siem-badge ${severityMap[alert.tone] || 'badge-info'}`}>
                {alert.tone}
              </span>
              <div>
                <strong>{alert.title}</strong>
                <p>{alert.detail}</p>
              </div>
            </div>
            <time>{alert.timestamp || 'agora'}</time>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default AlertsPanel
