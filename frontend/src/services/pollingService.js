const DEFAULT_INTERVAL = 5000
const FALLBACK_INTERVAL = 15000

export function startPolling({ label, fetcher, onSuccess, onError, interval = DEFAULT_INTERVAL, fallbackInterval = FALLBACK_INTERVAL }) {
  let timeoutId
  let active = true

  const scheduleNext = (delay) => {
    if (!active) return
    timeoutId = setTimeout(run, delay)
  }

  const run = async () => {
    if (!active) return

    try {
      const response = await fetcher()
      onSuccess?.(response)
      scheduleNext(interval)
    } catch (error) {
      console.warn(`[polling:${label}] failure`, error)
      onError?.(error)
      scheduleNext(fallbackInterval)
    }
  }

  run()

  return () => {
    active = false
    clearTimeout(timeoutId)
  }
}
