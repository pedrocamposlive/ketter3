import React from 'react'

const DEFAULT_LOGS = [
  { id: 'log-101', time: '13:45', event: 'Watch folder stabilized, zip ready' },
  { id: 'log-102', time: '13:40', event: 'Transfer job 290 started' },
  { id: 'log-103', time: '13:36', event: 'Volume /Storage/Ready mounted' },
]

/**
 * LogsViewer shows a stream of recent events.
 */
function LogsViewer({ logs = DEFAULT_LOGS }) {
  return (
    <div className="logs-viewer">
      <header className="logs-viewer-header">
        <h3>Recent Logs</h3>
        <span>Streaming</span>
      </header>
      <ul>
        {logs.map((log) => (
          <li key={log.id}>
            <span className="logs-viewer-time">{log.time}</span>
            <p className="logs-viewer-event">{log.event}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default LogsViewer
