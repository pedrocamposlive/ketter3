import { useState, useEffect } from 'react'
import { getAlerts } from '../services/api'
import { startPolling } from '../services/pollingService'

const FALLBACK_ALERTS = [
  { id: 'alert-1', tone: 'critical', title: 'Volume /mnt/backup low on space', detail: '80% used, watch mode writes paused' },
  { id: 'alert-2', tone: 'warning', title: 'Job 304 pending checksum', detail: 'Awaiting validation for 22 files' },
  { id: 'alert-3', tone: 'info', title: 'Audit logs rotated', detail: '24h retention active' },
]

function Alerts({ alerts = FALLBACK_ALERTS }) {
  const [remoteAlerts, setRemoteAlerts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const stop = startPolling({
      label: 'alerts',
      fetcher: () => getAlerts(),
      interval: 5000,
      fallbackInterval: 12000,
      onSuccess: (payload) => {
        if (Array.isArray(payload)) {
          setRemoteAlerts(payload)
          setError(null)
        }
        setLoading(false)
      },
      onError: (err) => {
        console.error('Alerts fetch failed', err)
        setError(err.message)
        setLoading(false)
      },
    })
    return () => stop()
  }, [])

  const list = remoteAlerts || alerts

  return (
    <div className="alerts-panel">
      <header>
        <h3>Operational Alerts</h3>
        <span>{loading ? 'Syncing...' : error ? 'Offline' : 'Updated now'}</span>
      </header>
      <ul>
        {list.map((alert) => (
          <li key={alert.id} className={`alerts-item alerts-item-${alert.tone}`}>
            <span className="alerts-badge">{alert.tone}</span>
            <div>
              <strong>{alert.title}</strong>
              <p>{alert.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default Alerts
