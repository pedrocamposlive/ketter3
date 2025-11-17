import { useState, useCallback } from 'react'

/**
 * useTransferRefresh
 * Provides a refresh key counter and a handler so child components can react to transfer updates.
 */
export function useTransferRefresh() {
  const [refreshKey, setRefreshKey] = useState(0)
  const triggerRefresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1)
  }, [])

  return [refreshKey, triggerRefresh]
}
