import Layout from './layout/Layout'
import DashboardPage from './pages/DashboardPage'
import TransfersPage from './pages/TransfersPage'
import AuditPage from './pages/AuditPage'
import SystemHealthPage from './pages/SystemHealthPage'
import SettingsPage from './pages/SettingsPage'
import { useSystemStatus, useSystemHealth, useTransferRefresh } from './hooks'
import './App.css'

/**
 * Ketter 3.0 - Main Application
 * Single operational view for file transfers
 *
 * MRC: Simple, clear UI for operators
 */
function App() {
  const systemStatus = useSystemStatus()
  const systemHealth = useSystemHealth()
  const [refreshKey, handleTransferCreated] = useTransferRefresh()

  return (
    <Layout>
      <DashboardPage systemStatus={systemStatus} systemHealth={systemHealth} />
      <TransfersPage refreshKey={refreshKey} onTransferCreated={handleTransferCreated} />
      <AuditPage />
      <SystemHealthPage systemHealth={systemHealth} systemStatus={systemStatus} />
      <SettingsPage />
    </Layout>
  )
}

export default App
