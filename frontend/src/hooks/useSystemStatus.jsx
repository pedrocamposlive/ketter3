import { useState, useEffect, useRef, useCallback } from 'react'
import { getStatus } from '../services/api'
import { startPolling } from '../services/pollingService.js'

/**
 * useSystemStatus
 * Polls the backend for status updates and exposes the latest payload.
 */
export default function useSystemStatus(pollInterval = 10000) {
  const [status, setStatus] = useState(null)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    const stop = startPolling({
      label: 'system-status',
      fetcher: () => getStatus(),
      onSuccess: (payload) => {
        if (isMounted.current) {
          setStatus(payload)
        }
      },
      onError: (error) => {
        console.error('useSystemStatus:', error)
      },
      interval: pollInterval,
      fallbackInterval: pollInterval * 2,
    })

    return () => {
      isMounted.current = false
      stop()
    }
  }, [pollInterval])

  return status
}
