import { useState, useEffect } from 'react'
import FilePicker from './components/FilePicker'
import TransferHistory from './components/TransferHistory'
import { getStatus } from './services/api'
import './App.css'

/**
 * Ketter 3.0 - Main Application
 * Single operational view for file transfers
 *
 * MRC: Simple, clear UI for operators
 */
function App() {
  const [systemStatus, setSystemStatus] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Load system status on mount
  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [])

  async function loadStatus() {
    try {
      const status = await getStatus()
      setSystemStatus(status)
    } catch (error) {
      console.error('Failed to load status:', error)
    }
  }

  function handleTransferCreated() {
    // Refresh history and progress views
    setRefreshKey(prev => prev + 1)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>Ketter 3.0</h1>
          <p>File Transfer System with Triple SHA-256 Verification</p>
          {systemStatus && (
            <div className="status-indicators">
              <StatusIndicator
                label="Database"
                status={systemStatus.database}
              />
              <StatusIndicator
                label="Redis"
                status={systemStatus.redis}
              />
              <StatusIndicator
                label="Worker"
                status={systemStatus.worker}
              />
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* File Picker - Create new transfers */}
        <section className="section">
          <h2>New Transfer</h2>
          <FilePicker onTransferCreated={handleTransferCreated} />
        </section>

        {/* Transfer History - Last 30 days (with active transfers and delete) */}
        <section className="section">
          <h2>Transfer History & Active Transfers (30 days)</h2>
          <TransferHistory key={`history-${refreshKey}`} />
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Ketter 3.0 - Minimal Reliable Core | Version 3.0.0</p>
      </footer>
    </div>
  )
}

/**
 * Status Indicator Component
 */
function StatusIndicator({ label, status }) {
  const getStatusClass = () => {
    if (status === 'connected' || status === 'operational') return 'status-ok'
    if (status.includes('worker')) return 'status-ok'
    return 'status-error'
  }

  return (
    <div className={`status-indicator ${getStatusClass()}`}>
      <span className="status-dot"></span>
      <span className="status-label">{label}</span>
    </div>
  )
}

export default App
