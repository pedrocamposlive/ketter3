import { useState, useEffect, useRef } from 'react'
import { getSystemHealth } from '../services/api'
import { startPolling } from '../services/pollingService.js'

/**
 * useSystemHealth
 * Polls the backend health endpoint and exposes the latest summary payload.
 */
export default function useSystemHealth(pollInterval = 15000) {
  const [health, setHealth] = useState(null)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    const stop = startPolling({
      label: 'system-health',
      fetcher: () => getSystemHealth(),
      interval: pollInterval,
      fallbackInterval: pollInterval * 2,
      onSuccess: (payload) => {
        if (isMounted.current) {
          setHealth(payload)
        }
      },
      onError: (error) => {
        console.error('useSystemHealth:', error)
      },
    })

    return () => {
      isMounted.current = false
      stop()
    }
  }, [pollInterval])

  return health
}
