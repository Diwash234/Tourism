import { useState, useRef } from 'react'
import { FiPlay, FiPause, FiVolume2, FiVolumeX } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Audio component that adapts to different screen sizes.
 * - Mobile: Full-width audio player with large touch controls
 * - Tablet/Desktop: Compact audio player
 */
const ResponsiveAudio = ({
  src,
  title,
  artist,
  autoPlay = false,
  loop = false,
  className = '',
}) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)
  const { isMobile } = useResponsive()

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setProgress((audioRef.current.currentTime / audioRef.current.duration) * 100)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleSeek = (e) => {
    if (audioRef.current) {
      const rect = e.currentTarget.getBoundingClientRect()
      const pos = (e.clientX - rect.left) / rect.width
      audioRef.current.currentTime = pos * duration
    }
  }

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 ${
      isMobile ? 'p-4' : 'p-4'
    } ${className}`}>
      <audio
        ref={audioRef}
        src={src}
        autoPlay={autoPlay}
        loop={loop}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
      />

      <div className="flex items-center gap-4">
        {/* Play button */}
        <button
          onClick={togglePlay}
          className={`${isMobile ? 'w-12 h-12' : 'w-10 h-10'} bg-emerald-600 text-white rounded-full flex items-center justify-center hover:bg-emerald-700 transition-colors flex-shrink-0`}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <FiPause className="w-5 h-5" /> : <FiPlay className="w-5 h-5 ml-0.5" />}
        </button>

        {/* Track info and progress */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <p className={`font-medium text-gray-900 dark:text-gray-100 truncate ${isMobile ? 'text-base' : 'text-sm'}`}>
              {title || 'Audio Track'}
            </p>
            <span className="text-gray-500 text-sm flex-shrink-0 ml-2">
              {formatTime(progress * duration / 100)} / {formatTime(duration)}
            </span>
          </div>

          {artist && (
            <p className={`text-gray-500 dark:text-gray-400 truncate ${isMobile ? 'text-sm' : 'text-xs'}`}>
              {artist}
            </p>
          )}

          {/* Progress bar */}
          <div
            className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full mt-2 cursor-pointer"
            onClick={handleSeek}
          >
            <div
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Mute button */}
        <button
          onClick={toggleMute}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0"
          aria-label={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? <FiVolumeX className="w-5 h-5" /> : <FiVolume2 className="w-5 h-5" />}
        </button>
      </div>
    </div>
  )
}

export default ResponsiveAudio
