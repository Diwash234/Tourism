import { useState, useRef } from 'react'
import { FiUpload, FiX, FiFile, FiCheck } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive File Upload component that adapts to different screen sizes.
 * - Mobile: Full-width upload area with large touch target
 * - Tablet/Desktop: Drag-and-drop zone with file list
 */
const ResponsiveFileUpload = ({
  onFileSelect,
  accept = '*',
  multiple = false,
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  label = 'Upload files',
  description = 'Drag and drop files here, or click to browse',
  className = '',
}) => {
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const { isMobile } = useResponsive()

  const handleFiles = (fileList) => {
    setError('')
    const newFiles = Array.from(fileList)

    // Validate file size
    const oversizedFiles = newFiles.filter((file) => file.size > maxSize)
    if (oversizedFiles.length > 0) {
      setError(`Some files exceed the maximum size of ${Math.round(maxSize / 1024 / 1024)}MB`)
      return
    }

    // Validate number of files
    if (!multiple && newFiles.length > 1) {
      setError('Only one file can be uploaded')
      return
    }

    if (files.length + newFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`)
      return
    }

    const updatedFiles = multiple ? [...files, ...newFiles] : newFiles
    setFiles(updatedFiles)
    onFileSelect?.(multiple ? updatedFiles : newFiles[0])
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleRemoveFile = (index) => {
    const updatedFiles = files.filter((_, i) => i !== index)
    setFiles(updatedFiles)
    onFileSelect?.(multiple ? updatedFiles : null)
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className={className}>
      {label && (
        <label className={`block font-medium text-gray-700 dark:text-gray-300 ${isMobile ? 'text-base mb-2' : 'text-sm mb-1'}`}>
          {label}
        </label>
      )}

      {/* Upload Area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl text-center cursor-pointer transition-colors
          ${isMobile ? 'p-6' : 'p-8'}
          ${isDragging
            ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-emerald-500 hover:bg-gray-50 dark:hover:bg-gray-800'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
        <div className={`flex flex-col items-center ${isMobile ? 'gap-3' : 'gap-2'}`}>
          <div className={`${isMobile ? 'w-12 h-12' : 'w-10 h-10'} bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center`}>
            <FiUpload className={`${isMobile ? 'w-6 h-6' : 'w-5 h-5'} text-gray-400`} />
          </div>
          <p className={`text-gray-600 dark:text-gray-400 ${isMobile ? 'text-base' : 'text-sm'}`}>
            {description}
          </p>
          <p className={`text-gray-400 ${isMobile ? 'text-sm' : 'text-xs'}`}>
            Max {Math.round(maxSize / 1024 / 1024)}MB {multiple ? `• Up to ${maxFiles} files` : ''}
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <p className={`mt-2 text-red-500 ${isMobile ? 'text-sm' : 'text-xs'}`} role="alert">
          {error}
        </p>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, index) => (
            <div
              key={index}
              className={`flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg ${
                isMobile ? 'text-base' : 'text-sm'
              }`}
            >
              <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-900/20 rounded flex items-center justify-center flex-shrink-0">
                <FiFile className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{file.name}</p>
                <p className="text-gray-500 text-xs">{formatFileSize(file.size)}</p>
              </div>
              <FiCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemoveFile(index)
                }}
                className="p-1 text-gray-400 hover:text-red-500 flex-shrink-0"
                aria-label={`Remove ${file.name}`}
              >
                <FiX className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ResponsiveFileUpload
