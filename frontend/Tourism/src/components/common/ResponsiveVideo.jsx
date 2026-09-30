import { useState, useRef } from 'react'
import { FiPlay, FiPause, FiVolume2, FiVolumeX, FiMaximize2 } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Video component that adapts to different screen sizes.
 * - Mobile: Full-width video with touch controls
 * - Tablet/Desktop: Inline video with hover controls
 */
const ResponsiveVideo = ({
  src,
  poster,
  title,
  autoPlay = false,
  loop = false,
  muted = false,
  controls = true,
  className = '',
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(muted)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const [showControls, setShowControls] = useState(true)
  const videoRef = useRef(null)
  const { isMobile } = useResponsive()

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setProgress((videoRef.current.currentTime / videoRef.current.duration) * 100)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

  const handleSeek = (e) => {
    if (videoRef.current) {
      const rect = e.currentTarget.getBoundingClientRect()
      const pos = (e.clientX - rect.left) / rect.width
      videoRef.current.currentTime = pos * duration
    }
  }

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        videoRef.current.requestFullscreen()
      }
    }
  }

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  return (
    <div
      className={`relative bg-black rounded-xl overflow-hidden group ${className}`}
      onMouseEnter={() => !isMobile && setShowControls(true)}
      onMouseLeave={() => !isMobile && !isPlaying && setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        loop={loop}
        muted={isMuted}
        controls={false}
        className="w-full h-full object-cover"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onClick={togglePlay}
      />

      {/* Play button overlay */}
      {!isPlaying && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/30">
          <button
            onClick={togglePlay}
            className={`${isMobile ? 'w-16 h-16' : 'w-20 h-20'} bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-white hover:bg-white/30 transition-colors`}
            aria-label="Play video"
          >
            <FiPlay className={`${isMobile ? 'w-8 h-8' : 'w-10 h-10'} ml-1`} />
          </button>
        </div>
      )}

      {/* Controls */}
      {controls && (showControls || isMobile) && (
        <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent ${
          isMobile ? 'p-3' : 'p-4'
        }`}>
          {/* Progress bar */}
          <div
            className="w-full h-1 bg-white/30 rounded-full mb-3 cursor-pointer"
            onClick={handleSeek}
          >
            <div
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Play/Pause */}
              <button
                onClick={togglePlay}
                className="text-white hover:text-emerald-400 transition-colors"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <FiPause className="w-5 h-5" /> : <FiPlay className="w-5 h-5" />}
              </button>

              {/* Mute */}
              <button
                onClick={toggleMute}
                className="text-white hover:text-emerald-400 transition-colors"
                aria-label={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <FiVolumeX className="w-5 h-5" /> : <FiVolume2 className="w-5 h-5" />}
              </button>

              {/* Time */}
              <span className="text-white text-sm">
                {formatTime(progress * duration / 100)} / {formatTime(duration)}
              </span>
            </div>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="text-white hover:text-emerald-400 transition-colors"
              aria-label="Fullscreen"
            >
              <FiMaximize2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Title */}
      {title && (
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4">
          <h3 className="text-white font-medium">{title}</h3>
        </div>
      )}
    </div>
  )
}

export default ResponsiveVideo
