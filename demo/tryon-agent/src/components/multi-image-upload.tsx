'use client'

import { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { HiPhoto, HiXMark, HiPlus } from 'react-icons/hi2'
import { cn } from '@/lib/utils'
import { useTheme } from './ThemeProvider'

interface GarmentImage {
  file: File
  preview: string
  id: string
  category?: string
}

interface MultiImageUploadProps {
  onImagesChange: (files: File[]) => void
  currentImages: File[]
  label?: string
  description?: string
  accept?: Record<string, string[]>
  maxFiles?: number
  categories?: string[]
  layout?: 'grid' | 'horizontal' | 'masonry' | 'compact'
  gridCols?: 2 | 3 | 4 | 5
}

export function MultiImageUpload({
  onImagesChange,
  currentImages,
  label,
  description,
  accept = { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
  maxFiles = 10,
  categories = ['Top', 'Jeans', 'Scarf', 'Hat', 'Glasses'],
  layout = 'grid',
  gridCols = 4,
}: MultiImageUploadProps) {
  const { theme } = useTheme()
  const [garmentImages, setGarmentImages] = useState<GarmentImage[]>([])

  useEffect(() => {
    // Initialize from currentImages
    const images = currentImages.map((file, index) => ({
      file,
      preview: URL.createObjectURL(file),
      id: `garment-${index}-${Date.now()}`,
    }))
    setGarmentImages(images)
  }, [currentImages])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newImages: GarmentImage[] = acceptedFiles.map((file) => ({
        file,
        preview: URL.createObjectURL(file),
        id: `garment-${Date.now()}-${Math.random()}`,
      }))

      const updatedImages = [...garmentImages, ...newImages].slice(0, maxFiles)
      setGarmentImages(updatedImages)
      onImagesChange(updatedImages.map((img) => img.file))
    },
    [garmentImages, maxFiles, onImagesChange]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: true,
    maxFiles,
  })

  const handleRemove = (id: string) => {
    const updatedImages = garmentImages.filter((img) => {
      if (img.id === id) {
        URL.revokeObjectURL(img.preview)
        return false
      }
      return true
    })
    setGarmentImages(updatedImages)
    onImagesChange(updatedImages.map((img) => img.file))
  }

  const canAddMore = garmentImages.length < maxFiles

  // Grid Layout (Default) - Upload zone as first item
  if (layout === 'grid') {
    // Responsive grid: 2 cols on mobile, 3 on tablet, original on desktop
    const gridColsClass = {
      2: 'grid-cols-2',
      3: 'grid-cols-2 sm:grid-cols-3',
      4: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4',
      5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
    }[gridCols] || 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4'

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
          {canAddMore && (
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
                {garmentImages.length > 0 && (
                  <p className={`text-[10px] sm:text-xs mt-1 sm:mt-2 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-neutral-400'
                  }`}>
                    {garmentImages.length} / {maxFiles}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Uploaded Images */}
          {garmentImages.map((garment) => (
            <div
              key={garment.id}
              className="relative aspect-square rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={garment.preview}
                alt={`Garment ${garment.id}`}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => handleRemove(garment.id)}
                className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 bg-primary-500 text-white rounded-full p-1 sm:p-1.5 hover:bg-primary-600 transition-all opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3 sm:w-4 sm:h-4" />
              </button>
              {garment.category && (
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1">
                  {garment.category}
                </div>
              )}
            </div>
          ))}
        </div>

        {categories.length > 0 && garmentImages.length === 0 && (
          <div className="flex flex-wrap gap-1.5 sm:gap-2 justify-center mt-3 sm:mt-4">
            {categories.map((category) => (
              <span
                key={category}
                className="text-[10px] sm:text-xs px-2 sm:px-3 py-0.5 sm:py-1 bg-primary-50 text-primary-600 rounded-full font-medium"
              >
                {category}
              </span>
            ))}
          </div>
        )}

        {!canAddMore && (
          <div className={`text-center text-sm py-4 mt-4 ${
            theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
          }`}>
            Maximum {maxFiles} images reached. Remove some to add more.
          </div>
        )}
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
          {/* Upload Dropzone - First */}
          {canAddMore && (
            <div
              {...getRootProps()}
              className={cn(
                'flex-shrink-0 w-32 h-32 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center',
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
              <div className="flex flex-col items-center justify-center space-y-1">
                <HiPlus className="w-6 h-6 text-primary-500" />
                <p className={`text-xs ${
                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-600'
                }`}>Add</p>
              </div>
            </div>
          )}

          {/* Uploaded Images */}
          {garmentImages.map((garment) => (
            <div
              key={garment.id}
              className="relative flex-shrink-0 w-32 h-32 rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={garment.preview}
                alt={`Garment ${garment.id}`}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => handleRemove(garment.id)}
                className="absolute top-1 right-1 bg-primary-500 text-white rounded-full p-1 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3" />
              </button>
            </div>
          ))}
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
          {canAddMore && (
            <div
              {...getRootProps()}
              className={cn(
                'mb-4 break-inside-avoid border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 p-8',
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
              <div className="flex flex-col items-center justify-center space-y-2">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <HiPlus className="w-6 h-6 text-primary-500" />
                </div>
                <p className={`text-sm font-medium text-center ${
                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                }`}>
                  {isDragActive ? 'Drop here' : 'Upload'}
                </p>
              </div>
            </div>
          )}

          {/* Uploaded Images */}
          {garmentImages.map((garment) => (
            <div
              key={garment.id}
              className="relative mb-4 break-inside-avoid rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={garment.preview}
                alt={`Garment ${garment.id}`}
                className="w-full h-auto object-cover"
              />
              <button
                onClick={() => handleRemove(garment.id)}
                className="absolute top-2 right-2 bg-primary-500 text-white rounded-full p-1.5 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-4 h-4" />
              </button>
            </div>
          ))}
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

        <div className="flex items-center gap-3 flex-wrap">
          {/* Upload Dropzone - Compact */}
          {canAddMore && (
            <div
              {...getRootProps()}
              className={cn(
                'w-20 h-20 flex-shrink-0 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 flex items-center justify-center',
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
              <HiPlus className="w-6 h-6 text-primary-500" />
            </div>
          )}

          {/* Uploaded Images */}
          {garmentImages.map((garment) => (
            <div
              key={garment.id}
              className="relative w-20 h-20 rounded-lg overflow-hidden border-2 group"
              style={{ 
                borderColor: '#e5e5e5',
                boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
              }}
            >
              <img
                src={garment.preview}
                alt={`Garment ${garment.id}`}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => handleRemove(garment.id)}
                className="absolute top-0 right-0 bg-primary-500 text-white rounded-full p-0.5 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                aria-label="Remove image"
              >
                <HiXMark className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return null
}

