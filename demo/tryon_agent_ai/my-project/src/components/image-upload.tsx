'use client'

import { useCallback, useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import { HiPhoto, HiXMark, HiPlus } from 'react-icons/hi2'
import { cn } from '@/lib/utils'
import { useTheme } from './ThemeProvider'

interface ImageUploadProps {
  onImageChange: (file: File | null) => void
  currentImage: File | null
  previewUrl?: string | null
  label?: string
  description?: string
  accept?: Record<string, string[]>
  maxFiles?: number
  multiple?: boolean
  layout?: 'grid' | 'horizontal' | 'masonry' | 'compact'
  gridCols?: 2 | 3 | 4 | 5
}

export function ImageUpload({
  onImageChange,
  currentImage,
  previewUrl,
  label,
  description,
  accept = { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
  maxFiles = 1,
  multiple = false,
  layout = 'grid',
  gridCols = 3,
}: ImageUploadProps) {
  const { theme } = useTheme()
  const [preview, setPreview] = useState<string | null>(previewUrl || null)
  const currentFileRef = useRef<File | null>(null)

  useEffect(() => {
    // Reset preview if no image
    if (!currentImage && !previewUrl) {
      setPreview(null)
      currentFileRef.current = null
      return
    }

    // Use previewUrl if provided (external preview)
    if (previewUrl) {
      setPreview(previewUrl)
      return
    }

    // Create preview from currentImage file
    if (currentImage) {
      // Check if this is the same file we already processed
      const isSameFile = currentFileRef.current === currentImage
      if (isSameFile) {
        // Already have preview for this file, don't recreate
        return
      }

      // Mark this file as processed
      currentFileRef.current = currentImage

      // Create new preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreview(reader.result as string)
      }
      reader.readAsDataURL(currentImage)
    }
  }, [currentImage, previewUrl])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        onImageChange(file)
      }
    },
    [onImageChange]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles,
    multiple,
    disabled: maxFiles === 1 && preview !== null,
  })

  const handleRemove = () => {
    onImageChange(null)
    setPreview(null)
  }

  const hasImage = preview !== null
  const canUpload = maxFiles === 1 ? !hasImage : true

  // Grid Layout (Default)
  if (layout === 'grid') {
    // Responsive grid: 1 col on mobile, 2 on tablet, original on desktop
    const gridColsClass = {
      2: 'grid-cols-1 sm:grid-cols-2',
      3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
      4: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4',
      5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
    }[gridCols] || 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'

    return (
      <div className="w-full">
        {label && (
          <label className={`block text-sm font-medium mb-2 sm:mb-3 ${
            theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
          }`}>
            {label}
          </label>
        )}
        {description && (
          <p className={`text-xs sm:text-sm mb-3 sm:mb-4 ${
            theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
          }`}>{description}</p>
        )}
        
        <div className={cn('grid gap-2 sm:gap-3 lg:gap-4', gridColsClass)}>
          {/* Upload Dropzone - Always First */}
          {canUpload && (
            <div
              {...getRootProps()}
              className={cn(
                'aspect-square border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center',
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : theme === 'dark'
                    ? 'border-gray-700 hover:border-primary-500 hover:bg-gray-800'
                    : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
              )}
              style={isDragActive 
                ? { borderColor: '#ef4444', backgroundColor: '#fef2f2', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                : { borderColor: '#d4d4d4', backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
              }
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center justify-center space-y-1 sm:space-y-2 p-2 sm:p-4">
                <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <HiPlus className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-primary-500" />
                </div>
                <div className="text-center">
                  <p className={`text-xs sm:text-sm font-medium ${
                    theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                  }`}>
                    {isDragActive ? 'Drop here' : 'Upload'}
                  </p>
                  <p className={`text-[10px] sm:text-xs mt-0.5 sm:mt-1 ${
                    theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
                  }`}>
                    {isDragActive ? 'Release' : 'Click or drag'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Uploaded Image - Only show once */}
          {hasImage && preview && (
            <div
              key={preview}
              className={`relative aspect-square rounded-lg overflow-hidden border-2 group ${
                theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
              }`}
              style={theme === 'dark'
                ? { 
                    borderColor: '#374151',
                    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.2)'
                  }
                : { 
                    borderColor: '#e5e5e5',
                    boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
                  }
              }
            >
              <img
                src={preview}
                alt="Preview"
                className="w-full h-full object-cover"
              />
              <button
                onClick={handleRemove}
                className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 bg-primary-500 text-white rounded-full p-1 sm:p-1.5 hover:bg-primary-600 transition-all opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3 sm:w-4 sm:h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Horizontal Scroll Layout
  if (layout === 'horizontal') {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-3">
            {label}
          </label>
        )}
        {description && (
          <p className="text-sm text-neutral-500 mb-4">{description}</p>
        )}
        
        <div className="flex gap-4 overflow-x-auto pb-2">
          {/* Upload Dropzone */}
          {canUpload && (
            <div
              {...getRootProps()}
              className={cn(
                'flex-shrink-0 w-32 h-32 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center',
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
              )}
              style={isDragActive 
                ? { borderColor: '#ef4444', backgroundColor: '#fef2f2', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                : { borderColor: '#d4d4d4', backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
              }
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center justify-center space-y-1">
                <HiPlus className="w-6 h-6 text-primary-500" />
                <p className="text-xs text-neutral-600">Add</p>
              </div>
            </div>
          )}

          {/* Uploaded Image - Only show once */}
          {hasImage && preview && (
            <div
              key={preview}
              className="relative flex-shrink-0 w-32 h-32 rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={preview}
                alt="Preview"
                className="w-full h-full object-cover"
              />
              <button
                onClick={handleRemove}
                className="absolute top-1 right-1 bg-primary-500 text-white rounded-full p-1 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Masonry Layout
  if (layout === 'masonry') {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-3">
            {label}
          </label>
        )}
        {description && (
          <p className="text-sm text-neutral-500 mb-4">{description}</p>
        )}
        
        <div className="columns-3 gap-4">
          {/* Upload Dropzone */}
          {canUpload && (
            <div
              {...getRootProps()}
              className={cn(
                'mb-4 break-inside-avoid border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 p-8',
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
              )}
              style={isDragActive 
                ? { borderColor: '#ef4444', backgroundColor: '#fef2f2', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                : { borderColor: '#d4d4d4', backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
              }
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center justify-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <HiPlus className="w-6 h-6 text-primary-500" />
                </div>
                <p className="text-sm font-medium text-neutral-700 text-center">
                  {isDragActive ? 'Drop here' : 'Upload Image'}
                </p>
              </div>
            </div>
          )}

          {/* Uploaded Image - Only show once */}
          {hasImage && preview && (
            <div
              key={preview}
              className="relative mb-4 break-inside-avoid rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={preview}
                alt="Preview"
                className="w-full h-auto object-cover"
              />
              <button
                onClick={handleRemove}
                className="absolute top-2 right-2 bg-primary-500 text-white rounded-full p-1.5 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Compact Layout
  if (layout === 'compact') {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-3">
            {label}
          </label>
        )}
        {description && (
          <p className="text-sm text-neutral-500 mb-4">{description}</p>
        )}
        
        <div className="flex items-center gap-3">
          {/* Upload Dropzone - Compact */}
          {canUpload && (
            <div
              {...getRootProps()}
              className={cn(
                'w-20 h-20 flex-shrink-0 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center',
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
              )}
              style={isDragActive 
                ? { borderColor: '#ef4444', backgroundColor: '#fef2f2', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                : { borderColor: '#d4d4d4', backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
              }
            >
              <input {...getInputProps()} />
              <HiPlus className="w-6 h-6 text-primary-500" />
            </div>
          )}

          {/* Uploaded Image - Only show once */}
          {hasImage && preview && (
            <div
              key={preview}
              className="relative flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={preview}
                alt="Preview"
                className="w-full h-full object-cover"
              />
              <button
                onClick={handleRemove}
                className="absolute top-0 right-0 bg-primary-500 text-white rounded-full p-0.5 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Fallback to grid
  return null
}

