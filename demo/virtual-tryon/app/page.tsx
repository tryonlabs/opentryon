'use client'

import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ImageUpload } from '@/components/image-upload'
import { MultiImageUpload } from '@/components/multi-image-upload'
import { HiSparkles, HiPhoto } from 'react-icons/hi2'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [modelImage, setModelImage] = useState<File | null>(null)
  const [garmentImages, setGarmentImages] = useState<File[]>([])
  const [resultImage, setResultImage] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [provider, setProvider] = useState<'nano-banana' | 'nano-banana-pro'>('nano-banana')

  const handleGenerate = async () => {
    if (!modelImage || garmentImages.length === 0) {
      setError('Please upload a model image and at least one garment image')
      return
    }

    setIsGenerating(true)
    setError(null)
    setResultImage(null)

    try {
      // Create FormData
      const formData = new FormData()
      formData.append('model_image', modelImage)
      
      // Append all garment images
      garmentImages.forEach((garment) => {
        formData.append('garment_images', garment)
      })
      
      formData.append('provider', provider)
      formData.append('prompt', 'Create a realistic virtual try-on image showing the person wearing the provided garments. CRITICAL REQUIREMENTS - Preserve all details exactly: 1. GARMENT EXTRACTION: The garment images may contain people wearing the garments. IGNORE and EXTRACT ONLY the garment itself - do not use any person, model, or human figure from the garment images. Focus solely on the garment: its shape, design, patterns, colors, textures, and all visual details. Remove or ignore any human elements from garment images. 2. GARMENT PRESERVATION: Keep ALL garment details completely intact - patterns, colors, textures, designs, prints, logos, text, embroidery, sequins, and any decorative elements must remain identical to the original garment images. Do not alter, fade, or modify any garment features. 3. PERSON PRESERVATION: Keep the person\'s face, body shape, skin tone, hair, and physical characteristics exactly as shown in the FIRST image (model image). Only apply the extracted garments from the subsequent images to this person. Do not use any person from garment images. 4. PARTIAL GARMENT HANDLING: If the person in the model image is wearing a full-body outfit (dress, jumpsuit, etc.) but the provided garment is only upper-body (top, shirt, blouse) or lower-body (pants, jeans, skirt), place the provided garment correctly over the corresponding body part. For the remaining uncovered body parts, generate an appropriate complementary garment that matches: (a) the person\'s physical characteristics and body type, (b) the person\'s style and personality traits visible in the model image, (c) the style, color scheme, and design aesthetic of the provided garment. The complementary garment should create a cohesive, harmonious outfit that looks natural and well-coordinated. 5. FITTING: The extracted garments should fit naturally on the person\'s body from the first image, following their body contours and proportions realistically, while maintaining all original garment details from the garment images. 6. COMPOSITION: The first image is the model/person to dress. The following images contain garments (top, bottom, accessories, etc.) - extract ONLY the garments from these images, ignoring any people shown. Combine the extracted garments to create a cohesive outfit where each garment maintains its original appearance and fits the person naturally. 7. REALISM: The final image should look like a professional photograph of the person from the first image wearing the exact extracted garments (and complementary garments if needed), with realistic lighting, shadows, and fabric draping.')

      // Make API request
      const response = await fetch(`${API_URL}/api/v1/virtual-tryon`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate try-on image')
      }

      const data = await response.json()
      
      if (data.success && data.image) {
        setResultImage(data.image)
      } else {
        throw new Error('No image received from server')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while generating the try-on image')
      console.error('Error generating try-on:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-primary-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              
            <img src="https://tryonlabs.ai/static/media/tryonai-logo.97121ed90f1dff3f0a6f.png" alt="TryOn AI" className="w-10 h-10 rounded-lg" />
              
              <div>
                <h1 className="text-2xl font-bold text-neutral-900">
                  TryOn AI
                </h1>
                <p className="text-sm text-neutral-500">
                  Virtual Try-On Demo
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Provider Selection */}
        <div className="mb-8 flex justify-center">
          <div className="bg-white rounded-lg border border-neutral-200 p-4">
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Model Provider
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="provider"
                  value="nano-banana"
                  checked={provider === 'nano-banana'}
                  onChange={(e) => setProvider(e.target.value as 'nano-banana')}
                  className="mr-2"
                />
                <span className="text-sm text-neutral-700">Nano Banana (Fast)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="provider"
                  value="nano-banana-pro"
                  checked={provider === 'nano-banana-pro'}
                  onChange={(e) => setProvider(e.target.value as 'nano-banana-pro')}
                  className="mr-2"
                />
                <span className="text-sm text-neutral-700">Nano Banana Pro (4K)</span>
              </label>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Section 1: Model Image Upload */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <HiPhoto className="w-5 h-5" />
                <span>Model Image</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ImageUpload
                label="Upload Model/Person Image"
                description="Upload a single image of the person/model"
                onImageChange={setModelImage}
                currentImage={modelImage}
              />
            </CardContent>
          </Card>

          {/* Section 2: Garment Images Upload */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <HiPhoto className="w-5 h-5" />
                <span>Garment Images</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MultiImageUpload
                label="Upload Garment Images"
                description="Upload multiple garment images (top, jeans, scarf, hat, glasses, etc.)"
                onImagesChange={setGarmentImages}
                currentImages={garmentImages}
                maxFiles={10}
                categories={['Top', 'Jeans', 'Scarf', 'Hat', 'Glasses', 'Shoes', 'Jacket']}
              />
            </CardContent>
          </Card>

          {/* Section 3: Result Image */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <HiSparkles className="w-5 h-5" />
                <span>Result</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full">
                {resultImage ? (
                  <div className="relative w-full aspect-square rounded-lg overflow-hidden border-2 border-neutral-200">
                    <img
                      src={resultImage}
                      alt="Try-on result"
                      className="w-full h-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="relative w-full aspect-square rounded-lg border-2 border-dashed border-neutral-300 flex items-center justify-center bg-neutral-50">
                    <div className="text-center">
                      <HiPhoto className="w-12 h-12 text-neutral-400 mx-auto mb-2" />
                      <p className="text-sm text-neutral-500">
                        Result will appear here
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 flex justify-center">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg max-w-2xl">
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <div className="mt-8 flex justify-center">
          <Button
            onClick={handleGenerate}
            disabled={!modelImage || garmentImages.length === 0 || isGenerating}
            className="px-8 py-3 text-lg"
            variant="primary"
          >
            {isGenerating ? (
              <span className="flex items-center space-x-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Generating...</span>
              </span>
            ) : (
              <span className="flex items-center space-x-2">
                <HiSparkles className="w-5 h-5" />
                <span>Generate Try-On</span>
              </span>
            )}
          </Button>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-white rounded-lg border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">
            How to use
          </h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-neutral-600">
            <li>Upload a model/person image in the first section</li>
            <li>Upload one or more garment images (top, jeans, scarf, hat, glasses, etc.) in the second section</li>
            <li>Click the "Generate Try-On" button to see the virtual try-on result</li>
            <li>The result will appear in the third section</li>
          </ol>
        </div>
      </main>
    </div>
  )
}

