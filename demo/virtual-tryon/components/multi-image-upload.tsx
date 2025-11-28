'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { HiPhoto, HiXMark } from 'react-icons/hi2'
import { cn } from '@/lib/utils'

interface GarmentImage {
  file: File
  preview: string
  id: string
  category?: string
}

interface MultiImageUploadProps {
  onImagesChange: (files: File[]) => void
  currentImages: File[]
  label: string
  description?: string
  accept?: Record<string, string[]>
  maxFiles?: number
  categories?: string[]
}

export function MultiImageUpload({
  onImagesChange,
  currentImages,
  label,
  description,
  accept = { 'image/*': ['.jpeg', '.jpg', '.png', '.webp'] },
  maxFiles = 10,
  categories = ['Top', 'Jeans', 'Scarf', 'Hat', 'Glasses'],
}: MultiImageUploadProps) {
  const [garmentImages, setGarmentImages] = useState<GarmentImage[]>(() => {
    // Initialize from currentImages if provided
    return currentImages.map((file, index) => ({
      file,
      preview: URL.createObjectURL(file),
      id: `garment-${index}`,
    }))
  })

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

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-neutral-700 mb-2">
        {label}
      </label>
      {description && (
        <p className="text-sm text-neutral-500 mb-4">{description}</p>
      )}

      {/* Uploaded Images Grid */}
      {garmentImages.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-4">
          {garmentImages.map((garment) => (
            <div
              key={garment.id}
              className="relative aspect-square rounded-lg overflow-hidden border-2 border-neutral-200 group"
            >
              <img
                src={garment.preview}
                alt={`Garment ${garment.id}`}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => handleRemove(garment.id)}
                className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1.5 hover:bg-red-600 transition-colors shadow-lg opacity-0 group-hover:opacity-100"
                aria-label="Remove image"
              >
                <HiXMark className="w-4 h-4" />
              </button>
              {garment.category && (
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs px-2 py-1">
                  {garment.category}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Dropzone */}
      {canAddMore && (
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-neutral-300 hover:border-primary-400 hover:bg-neutral-50'
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
              <HiPhoto className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-neutral-700">
                {isDragActive
                  ? 'Drop images here'
                  : 'Drag & drop garment images here'}
              </p>
              <p className="text-xs text-neutral-500 mt-1">
                or click to browse
              </p>
            </div>
            <p className="text-xs text-neutral-400">
              {garmentImages.length > 0
                ? `${garmentImages.length} of ${maxFiles} images uploaded`
                : `Upload up to ${maxFiles} images`}
            </p>
            {categories.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center mt-2">
                {categories.map((category) => (
                  <span
                    key={category}
                    className="text-xs px-2 py-1 bg-primary-50 text-primary-600 rounded-full"
                  >
                    {category}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {!canAddMore && (
        <div className="text-center text-sm text-neutral-500 py-4">
          Maximum {maxFiles} images reached. Remove some to add more.
        </div>
      )}
    </div>
  )
}

