import React, { useState, useEffect } from 'react'
import FilePicker from '../components/FilePicker'
import TransferProgress from '../components/TransferProgress'
import TransferHistory from '../components/TransferHistory'
import TransferCard from '../components/TransferCard'
import TransferDetailsPanel from '../components/TransferDetailsPanel'
import { ApiError, getTransfers, cancelTransfer } from '../services/api'
import { startPolling } from '../services/pollingService'

/**
 * Transfers page showing job creation, queue snapshot, and activity logs.
 */
function TransfersPage({ onTransferCreated }) {
  const [transfers, setTransfers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTransfer, setSelectedTransfer] = useState(null)

  const normalizeTransfers = (payload) => {
    if (Array.isArray(payload?.items)) return payload.items
    if (Array.isArray(payload?.jobs)) return payload.jobs
    return []
  }

  const heroMetrics = [
    {
      id: 'hero-1',
      value: '3 watch jobs',
      note: 'Watchers conectados · 2 com zones seguras',
    },
    {
      id: 'hero-2',
      value: '124 MB/s',
      note: 'Throughput médio nas últimas 6h',
    },
    {
      id: 'hero-3',
      value: 'ZIP Smart',
      note: '2 pastas em monitoramento contínuo',
    },
    {
      id: 'hero-4',
      value: '0 falhas',
      note: 'Rollback pronto · SHA verified',
    },
  ]

  useEffect(() => {
    let active = true
    const stop = startPolling({
      label: 'transfers-page',
      fetcher: () => getTransfers(),
      interval: 5000,
      fallbackInterval: 15000,
      onSuccess: (payload) => {
        if (!active) return
        const list = normalizeTransfers(payload)
        setTransfers(list)
        setError(null)
        setIsLoading(false)
      },
      onError: (err) => {
        if (!active) return
        const message = err instanceof ApiError ? `${err.statusCode || 'Error'} – ${err.message}` : err.message
        setError(message)
        setIsLoading(false)
      },
    })

    return () => {
      active = false
      stop()
    }
  }, [])

  const handleTransferSelect = (transfer) => {
    setSelectedTransfer(transfer)
  }

  const handleStopTransfer = async (transferId) => {
    try {
      await cancelTransfer(transferId)
    } catch (err) {
      console.error('Failed to stop transfer', err)
      const message = err instanceof ApiError ? `${err.statusCode || 'Error'} – ${err.message}` : err.message
      setError(message)
    }
  }

  const previewTransfers = transfers.slice(0, 3)

  const detail = selectedTransfer || transfers[0]

  return (
    <div id="transfers" className="transfers-page">
      <div className="ui-container transfers-page-shell">
        <section className="transfers-section transfers-section-create card-panel">
          <div className="transfers-section-header">
            <span className="transfers-section-label">Automação</span>
            <h2 className="transfers-section-heading">Create Transfer Job</h2>
          </div>
          <p className="transfers-section-lede">
            Todos os jobs passam pelo Automation Node, com validação tripla e auditoria ativa.
          </p>
          <FilePicker onTransferCreated={onTransferCreated} />
        </section>

        <section className="transfers-section transfers-section-hero card-panel">
          <div className="transfers-hero-grid">
            {heroMetrics.map((metric) => (
              <article key={metric.id} className="transfers-hero-card">
                <strong>{metric.value}</strong>
                <p>{metric.note}</p>
              </article>
            ))}
          </div>
          <div className="transfers-events-panel">
            <h3>Recent Events</h3>
            <ul className="events-list">
              <li>Transfer job 298 completed · SHA-256 validated</li>
              <li>Alert: Volume /mnt/backup low on space</li>
              <li>Auto-rollback triggered for job 304 (checksum mismatch)</li>
            </ul>
          </div>
        </section>

        <section className="transfers-section transfers-section-queue card-panel">
          <div className="transfers-section-header">
            <span className="transfers-section-label">Queue</span>
            <h2 className="transfers-section-heading">Live Queue Snapshot</h2>
            <p className="transfers-section-lede">
              Lista em tempo real com estados tokenizados e seleção rápida para detalhes.
            </p>
          </div>
          <div className="transfers-queue-layout">
            <div className="transfers-queue-column">
              <div className="transfers-queue-table">
                <div className="transfers-queue-row transfers-queue-header">
                  <span>Job</span>
                  <span>Status</span>
                  <span>Source → Destination</span>
                  <span>ETA</span>
                </div>
                <div className="transfers-queue-body">
                  {previewTransfers.length
                    ? previewTransfers.map((job) => (
                        <TransferCard
                          key={job.id}
                          transfer={job}
                          onSelect={handleTransferSelect}
                          isSelected={detail?.id === job.id}
                        />
                      ))
                    : (
                        <div className="transfers-empty-state">
                          <p>No queued jobs yet.</p>
                        </div>
                      )}
                </div>
              </div>
            </div>
            <div className="transfers-details-column">
              <TransferDetailsPanel transfer={detail} />
            </div>
          </div>
        </section>

        <section className="transfers-section transfers-section-progress card-panel">
          <div className="transfers-section-header">
            <span className="transfers-section-label">Pipeline</span>
            <h2 className="transfers-section-heading">Active Transfers</h2>
          </div>
          <TransferProgress transfers={transfers} isLoading={isLoading} error={error} onCancel={handleStopTransfer} />
        </section>

        <section className="transfers-section transfers-section-history card-panel">
          <div className="transfers-section-header">
            <span className="transfers-section-label">Auditoria</span>
            <h2 className="transfers-section-heading">Transfer History (30 days)</h2>
          </div>
          <TransferHistory />
        </section>
      </div>
    </div>
  )
}

export default TransfersPage
