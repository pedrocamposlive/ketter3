import React from 'react'
import StatusIndicator from '../components/StatusIndicator'
import AlertsPanel from '../components/AlertsPanel'
import KpiCard from '../components/KpiCard'
import ThroughputChart from '../components/ThroughputChart'
import MoveCopyDonut from '../components/MoveCopyDonut'

const toneFromStatus = (value) => {
  if (!value) return 'warn'
  const normalized = value.toLowerCase()
  if (normalized.includes('operational') || normalized.includes('connected') || normalized.includes('healthy')) {
    return 'ok'
  }
  if (normalized.includes('warn') || normalized.includes('degrad') || normalized.includes('pending')) {
    return 'warn'
  }
  if (normalized.includes('error') || normalized.includes('fail')) {
    return 'critical'
  }
  return 'warn'
}

const formatTimestamp = (value) => {
  if (!value) return 'Awaiting sync'
  try {
    return new Date(value).toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return value
  }
}

function DashboardPage({ systemStatus, systemHealth }) {
  const workerMatch = systemStatus?.worker?.match(/\\d+/)
  const workerCount = Number(workerMatch?.[0]) || 4
  const jobTrend = workerCount >= 5 ? '+3 jobs vs last hour' : '+1 job vs last hour'
  const kpiCards = [
    {
      title: 'Transferências ativas',
      value: `${workerCount} jobs`,
      note: 'Automation Node queue depth',
      status: 'info',
      trend: jobTrend,
      miniGraphData: [38, 41, 44, 47, 45, workerCount * 10],
    },
    {
      title: 'Throughput 24h',
      value: systemHealth?.redis ? '124 MB/s' : 'waiting',
      note: 'Average size/pipeline node',
      status: 'success',
      trend: '+4 MB/s vs 1h',
      miniGraphData: [76, 82, 84, 90, 88, 91],
    },
    {
      title: 'ZIP Smart jobs',
      value: '3 ativos',
      note: 'Watch mode folders',
      status: 'warning',
      trend: '+1 vs yesterday',
      miniGraphData: [2, 2.5, 3, 3.2, 3.1, 3],
    },
    {
      title: 'Falhas 24h',
      value: '0 falhas',
      note: 'Rollback ready',
      status: 'danger',
      trend: 'Monitoramento contínuo',
      miniGraphData: [1, 0.5, 0, 0, 0, 0],
    },
  ]

  const statusCards = [
    {
      title: 'API Gateway',
      value: systemStatus?.api || 'Unknown',
      note: systemStatus?.version ? `v${systemStatus.version}` : 'Awaiting version',
      tone: toneFromStatus(systemStatus?.api),
    },
    {
      title: 'Database',
      value: systemStatus?.database || 'Unknown',
      note: 'PostgreSQL connectivity',
      tone: toneFromStatus(systemStatus?.database),
    },
    {
      title: 'Redis Queue',
      value: systemStatus?.redis || 'Unknown',
      note: 'RQ Worker handshake',
      tone: toneFromStatus(systemStatus?.redis),
    },
    {
      title: 'System Health',
      value: systemHealth?.status || 'Unknown',
      note: systemHealth?.environment ? systemHealth.environment : 'Awaiting node',
      tone: toneFromStatus(systemHealth?.status),
    },
  ]

  const summaryList = [
    {
      label: 'Service',
      value: systemHealth?.service || 'ketter-api',
      detail: systemHealth?.version ? `Version ${systemHealth.version}` : 'Version unknown',
    },
    {
      label: 'Environment',
      value: systemHealth?.environment || 'development',
      detail: systemHealth?.timestamp ? formatTimestamp(systemHealth.timestamp) : 'Timestamp pending',
    },
    {
      label: 'Database',
      value: systemHealth?.database ? 'Connected' : 'Offline',
      detail: 'PostgreSQL',
    },
    {
      label: 'Redis',
      value: systemHealth?.redis ? 'Connected' : 'Offline',
      detail: 'Queue backend',
    },
  ]

  const indicatorData = [
    {
      label: 'Automation Node API',
      status: systemStatus?.api,
      detail: systemStatus?.version ? `v${systemStatus.version}` : 'Awaiting handshake',
    },
    {
      label: 'Database',
      status: systemStatus?.database,
      detail: 'PostgreSQL health',
    },
    {
      label: 'Redis',
      status: systemStatus?.redis,
      detail: 'RQ queue',
    },
    {
      label: 'Workers',
      status: systemStatus?.worker,
      detail: 'RQ workers reporting',
    },
  ]

  return (
    <div id="dashboard" className="dashboard-page">
      <section className="dashboard-section dashboard-section-title">
        <span className="dashboard-section-label">Manus Task Dashboard</span>
        <h2 className="dashboard-section-heading">Operational Mission Control</h2>
        <p className="dashboard-section-lede">
          KPIs, throughputs and alerts aligned with Manus spacing to keep the Automation Node crew informed
          without noise.
        </p>
      </section>

      <section className="dashboard-section dashboard-section-block card-panel">
        <div className="dashboard-top">
          <div className="dashboard-kpi-grid">
            {kpiCards.map((card) => (
              <KpiCard
                key={card.title}
                title={card.title}
                value={card.value}
                note={card.note}
                status={card.status}
                trend={card.trend}
                miniGraphData={card.miniGraphData}
              />
            ))}
          </div>
          <div className="dashboard-status-grid">
            {statusCards.map((card) => (
              <article key={card.title} className={`dashboard-card dashboard-card-${card.tone}`}>
                <span className="dashboard-card-subtitle">{card.title}</span>
                <strong className="dashboard-card-value">{card.value}</strong>
                <p className="dashboard-card-note">{card.note}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="dashboard-section dashboard-section-charts card-panel">
        <div className="dashboard-charts-row">
          <ThroughputChart />
          <MoveCopyDonut />
        </div>
      </section>

      <section className="dashboard-section dashboard-section-status card-panel">
        <div className="dashboard-status-row">
          {indicatorData.map((indicator) => (
            <StatusIndicator
              key={indicator.label}
              label={indicator.label}
              status={indicator.status}
              detail={indicator.detail}
            />
          ))}
        </div>
      </section>

      <section className="dashboard-section dashboard-section-alerts card-panel">
        <AlertsPanel />
      </section>

      <section className="dashboard-section dashboard-section-logs card-panel">
        <h2>System Health Feed</h2>
        <div className="health-summary-grid">
          {summaryList.map((item) => (
            <article key={item.label} className="health-summary-card">
              <span className="health-summary-label">{item.label}</span>
              <strong className="health-summary-value">{item.value}</strong>
              <p className="health-summary-detail">{item.detail}</p>
            </article>
          ))}
        </div>
        <p className="transfers-note">
          Signals sync: {formatTimestamp(systemHealth?.timestamp || systemStatus?.timestamp)}
        </p>
      </section>
    </div>
  )
}

export default DashboardPage
