import { useState, useEffect } from 'react'

/**
 * Hook for responsive design across all device sizes.
 * Provides breakpoint detection, device type, and orientation.
 */
const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  })

  const [deviceType, setDeviceType] = useState('desktop')
  const [orientation, setOrientation] = useState('portrait')
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      const height = window.innerHeight

      setWindowSize({ width, height })

      // Determine device type
      if (width < 640) {
        setDeviceType('mobile')
      } else if (width < 1024) {
        setDeviceType('tablet')
      } else if (width < 1280) {
        setDeviceType('laptop')
      } else {
        setDeviceType('desktop')
      }

      // Determine orientation
      setOrientation(width > height ? 'landscape' : 'portrait')

      // Detect touch device
      setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0)
    }

    // Initial check
    handleResize()

    // Add event listener
    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Breakpoint helpers
  const isMobile = deviceType === 'mobile'
  const isTablet = deviceType === 'tablet'
  const isLaptop = deviceType === 'laptop'
  const isDesktop = deviceType === 'desktop'
  const isSmallScreen = isMobile || isTablet
  const isLargeScreen = isLaptop || isDesktop

  // Responsive value helper
  const responsive = (values) => {
    if (isMobile) return values.mobile
    if (isTablet) return values.tablet
    if (isLaptop) return values.laptop
    return values.desktop
  }

  return {
    windowSize,
    deviceType,
    orientation,
    isTouch,
    isMobile,
    isTablet,
    isLaptop,
    isDesktop,
    isSmallScreen,
    isLargeScreen,
    responsive,
  }
}

export default useResponsive
