'use client'

import { useState, useMemo, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { ImageUpload } from '../../../components/image-upload'
import { MultiImageUpload } from '../../../components/multi-image-upload'
import { HiSparkles, HiUser, HiXMark, HiMagnifyingGlass, HiPhoto } from 'react-icons/hi2'
import pricingConfig from '../../../data/pricing_config.json'
import { useTheme } from '../../../components/ThemeProvider'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Provider = 'nano-banana' | 'nano-banana-pro' | 'flux-2-pro' | 'flux-2-flex'

interface PricingConfig {
  models: {
    [key: string]: {
      pricing_strategy: string
      credits_per_image?: number
      credits_by_resolution?: { [key: string]: number }
      base_credits_by_mode?: { [key: string]: number }
      resolution_multipliers?: { [key: string]: number }
      input_image_multipliers?: { [key: string]: number }
      default_resolution?: string
      default_mode?: string
    }
  }
  fallback: {
    default_credits_per_image: number
  }
}

interface ImageDimensions {
  width: number
  height: number
}

function mapResolutionToNanoBananaPro(maxDimension: number): string {
  if (maxDimension <= 1500) {
    return '1K'
  } else if (maxDimension <= 3000) {
    return '2K'
  } else {
    return '4K'
  }
}

function findClosestResolution(
  width: number,
  height: number,
  availableResolutions: { [key: string]: number }
): string {
  const megapixels = (width * height) / 1_000_000
  let closestRes = '1024x1024'
  let minDiff = Infinity

  for (const [res, multiplier] of Object.entries(availableResolutions)) {
    // Parse resolution string like "1024x1024" to get dimensions
    const [resWidth, resHeight] = res.split('x').map(Number)
    const resMegapixels = (resWidth * resHeight) / 1_000_000
    const diff = Math.abs(resMegapixels - megapixels)
    
    if (diff < minDiff) {
      minDiff = diff
      closestRes = res
    }
  }

  return closestRes
}

function calculateCredits(
  provider: Provider,
  numGarmentImages: number,
  imageDimensions: ImageDimensions | null,
  pricingConfig: PricingConfig
): number {
  const modelConfig = pricingConfig.models[provider]
  if (!modelConfig) {
    return pricingConfig.fallback.default_credits_per_image
  }

  const totalInputImages = 1 + numGarmentImages // 1 model image + garment images

  switch (modelConfig.pricing_strategy) {
    case 'flat_rate':
      return modelConfig.credits_per_image || pricingConfig.fallback.default_credits_per_image

    case 'resolution_based':
      // Use image dimensions if available, otherwise use default
      if (imageDimensions) {
        const maxDimension = Math.max(imageDimensions.width, imageDimensions.height)
        const resolution = mapResolutionToNanoBananaPro(maxDimension)
        const creditsByRes = modelConfig.credits_by_resolution || {}
        return creditsByRes[resolution] || pricingConfig.fallback.default_credits_per_image
      }
      const defaultRes = modelConfig.default_resolution || '1K'
      const creditsByRes = modelConfig.credits_by_resolution || {}
      return creditsByRes[defaultRes] || pricingConfig.fallback.default_credits_per_image

    case 'dynamic':
      // For virtual try-on, we use multi-image mode
      const baseCredits = modelConfig.base_credits_by_mode?.['multi-image'] || 
                         modelConfig.base_credits_by_mode?.['image2image'] ||
                         pricingConfig.fallback.default_credits_per_image
      
      // Get resolution multiplier based on actual image dimensions
      let resolutionMultiplier = 1.0
      if (imageDimensions && modelConfig.resolution_multipliers) {
        const resolution = findClosestResolution(
          imageDimensions.width,
          imageDimensions.height,
          modelConfig.resolution_multipliers
        )
        resolutionMultiplier = modelConfig.resolution_multipliers[resolution] || 1.0
      } else {
        // Fallback to default resolution
        const defaultResolution = modelConfig.default_resolution || '1024x1024'
        resolutionMultiplier = modelConfig.resolution_multipliers?.[defaultResolution] || 1.0
      }
      
      // Get input image multiplier (cap at 8 images)
      const inputImageCount = Math.min(totalInputImages, 8)
      const inputImageMultiplier = modelConfig.input_image_multipliers?.[String(inputImageCount)] || 1.0
      
      return Math.round(baseCredits * resolutionMultiplier * inputImageMultiplier)

    default:
      return pricingConfig.fallback.default_credits_per_image
  }
}

export default function VirtualTryOnPage() {
  const { theme } = useTheme()
  const [modelImage, setModelImage] = useState<File | null>(null)
  const [garmentImages, setGarmentImages] = useState<File[]>([])
  const [resultImage, setResultImage] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [provider, setProvider] = useState<Provider>('nano-banana')
  const [imageDimensions, setImageDimensions] = useState<ImageDimensions | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  
  // Create preview URLs for model and garment images
  const [modelPreviewUrl, setModelPreviewUrl] = useState<string | null>(null)
  const [garmentPreviewUrls, setGarmentPreviewUrls] = useState<string[]>([])
  
  // Update preview URLs when images change
  useEffect(() => {
    if (modelImage) {
      const url = URL.createObjectURL(modelImage)
      setModelPreviewUrl(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setModelPreviewUrl(null)
    }
  }, [modelImage])
  
  useEffect(() => {
    const urls = garmentImages.map(file => URL.createObjectURL(file))
    setGarmentPreviewUrls(urls)
    return () => {
      urls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [garmentImages])

  // Extract image dimensions when model image is uploaded (reuse preview URL)
  useEffect(() => {
    if (modelPreviewUrl) {
      const img = new Image()
      
      img.onload = () => {
        setImageDimensions({
          width: img.width,
          height: img.height
        })
      }
      
      img.onerror = () => {
        setImageDimensions(null)
      }
      
      img.src = modelPreviewUrl
    } else {
      setImageDimensions(null)
    }
  }, [modelPreviewUrl])

  // Calculate credits based on provider, number of images, and image dimensions
  const estimatedCredits = useMemo(() => {
    return calculateCredits(
      provider,
      garmentImages.length,
      imageDimensions,
      pricingConfig as PricingConfig
    )
  }, [provider, garmentImages.length, imageDimensions])

  const handleGenerate = async () => {
    if (!modelImage || garmentImages.length === 0) {
      setError('Please upload a model image and at least one garment image')
      return
    }

    setIsGenerating(true)
    setError(null)
    setResultImage(null)

    try {
      const formData = new FormData()
      formData.append('model_image', modelImage)
      
      garmentImages.forEach((garment) => {
        formData.append('garment_images', garment)
      })
      
      formData.append('provider', provider)
      formData.append('prompt', 'Create a realistic virtual try-on image showing the person wearing the provided garments. CRITICAL REQUIREMENTS - Preserve all details exactly: 1. GARMENT EXTRACTION: The garment images may contain people wearing the garments. IGNORE and EXTRACT ONLY the garment itself - do not use any person, model, or human figure from the garment images. Focus solely on the garment: its shape, design, patterns, colors, textures, and all visual details. Remove or ignore any human elements from garment images. 2. GARMENT PRESERVATION: Keep ALL garment details completely intact - patterns, colors, textures, designs, prints, logos, text, embroidery, sequins, and any decorative elements must remain identical to the original garment images. Do not alter, fade, or modify any garment features. 3. PERSON PRESERVATION: Keep the person\'s face, body shape, skin tone, hair, and physical characteristics exactly as shown in the FIRST image (model image). Only apply the extracted garments from the subsequent images to this person. Do not use any person from garment images. 4. PARTIAL GARMENT HANDLING: If the person in the model image is wearing a full-body outfit (dress, jumpsuit, etc.) but the provided garment is only upper-body (top, shirt, blouse) or lower-body (pants, jeans, skirt), place the provided garment correctly over the corresponding body part. For the remaining uncovered body parts, generate an appropriate complementary garment that matches: (a) the person\'s physical characteristics and body type, (b) the person\'s style and personality traits visible in the model image, (c) the style, color scheme, and design aesthetic of the provided garment. The complementary garment should create a cohesive, harmonious outfit that looks natural and well-coordinated. 5. FITTING: The extracted garments should fit naturally on the person\'s body from the first image, following their body contours and proportions realistically, while maintaining all original garment details from the garment images. 6. COMPOSITION: The first image is the model/person to dress. The following images contain garments (top, bottom, accessories, etc.) - extract ONLY the garments from these images, ignoring any people shown. Combine the extracted garments to create a cohesive outfit where each garment maintains its original appearance and fits the person naturally. 7. REALISM: The final image should look like a professional photograph of the person from the first image wearing the exact extracted garments (and complementary garments if needed), with realistic lighting, shadows, and fabric draping.')

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
      console.error('Error generating try-on:', err)
      
      // Provide more specific error messages
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setError(`Cannot connect to API server at ${API_URL}. Please ensure the server is running.`)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('An error occurred while generating the try-on image')
      }
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: 'var(--background)' }}>
      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b sticky top-0 z-10" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-primary)', boxShadow: 'var(--shadow-sm)' }}>
          <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-5">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-1 min-w-0">
                {/* Main Title */}
                <div className="min-w-0 flex-1">
                  <h1 className="text-xl sm:text-2xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>Virtual Try-On</h1>
                  <p className="text-xs sm:text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Generate realistic try-on images with AI</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 pt-4 sm:pt-6 lg:pt-8 pb-2 sm:pb-3 lg:pb-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 lg:gap-10 max-w-7xl mx-auto">
            {/* Left Panel - Input Form */}
            <div className="space-y-5 sm:space-y-6 lg:space-y-7">
              {/* Model Selection */}
              <Card className="!p-5 sm:!p-6">
                <CardHeader className="!mb-4 !pb-0">
                  <CardTitle className="!text-base sm:!text-lg font-semibold">Select Model</CardTitle>
                </CardHeader>
                <CardContent className="!pt-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
                    <button
                      onClick={() => setProvider('nano-banana')}
                      className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg border-2 text-xs sm:text-sm font-medium transition-all shadow-sm"
                      style={provider === 'nano-banana' 
                        ? { 
                            backgroundColor: 'var(--primary-50)', 
                            borderColor: 'var(--primary-500)', 
                            color: 'var(--primary-600)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                        : { 
                            backgroundColor: 'var(--card-bg)', 
                            borderColor: 'var(--border-primary)', 
                            color: 'var(--text-primary)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                      }
                      onMouseEnter={(e) => {
                        if (provider !== 'nano-banana') {
                          e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (provider !== 'nano-banana') {
                          e.currentTarget.style.backgroundColor = 'var(--card-bg)';
                        }
                      }}
                    >
                      Nano Banana
                    </button>
                    <button
                      onClick={() => setProvider('flux-2-pro')}
                      className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg border-2 text-xs sm:text-sm font-medium transition-all shadow-sm"
                      style={provider === 'flux-2-pro'
                        ? { 
                            backgroundColor: 'var(--primary-50)', 
                            borderColor: 'var(--primary-500)', 
                            color: 'var(--primary-600)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                        : { 
                            backgroundColor: 'var(--card-bg)', 
                            borderColor: 'var(--border-primary)', 
                            color: 'var(--text-primary)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                      }
                      onMouseEnter={(e) => {
                        if (provider !== 'flux-2-pro') {
                          e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (provider !== 'flux-2-pro') {
                          e.currentTarget.style.backgroundColor = 'var(--card-bg)';
                        }
                      }}
                    >
                      Flux 2 Pro
                    </button>
                    <button
                      onClick={() => setProvider('nano-banana-pro')}
                      className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg border-2 text-xs sm:text-sm font-medium transition-all shadow-sm"
                      style={provider === 'nano-banana-pro'
                        ? { 
                            backgroundColor: 'var(--primary-50)', 
                            borderColor: 'var(--primary-500)', 
                            color: 'var(--primary-600)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                        : { 
                            backgroundColor: 'var(--card-bg)', 
                            borderColor: 'var(--border-primary)', 
                            color: 'var(--text-primary)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                      }
                      onMouseEnter={(e) => {
                        if (provider !== 'nano-banana-pro') {
                          e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (provider !== 'nano-banana-pro') {
                          e.currentTarget.style.backgroundColor = 'var(--card-bg)';
                        }
                      }}
                    >
                      Nano Banana Pro
                    </button>
                    <button
                      onClick={() => setProvider('flux-2-flex')}
                      className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg border-2 text-xs sm:text-sm font-medium transition-all shadow-sm"
                      style={provider === 'flux-2-flex'
                        ? { 
                            backgroundColor: 'var(--primary-50)', 
                            borderColor: 'var(--primary-500)', 
                            color: 'var(--primary-600)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                        : { 
                            backgroundColor: 'var(--card-bg)', 
                            borderColor: 'var(--border-primary)', 
                            color: 'var(--text-primary)',
                            boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' 
                          }
                      }
                      onMouseEnter={(e) => {
                        if (provider !== 'flux-2-flex') {
                          e.currentTarget.style.backgroundColor = 'var(--bg-secondary)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (provider !== 'flux-2-flex') {
                          e.currentTarget.style.backgroundColor = 'var(--card-bg)';
                        }
                      }}
                    >
                      Flux 2 Flex
                    </button>
                  </div>
                </CardContent>
              </Card>

              {/* Model Image Upload */}
              <Card className="!p-5 sm:!p-6">
                <CardHeader className="!mb-4 !pb-0">
                  <CardTitle className="!text-base sm:!text-lg font-semibold">Model Image</CardTitle>
                </CardHeader>
                <CardContent className="!pt-4">
                  <ImageUpload
                    label="Upload Model/Person Image"
                    description="Upload a single image of the person/model"
                    onImageChange={setModelImage}
                    currentImage={modelImage}
                    layout="grid"
                    gridCols={3}
                  />
                </CardContent>
              </Card>

              {/* Garment Images Upload */}
              <Card className="!p-5 sm:!p-6">
                <CardHeader className="!mb-4 !pb-0">
                  <CardTitle className="!text-base sm:!text-lg font-semibold">Garment Images</CardTitle>
                </CardHeader>
                <CardContent className="!pt-4">
                  <MultiImageUpload
                    label="Upload Garment Images"
                    description="Upload multiple garment images (top, jeans, scarf, hat, glasses, etc.)"
                    onImagesChange={setGarmentImages}
                    currentImages={garmentImages}
                    maxFiles={10}
                    categories={['Top', 'Jeans', 'Scarf', 'Hat', 'Glasses', 'Shoes', 'Jacket']}
                    layout="grid"
                    gridCols={4}
                  />
                </CardContent>
              </Card>

              {/* Estimated Cost */}
              <div className="rounded-xl p-4 sm:p-5 shadow-sm border" style={{ backgroundColor: 'var(--bg-tertiary)', borderColor: 'var(--border-primary)', boxShadow: 'var(--shadow-sm)' }}>
                <div className="flex items-center justify-between flex-wrap gap-2 sm:gap-3 mb-2.5 sm:mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-base sm:text-lg">💰</span>
                    <span className="text-xs sm:text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Estimated Cost</span>
                  </div>
                  <span className="text-lg sm:text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{estimatedCredits} <span className="text-xs sm:text-sm font-semibold">Credits</span></span>
                </div>
                <div className="pt-2.5 sm:pt-3 border-t space-y-1" style={{ borderColor: 'var(--border-primary)' }}>
                  {imageDimensions && (
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                      Resolution: <span className="font-medium">{imageDimensions.width}×{imageDimensions.height}px</span>
                    </p>
                  )}
                  {garmentImages.length > 0 && (
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                      <span className="font-medium">{1 + garmentImages.length}</span> image{1 + garmentImages.length !== 1 ? 's' : ''} total
                    </p>
                  )}
                </div>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={!modelImage || garmentImages.length === 0 || isGenerating}
                className="w-full py-3 sm:py-3.5 text-sm sm:text-base font-semibold shadow-md hover:shadow-lg transition-shadow"
                variant="primary"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center gap-2">
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
                  <span className="flex items-center justify-center gap-2">
                    <HiSparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Generate (~{estimatedCredits} Credits)</span>
                  </span>
                )}
              </Button>

              {/* Error Message */}
              {error && (
                <div className="bg-[var(--bg-tertiary)] border border-red-500/30 text-[var(--text-primary)] px-4 py-3 rounded-lg shadow-sm">
                  <p className="text-xs sm:text-sm font-medium">{error}</p>
                </div>
              )}
            </div>

            {/* Right Panel - Image Output */}
            <div>
              <Card className="h-full !p-5 sm:!p-6">
                <CardHeader className="!mb-4 !pb-0">
                  <CardTitle className="!text-base sm:!text-lg font-semibold">Generated Image</CardTitle>
                </CardHeader>
                <CardContent className="!pt-4">
                  <div className="w-full min-h-[400px] sm:min-h-[500px] lg:min-h-[600px] flex flex-col items-center justify-center gap-5 sm:gap-6">
                    {resultImage ? (
                      <>
                        <div className="relative w-full aspect-square rounded-xl overflow-hidden border-2 shadow-md" style={{ borderColor: 'var(--border-primary)' }}>
                          <img
                            src={resultImage}
                            alt="Try-on result"
                            className="w-full h-full object-contain"
                            style={{ backgroundColor: 'var(--bg-tertiary)' }}
                          />
                        </div>
                        <Button
                          onClick={() => setIsModalOpen(true)}
                          variant="outline"
                          className="flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-medium"
                        >
                          <HiMagnifyingGlass className="w-4 h-4 sm:w-5 sm:h-5" />
                          <span>Preview & Compare</span>
                        </Button>
                      </>
                    ) : (
                      <div className="text-center px-4">
                        <div className="w-24 h-24 sm:w-28 sm:h-28 mx-auto mb-4 sm:mb-5 rounded-xl image-placeholder flex items-center justify-center" style={{ backgroundColor: 'var(--bg-tertiary)', boxShadow: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)' }}>
                          <HiPhoto className="w-12 h-12 sm:w-14 sm:h-14" style={{ color: 'var(--text-tertiary)' }} />
                        </div>
                        <p className="text-base sm:text-lg font-semibold mb-1.5 sm:mb-2" style={{ color: 'var(--text-primary)' }}>No Image Generated</p>
                        <p className="text-xs sm:text-sm max-w-sm mx-auto" style={{ color: 'var(--text-secondary)' }}>Generated image will appear here after completion</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>

      {/* Comparison Modal */}
      {isModalOpen && resultImage && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setIsModalOpen(false)}
        >
          <div 
            className="relative rounded-lg shadow-xl max-w-7xl w-full mx-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            style={{ backgroundColor: 'var(--card-bg)', boxShadow: 'var(--shadow-md)' }}
          >
            {/* Modal Header */}
            <div className="sticky top-0 border-b px-4 sm:px-6 lg:px-8 py-3.5 sm:py-4 flex items-center justify-between z-10" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-primary)' }}>
              <h2 className="text-lg sm:text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>Image Comparison</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 sm:p-2 rounded-lg transition-colors"
                style={{ color: 'var(--text-secondary)' }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-secondary)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                aria-label="Close modal"
              >
                <HiXMark className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 sm:p-6 lg:p-8">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
                {/* Model Image */}
                <div className="space-y-2.5 sm:space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                    Model Image
                  </h3>
                  {modelPreviewUrl ? (
                    <div className="relative w-full aspect-square rounded-xl overflow-hidden border-2 shadow-sm" style={{ borderColor: 'var(--border-primary)', backgroundColor: 'var(--bg-tertiary)' }}>
                      <img
                        src={modelPreviewUrl}
                        alt="Model"
                        className="w-full h-full object-contain"
                      />
                    </div>
                  ) : (
                    <div className="w-full aspect-square rounded-xl border-2 border-dashed flex items-center justify-center" style={{ borderColor: 'var(--border-secondary)', backgroundColor: 'var(--bg-tertiary)' }}>
                      <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>No model image</p>
                    </div>
                  )}
                </div>

                {/* Garment Images */}
                <div className="space-y-2.5 sm:space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                    Garment Images ({garmentPreviewUrls.length})
                  </h3>
                  {garmentPreviewUrls.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2.5 sm:gap-3">
                      {garmentPreviewUrls.map((url, index) => (
                        <div
                          key={index}
                          className="relative aspect-square rounded-xl overflow-hidden border-2 shadow-sm"
                          style={{ borderColor: 'var(--border-primary)', backgroundColor: 'var(--bg-tertiary)' }}
                        >
                          <img
                            src={url}
                            alt={`Garment ${index + 1}`}
                            className="w-full h-full object-contain"
                          />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="w-full aspect-square rounded-xl border-2 border-dashed flex items-center justify-center" style={{ borderColor: 'var(--border-secondary)', backgroundColor: 'var(--bg-tertiary)' }}>
                      <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>No garment images</p>
                    </div>
                  )}
                </div>

                {/* Generated Result */}
                <div className="space-y-2.5 sm:space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Generated Result</h3>
                  <div className="relative w-full aspect-square rounded-xl overflow-hidden border-2 shadow-md" style={{ borderColor: 'var(--primary-500)', backgroundColor: 'var(--bg-tertiary)' }}>
                    <img
                      src={resultImage}
                      alt="Try-on result"
                      className="w-full h-full object-contain"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

