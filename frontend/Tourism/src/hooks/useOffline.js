import { useState, useEffect, useCallback, useRef } from "react"

/**
 * useOffline - Hook for offline detection and background sync
 *
 * Features:
 * - Real-time online/offline status detection
 * - Background sync queue for forms submitted while offline
 * - Automatic retry when connection is restored
 * - Offline data persistence in localStorage
 */

const SYNC_QUEUE_KEY = "offline_sync_queue"
const OFFLINE_DATA_KEY = "offline_data_cache"

export const useOffline = () => {
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator !== "undefined" ? navigator.onLine : true
  )
  const [isSyncing, setIsSyncing] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)
  const [lastSynced, setLastSynced] = useState(null)
  const syncQueueRef = useRef([])

  // ─── Online/Offline Detection ─────────────────────────────────────────────
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      // Trigger sync when back online
      processSyncQueue()
    }
    const handleOffline = () => {
      setIsOnline(false)
    }

    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)

    // Initialize pending count from storage
    const queue = getSyncQueue()
    syncQueueRef.current = queue
    setPendingCount(queue.length)

    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
    }
  }, [])

  // ─── Sync Queue Management ────────────────────────────────────────────────
  const getSyncQueue = useCallback(() => {
    try {
      const stored = localStorage.getItem(SYNC_QUEUE_KEY)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  }, [])

  const saveSyncQueue = useCallback((queue) => {
    try {
      localStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue))
      syncQueueRef.current = queue
      setPendingCount(queue.length)
    } catch {
      // Storage full or unavailable
    }
  }, [])

  const addToSyncQueue = useCallback((action) => {
    const queue = getSyncQueue()
    const entry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      action,
      retries: 0,
    }
    queue.push(entry)
    saveSyncQueue(queue)
    return entry
  }, [getSyncQueue, saveSyncQueue])

  const removeFromSyncQueue = useCallback((id) => {
    const queue = getSyncQueue().filter((item) => item.id !== id)
    saveSyncQueue(queue)
  }, [getSyncQueue, saveSyncQueue])

  // ─── Background Sync Processing ───────────────────────────────────────────
  const processSyncQueue = useCallback(async () => {
    if (!navigator.onLine || isSyncing) return

    const queue = getSyncQueue()
    if (queue.length === 0) return

    setIsSyncing(true)
    const failed = []

    for (const item of queue) {
      try {
        // Attempt to sync the item
        // In production, this would make the actual API call
        await performSync(item)
        removeFromSyncQueue(item.id)
      } catch (err) {
        item.retries = (item.retries || 0) + 1
        if (item.retries < 3) {
          failed.push(item)
        }
        // Drop items that failed 3+ times
      }
    }

    if (failed.length > 0) {
      saveSyncQueue(failed)
    }

    setIsSyncing(false)
    setLastSynced(new Date())
  }, [isSyncing, getSyncQueue, removeFromSyncQueue, saveSyncQueue])

  // Simulated sync operation - replace with actual API calls
  const performSync = async (item) => {
    // Simulate network request
    await new Promise((resolve) => setTimeout(resolve, 500))
    // In production: make the actual API call here
    // await axiosClient.post(item.action.endpoint, item.action.payload)
    return true
  }

  // ─── Offline Data Cache ───────────────────────────────────────────────────
  const cacheData = useCallback((key, data) => {
    try {
      const cache = JSON.parse(localStorage.getItem(OFFLINE_DATA_KEY) || "{}")
      cache[key] = {
        data,
        timestamp: new Date().toISOString(),
      }
      localStorage.setItem(OFFLINE_DATA_KEY, JSON.stringify(cache))
    } catch {
      // Storage full
    }
  }, [])

  const getCachedData = useCallback((key) => {
    try {
      const cache = JSON.parse(localStorage.getItem(OFFLINE_DATA_KEY) || "{}")
      return cache[key]?.data || null
    } catch {
      return null
    }
  }, [])

  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem(OFFLINE_DATA_KEY)
    } catch {
      // Ignore
    }
  }, [])

  // ─── Service Worker Registration ──────────────────────────────────────────
  const registerServiceWorker = useCallback(async () => {
    if (!("serviceWorker" in navigator)) {
      return null
    }

    try {
      const registration = await navigator.serviceWorker.register("/sw.js")
      return registration
    } catch (err) {
      console.warn("Service worker registration failed:", err)
      return null
    }
  }, [])

  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSynced,
    addToSyncQueue,
    processSyncQueue,
    cacheData,
    getCachedData,
    clearCache,
    registerServiceWorker,
  }
}

export default useOffline
