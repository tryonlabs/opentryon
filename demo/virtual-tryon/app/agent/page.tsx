'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MultiImageUpload } from '@/components/multi-image-upload'
import { ImageUpload } from '@/components/image-upload'
import { 
  HiSparkles, 
  HiPhoto, 
  HiUser, 
  HiShoppingBag, 
  HiCog6Tooth,
  HiArrowPath,
  HiCamera,
  HiPaintBrush,
  HiGlobeAlt,
  HiLightBulb,
  HiChatBubbleLeftRight,
  HiPaperAirplane,
  HiXMark,
  HiCheckCircle,
  HiClock
} from 'react-icons/hi2'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type UseCase = 'single-garment' | 'full-outfit' | 'generate-model' | 'multiple-poses' | 'custom'
type AgentMessage = {
  id: string
  type: 'agent' | 'user' | 'system'
  content: string
  timestamp: Date
  suggestions?: string[]
  attachments?: { type: string; url: string }[]
}

interface GarmentImage {
  file: File
  type: string
  preview: string
}

export default function AgentPage() {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: '1',
      type: 'agent',
      content: "Hi! I'm your Try-On AI Agent. I can help you with multiple virtual try-on scenarios. What would you like to do today?",
      timestamp: new Date(),
      suggestions: [
        'Try on a single garment',
        'Create a full outfit',
        'Generate a new model',
        'Try multiple poses & scenes'
      ]
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [activeUseCase, setActiveUseCase] = useState<UseCase | null>(null)
  const [garmentImages, setGarmentImages] = useState<GarmentImage[]>([])
  const [modelImage, setModelImage] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [resultImages, setResultImages] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const useCases = [
    {
      id: 'single-garment' as UseCase,
      title: 'Single Garment Try-On',
      description: 'Try on one garment item on a model',
      icon: <HiShoppingBag className="w-6 h-6" />,
      color: 'bg-blue-50 text-blue-600 border-blue-200'
    },
    {
      id: 'full-outfit' as UseCase,
      title: 'Full Outfit Try-On',
      description: 'Combine multiple garments into a complete outfit',
      icon: <HiUser className="w-6 h-6" />,
      color: 'bg-purple-50 text-purple-600 border-purple-200'
    },
    {
      id: 'generate-model' as UseCase,
      title: 'Generate Model & Try-On',
      description: 'Create a new AI model and try garments on it',
      icon: <HiSparkles className="w-6 h-6" />,
      color: 'bg-pink-50 text-pink-600 border-pink-200'
    },
    {
      id: 'multiple-poses' as UseCase,
      title: 'Multiple Poses & Scenes',
      description: 'Generate try-on results in various poses and settings',
      icon: <HiCamera className="w-6 h-6" />,
      color: 'bg-green-50 text-green-600 border-green-200'
    },
    {
      id: 'custom' as UseCase,
      title: 'Custom Workflow',
      description: 'Build your own try-on workflow',
      icon: <HiLightBulb className="w-6 h-6" />,
      color: 'bg-orange-50 text-orange-600 border-orange-200'
    }
  ]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = (type: 'agent' | 'user' | 'system', content: string, suggestions?: string[]) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      suggestions
    }])
  }

  const handleUseCaseSelect = (useCase: UseCase) => {
    setActiveUseCase(useCase)
    let response = ''
    let suggestions: string[] = []

    switch (useCase) {
      case 'single-garment':
        response = "Great! Let's try on a single garment. Please upload:\n1. A garment image (flatlay or worn by person)\n2. Optionally, a model image (or I can generate one for you)"
        suggestions = ['Upload garment', 'Generate model', 'Use existing model']
        break
      case 'full-outfit':
        response = "Perfect! For a full outfit, I'll need:\n1. Multiple garment images (top, bottom, accessories, etc.)\n2. A model image (optional - I can create one)"
        suggestions = ['Upload garments', 'Select model', 'Start generation']
        break
      case 'generate-model':
        response = "Excellent choice! I'll help you:\n1. Generate a new fashion model based on your description\n2. Try garments on the generated model\n\nDescribe your ideal model (age, appearance, style, etc.)"
        suggestions = ['Describe model', 'Upload garments', 'Generate']
        break
      case 'multiple-poses':
        response = "Awesome! I can generate try-on results in multiple poses and scenes. Please:\n1. Upload garment images\n2. Select poses and scenes\n3. Choose number of variations"
        suggestions = ['Upload garments', 'Select poses', 'Choose scenes']
        break
      case 'custom':
        response = "Let's build a custom workflow! Tell me what you'd like to achieve and I'll guide you through it."
        suggestions = ['Describe your goal', 'Upload images', 'Configure settings']
        break
    }

    addMessage('user', `I want to use: ${useCases.find(uc => uc.id === useCase)?.title}`)
    setTimeout(() => {
      addMessage('agent', response, suggestions)
    }, 500)
  }

  const handleSuggestionClick = (suggestion: string) => {
    addMessage('user', suggestion)
    setInputMessage('')
    
    // Simulate agent response
    setTimeout(() => {
      if (suggestion.includes('Upload')) {
        addMessage('agent', 'Please drag and drop your images in the workspace area on the right, or click to browse.', ['Continue', 'Need help?'])
      } else if (suggestion.includes('Generate')) {
        addMessage('agent', 'I\'ll start generating now. This may take a few moments...', [])
        setIsProcessing(true)
        // Simulate processing
        setTimeout(() => {
          setIsProcessing(false)
          addMessage('agent', 'Generation complete! Check the results in the workspace.', ['Generate more', 'Try different settings'])
        }, 3000)
      } else if (suggestion.includes('Describe')) {
        addMessage('agent', 'Please describe your model in the workspace. I\'ll generate it based on your description.', ['Continue'])
      }
    }, 500)
  }

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return

    addMessage('user', inputMessage)
    setInputMessage('')

    // Simulate agent thinking
    setTimeout(() => {
      addMessage('agent', 'I understand. Let me help you with that. Please use the workspace on the right to upload images or configure settings.', ['Upload images', 'Configure settings', 'Start generation'])
    }, 1000)
  }

  const handleGarmentUpload = (files: File[]) => {
    const newGarments: GarmentImage[] = files.map((file) => ({
      file,
      type: 'garment',
      preview: URL.createObjectURL(file),
    }))
    setGarmentImages([...garmentImages, ...newGarments])
    addMessage('system', `Uploaded ${files.length} garment image(s)`)
    setTimeout(() => {
      addMessage('agent', `Great! I've received ${files.length} garment image(s). ${modelImage ? 'You also have a model image. Ready to generate?' : 'Would you like to upload a model image or should I generate one for you?'}`, modelImage ? ['Generate now', 'Upload model'] : ['Generate model', 'Upload model', 'Generate without model'])
    }, 500)
  }

  const handleModelUpload = (file: File | null) => {
    setModelImage(file)
    if (file) {
      addMessage('system', 'Model image uploaded')
      setTimeout(() => {
        addMessage('agent', 'Perfect! I have both the garments and model. Ready to generate the try-on results?', ['Generate now', 'Configure settings'])
      }, 500)
    }
  }

  return (
    <div className="h-screen bg-neutral-50 flex overflow-hidden" style={{ backgroundColor: '#fafafa' }}>
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-white border-r border-neutral-200 flex flex-col fixed h-full sidebar-shadow" style={{ backgroundColor: '#ffffff', boxShadow: '1px 0 3px 0 rgb(0 0 0 / 0.05)' }}>
        <div className="p-6 border-b border-neutral-200" style={{ borderColor: '#e5e5e5' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-sm">
              <HiSparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-neutral-900">TryOn AI</h1>
              <p className="text-xs text-neutral-500">Playground</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          <Link href="/" className="sidebar-link">
            <HiUser className="w-5 h-5" />
            <span>Virtual Try-On</span>
          </Link>
          <Link href="/agent" className="sidebar-link sidebar-link-active">
            <HiChatBubbleLeftRight className="w-5 h-5" />
            <span>Try-On Agent</span>
          </Link>
          <a href="#" className="sidebar-link">
            <HiPhoto className="w-5 h-5" />
            <span>My Gallery</span>
          </a>
          <a href="#" className="sidebar-link">
            <HiShoppingBag className="w-5 h-5" />
            <span>Model Generator</span>
          </a>
        </nav>

        <div className="p-4 border-t border-neutral-200" style={{ borderColor: '#e5e5e5' }}>
          <a href="#" className="sidebar-link">
            <HiCog6Tooth className="w-5 h-5" />
            <span>Settings</span>
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="flex-shrink-0 bg-white border-b border-neutral-200 sticky top-0 z-10 header-shadow" style={{ backgroundColor: '#ffffff', borderColor: '#e5e5e5', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)' }}>
          <div className="px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-neutral-900">Try-On AI Agent</h1>
                <p className="text-sm text-neutral-500 mt-1">Conversational AI assistant for virtual try-on workflows</p>
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 rounded-lg border border-yellow-200 shadow-sm" style={{ backgroundColor: '#fefce8', borderColor: '#fde047', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}>
                  <span className="text-sm font-medium text-yellow-800">394</span>
                  <span className="text-xs text-yellow-600">Credits</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-neutral-200 flex items-center justify-center shadow-sm" style={{ backgroundColor: '#e5e5e5', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}>
                    <HiUser className="w-5 h-5 text-neutral-600" />
                  </div>
                  <span className="text-sm font-medium text-neutral-700">tryondemo</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area - Split View */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* Left Panel - Chat Interface */}
          <div className="w-1/2 border-r border-neutral-200 flex flex-col h-full" style={{ borderColor: '#e5e5e5' }}>
            {/* Use Cases Quick Access */}
            {!activeUseCase && (
              <div className="flex-shrink-0 p-4 border-b border-neutral-200 bg-neutral-50" style={{ borderColor: '#e5e5e5', backgroundColor: '#fafafa' }}>
                <h3 className="text-sm font-semibold text-neutral-700 mb-3">Quick Start - Choose a Use Case:</h3>
                <div className="grid grid-cols-2 gap-2">
                  {useCases.map((useCase) => (
                    <button
                      key={useCase.id}
                      onClick={() => handleUseCaseSelect(useCase.id)}
                      className={`p-3 rounded-lg border-2 text-left transition-all hover:shadow-md ${useCase.color}`}
                      style={{ boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                    >
                      <div className="flex items-start gap-2">
                        {useCase.icon}
                        <div className="flex-1">
                          <div className="font-medium text-sm">{useCase.title}</div>
                          <div className="text-xs opacity-75 mt-1">{useCase.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-white min-h-0">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type === 'agent' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center flex-shrink-0 shadow-sm">
                      <HiSparkles className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div className={`flex flex-col max-w-[80%] ${message.type === 'user' ? 'items-end' : 'items-start'}`}>
                    <div
                      className={`rounded-lg px-4 py-2 ${
                        message.type === 'user'
                          ? 'bg-primary-500 text-white'
                          : message.type === 'system'
                          ? 'bg-neutral-100 text-neutral-600 text-sm'
                          : 'bg-neutral-100 text-neutral-900'
                      }`}
                      style={
                        message.type === 'user'
                          ? { boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                          : { boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }
                      }
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {message.suggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="text-xs px-3 py-1.5 bg-white border border-neutral-300 rounded-full hover:bg-primary-50 hover:border-primary-300 hover:text-primary-600 transition-all"
                            style={{ boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                    <span className="text-xs text-neutral-400 mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  {message.type === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-neutral-200 flex items-center justify-center flex-shrink-0">
                      <HiUser className="w-4 h-4 text-neutral-600" />
                    </div>
                  )}
                </div>
              ))}
              {isProcessing && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center flex-shrink-0 shadow-sm">
                    <HiSparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-neutral-100 rounded-lg px-4 py-2">
                    <div className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4 text-primary-500" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="text-sm text-neutral-600">Processing...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className="flex-shrink-0 p-4 border-t border-neutral-200 bg-white" style={{ borderColor: '#e5e5e5' }}>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type your message or ask a question..."
                  className="flex-1 px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  style={{ backgroundColor: '#ffffff', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim()}
                  variant="primary"
                  className="px-4"
                >
                  <HiPaperAirplane className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </div>

          {/* Right Panel - Workspace */}
          <div className="w-1/2 overflow-y-auto bg-neutral-50" style={{ backgroundColor: '#fafafa' }}>
            <div className="p-6 space-y-6">
              {/* Active Use Case Badge */}
              {activeUseCase && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-neutral-200 shadow-sm">
                    {useCases.find(uc => uc.id === activeUseCase)?.icon}
                    <span className="text-sm font-medium text-neutral-700">
                      {useCases.find(uc => uc.id === activeUseCase)?.title}
                    </span>
                  </div>
                  <button
                    onClick={() => {
                      setActiveUseCase(null)
                      setGarmentImages([])
                      setModelImage(null)
                      setResultImages([])
                    }}
                    className="text-sm text-neutral-500 hover:text-neutral-700"
                  >
                    Clear
                  </button>
                </div>
              )}

              {/* Garment Upload Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HiShoppingBag className="w-5 h-5" />
                    <span>Garments</span>
                    {garmentImages.length > 0 && (
                      <span className="ml-auto text-sm font-normal text-primary-600">
                        {garmentImages.length} uploaded
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {garmentImages.length > 0 && (
                    <div className="grid grid-cols-3 gap-3 mb-4">
                      {garmentImages.map((garment, index) => (
                        <div
                          key={index}
                          className="relative aspect-square rounded-lg overflow-hidden border-2 group"
                          style={{ 
                            borderColor: '#e5e5e5',
                            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
                          }}
                        >
                          <img
                            src={garment.preview}
                            alt={`Garment ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                          <button
                            onClick={() => {
                              URL.revokeObjectURL(garment.preview)
                              setGarmentImages(garmentImages.filter((_, i) => i !== index))
                            }}
                            className="absolute top-2 right-2 bg-primary-500 text-white rounded-full p-1 hover:bg-primary-600 transition-all opacity-0 group-hover:opacity-100"
                            style={{ boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                          >
                            <HiXMark className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <MultiImageUpload
                    label=""
                    description=""
                    onImagesChange={handleGarmentUpload}
                    currentImages={garmentImages.map(g => g.file)}
                    maxFiles={10}
                    categories={['Top', 'Jeans', 'Hat', 'Glasses', 'Shoes', 'Jacket', 'Scarf', 'Dress']}
                    layout="grid"
                    gridCols={3}
                  />
                </CardContent>
              </Card>

              {/* Model Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HiUser className="w-5 h-5" />
                    <span>Model</span>
                    {modelImage && (
                      <span className="ml-auto text-sm font-normal text-primary-600 flex items-center gap-1">
                        <HiCheckCircle className="w-4 h-4" />
                        Ready
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ImageUpload
                    label=""
                    description=""
                    onImageChange={handleModelUpload}
                    currentImage={modelImage}
                    layout="grid"
                    gridCols={3}
                  />
                </CardContent>
              </Card>

              {/* Results Section */}
              {resultImages.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HiPhoto className="w-5 h-5" />
                      <span>Results</span>
                      <span className="ml-auto text-sm font-normal text-neutral-500">
                        {resultImages.length} generated
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      {resultImages.map((image, index) => (
                        <div
                          key={index}
                          className="relative aspect-square rounded-lg overflow-hidden border-2"
                          style={{ 
                            borderColor: '#e5e5e5',
                            boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
                          }}
                        >
                          <img
                            src={image}
                            alt={`Result ${index + 1}`}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
