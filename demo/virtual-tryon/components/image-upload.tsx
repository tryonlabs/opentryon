'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { HiPhoto, HiXMark } from 'react-icons/hi2'
import { cn } from '@/lib/utils'

interface ImageUploadProps {
  onImageChange: (file: File | null) => void
  currentImage: File | null
  previewUrl?: string | null
  label: string
  description?: string
  accept?: Record<string, string[]>
  maxFiles?: number
  multiple?: boolean
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
}: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(previewUrl || null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        onImageChange(file)
        
        // Create preview
        const reader = new FileReader()
        reader.onloadend = () => {
          setPreview(reader.result as string)
        }
        reader.readAsDataURL(file)
      }
    },
    [onImageChange]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles,
    multiple,
  })

  const handleRemove = () => {
    onImageChange(null)
    setPreview(null)
  }

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-neutral-700 mb-2">
        {label}
      </label>
      {description && (
        <p className="text-sm text-neutral-500 mb-4">{description}</p>
      )}
      
      {preview ? (
        <div className="relative w-full aspect-square max-w-md mx-auto">
          <div className="relative w-full h-full rounded-lg overflow-hidden border-2 border-neutral-200">
            <img
              src={preview}
              alt="Preview"
              className="w-full h-full object-contain"
            />
          </div>
          <button
            onClick={handleRemove}
            className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1.5 hover:bg-red-600 transition-colors shadow-lg"
            aria-label="Remove image"
          >
            <HiXMark className="w-4 h-4" />
          </button>
        </div>
      ) : (
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
                {isDragActive ? 'Drop image here' : 'Drag & drop image here'}
              </p>
              <p className="text-xs text-neutral-500 mt-1">
                or click to browse
              </p>
            </div>
            <p className="text-xs text-neutral-400">
              Supports: JPEG, PNG, WebP
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

