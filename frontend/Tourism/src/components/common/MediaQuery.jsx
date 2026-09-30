import { useState, useEffect } from 'react'

/**
 * Media Query hook for responsive breakpoints.
 * Returns whether the current viewport matches the query.
 */
export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const media = window.matchMedia(query)
    if (media.matches !== matches) {
      setMatches(media.matches)
    }

    const listener = (e) => setMatches(e.matches)
    media.addEventListener('change', listener)

    return () => media.removeEventListener('change', listener)
  }, [matches, query])

  return matches
}

/**
 * Hook for common breakpoints.
 */
export const useBreakpoints = () => {
  const isMobile = useMediaQuery('(max-width: 639px)')
  const isTablet = useMediaQuery('(min-width: 640px) and (max-width: 1023px)')
  const isLaptop = useMediaQuery('(min-width: 1024px) and (max-width: 1279px)')
  const isDesktop = useMediaQuery('(min-width: 1280px)')
  const isLargeDesktop = useMediaQuery('(min-width: 1536px)')

  const isSmallScreen = isMobile || isTablet
  const isMediumScreen = isLaptop
  const isLargeScreen = isDesktop || isLargeDesktop

  const isTouchDevice = useMediaQuery('(hover: none) and (pointer: coarse)')
  const isLandscape = useMediaQuery('(orientation: landscape)')
  const isPortrait = useMediaQuery('(orientation: portrait)')

  return {
    isMobile,
    isTablet,
    isLaptop,
    isDesktop,
    isLargeDesktop,
    isSmallScreen,
    isMediumScreen,
    isLargeScreen,
    isTouchDevice,
    isLandscape,
    isPortrait,
  }
}

/**
 * Hook for device orientation.
 */
export const useOrientation = () => {
  const [orientation, setOrientation] = useState(
    typeof window !== 'undefined' && window.innerWidth > window.innerHeight
      ? 'landscape'
      : 'portrait'
  )

  useEffect(() => {
    const handleResize = () => {
      setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait')
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return orientation
}

/**
 * Hook for safe area insets (notch, home indicator).
 */
export const useSafeArea = () => {
  const [safeArea, setSafeArea] = useState({
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
  })

  useEffect(() => {
    const computeSafeArea = () => {
      const style = getComputedStyle(document.documentElement)
      setSafeArea({
        top: parseInt(style.getPropertyValue('--sat') || '0'),
        right: parseInt(style.getPropertyValue('--sar') || '0'),
        bottom: parseInt(style.getPropertyValue('--sab') || '0'),
        left: parseInt(style.getPropertyValue('--sal') || '0'),
      })
    }

    computeSafeArea()
  }, [])

  return safeArea
}

/**
 * Hook for viewport dimensions.
 */
export const useViewport = () => {
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  })

  useEffect(() => {
    const handleResize = () => {
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return viewport
}

/**
 * Hook for scroll position.
 */
export const useScrollPosition = () => {
  const [scrollPosition, setScrollPosition] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      setScrollPosition(window.scrollY)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return scrollPosition
}

/**
 * Hook for element visibility in viewport.
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
