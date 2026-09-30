import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Performance utilities for better rendering across all devices.
 */

/**
 * Hook for lazy loading components.
 */
export const useLazyLoad = (options = {}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [ref, setRef] = useState(null)

  useEffect(() => {
    if (!ref) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.1, ...options }
    )

    observer.observe(ref)
    return () => observer.disconnect()
  }, [ref, options])

  return [setRef, isVisible]
}

/**
 * Hook for memoizing expensive calculations.
 */
export const useMemoizedCallback = (callback, deps) => {
  const memoized = useCallback(callback, deps)
  return memoized
}

/**
 * Hook for throttling scroll events.
 */
export const useThrottledScroll = (callback, delay = 100) => {
  const [scrollY, setScrollY] = useState(0)
  const ticking = useRef(false)

  useEffect(() => {
    const handleScroll = () => {
      if (!ticking.current) {
        window.requestAnimationFrame(() => {
          setScrollY(window.scrollY)
          callback(window.scrollY)
          ticking.current = false
        })
        ticking.current = true
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [callback])

  return scrollY
}

/**
 * Hook for detecting when element is in viewport.
 */
export const useInView = (options = {}) => {
  const [isInView, setIsInView] = useState(false)
  const [ref, setRef] = useState(null)

  useEffect(() => {
    if (!ref) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsInView(entry.isIntersecting)
      },
      { threshold: 0.1, ...options }
    )

    observer.observe(ref)
    return () => observer.disconnect()
  }, [ref, options])

  return [setRef, isInView]
}

/**
 * Hook for measuring render performance.
 */
export const useRenderTime = (componentName) => {
  const renderCount = useRef(0)
  const lastRenderTime = useRef(performance.now())

  useEffect(() => {
    renderCount.current += 1
    const now = performance.now()
    const timeSinceLastRender = now - lastRenderTime.current
    lastRenderTime.current = now

    if (process.env.NODE_ENV === 'development') {
      console.log(`[${componentName}] Render #${renderCount.current} took ${timeSinceLastRender.toFixed(2)}ms`)
    }
  })

  return renderCount.current
}

/**
 * Hook for detecting slow devices.
 */
export const useDevicePerformance = () => {
  const [performanceLevel, setPerformanceLevel] = useState('unknown')

  useEffect(() => {
    const checkPerformance = () => {
      // Check device memory
      const memory = navigator.deviceMemory
      if (memory && memory < 4) {
        setPerformanceLevel('low')
        return
      }

      // Check CPU cores
      const cores = navigator.hardwareConcurrency
      if (cores && cores < 4) {
        setPerformanceLevel('low')
        return
      }

      // Check connection
      const connection = navigator.connection
      if (connection) {
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
          setPerformanceLevel('low')
          return
        }
        if (connection.effectiveType === '3g') {
          setPerformanceLevel('medium')
          return
        }
      }

      setPerformanceLevel('high')
    }

    checkPerformance()
  }, [])

  return performanceLevel
}

/**
 * Hook for optimizing images based on device.
 */
export const useOptimizedImage = (src, options = {}) => {
  const { maxWidth = 800, quality = 75 } = options
  const performanceLevel = useDevicePerformance()
  const [optimizedSrc, setOptimizedSrc] = useState(src)

  useEffect(() => {
    if (!src) return

    // Adjust quality based on device performance
    let adjustedQuality = quality
    if (performanceLevel === 'low') {
      adjustedQuality = 50
    } else if (performanceLevel === 'medium') {
      adjustedQuality = 65
    }

    // Add image optimization parameters
    const url = new URL(src, window.location.origin)
    url.searchParams.set('w', maxWidth.toString())
    url.searchParams.set('q', adjustedQuality.toString())

    setOptimizedSrc(url.toString())
  }, [src, maxWidth, quality, performanceLevel])

  return optimizedSrc
}

/**
 * Hook for preloading critical resources.
 */
export const usePreload = (resources) => {
  useEffect(() => {
    resources.forEach(({ href, as, type }) => {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.href = href
      link.as = as
      if (type) link.type = type
      document.head.appendChild(link)
    })
  }, [resources])
}

/**
 * Hook for detecting reduced motion preference.
 */
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handler = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handler)

    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return prefersReducedMotion
}

/**
 * Hook for detecting color scheme preference.
 */
export const useColorScheme = () => {
  const [colorScheme, setColorScheme] = useState('light')

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setColorScheme(mediaQuery.matches ? 'dark' : 'light')

    const handler = (e) => setColorScheme(e.matches ? 'dark' : 'light')
    mediaQuery.addEventListener('change', handler)

    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return colorScheme
}

/**
 * Hook for detecting online/offline status.
 */
export const useOnlineStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}

/**
 * Hook for detecting visibility change.
 */
export const useVisibilityChange = (callback) => {
  useEffect(() => {
    const handleVisibilityChange = () => {
      callback(document.hidden)
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [callback])
}

/**
 * Hook for request idle callback.
 */
export const useIdleCallback = (callback, timeout = 1000) => {
  useEffect(() => {
    const id = window.requestIdleCallback(callback, { timeout })
    return () => window.cancelIdleCallback(id)
  }, [callback, timeout])
}

/**
 * Hook for measuring FPS.
 */
export const useFPS = () => {
  const [fps, setFps] = useState(60)

  useEffect(() => {
    let frameCount = 0
    let lastTime = performance.now()
    let animationId

    const measureFPS = () => {
      frameCount++
      const currentTime = performance.now()

      if (currentTime - lastTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (currentTime - lastTime)))
        frameCount = 0
        lastTime = currentTime
      }

      animationId = requestAnimationFrame(measureFPS)
    }

    animationId = requestAnimationFrame(measureFPS)
    return () => cancelAnimationFrame(animationId)
  }, [])

  return fps
}
