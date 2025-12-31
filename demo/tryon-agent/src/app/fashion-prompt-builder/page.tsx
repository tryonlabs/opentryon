'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs'
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Input, Textarea, Select } from '../../components/ui/input'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../../components/ui/accordion'
import { HiSparkles, HiPhoto, HiPencil } from 'react-icons/hi2'
import { Toast } from '../../components/ui/toast'
import { useTheme } from '../../components/ThemeProvider'

interface Template {
  name: string
  description: string
  template: string
}

interface TemplatesData {
  [key: string]: Template[]
}

export default function FashionPromptBuilderPage() {
  const { theme } = useTheme()
  const [templatesData, setTemplatesData] = useState<TemplatesData>({})
  const [models, setModels] = useState<string[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [templates, setTemplates] = useState<Template[]>([])
  const [parameters, setParameters] = useState<Record<string, string>>({})
  const [generatedPrompt, setGeneratedPrompt] = useState<string>('')
  const [status, setStatus] = useState<{ type: 'success' | 'warning' | 'error'; message: string } | null>(null)
  const [galleryPrompts, setGalleryPrompts] = useState<string[]>([])
  const [selectedGalleryPrompt, setSelectedGalleryPrompt] = useState<string>('')
  const [rawPrompt, setRawPrompt] = useState<string>('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'warning' | 'error'; isVisible: boolean }>({
    message: '',
    type: 'success',
    isVisible: false,
  })

  useEffect(() => {
    // Load templates
    fetch('/prompt_templates.json')
      .then((res) => res.json())
      .then((data) => {
        setTemplatesData(data)
        const modelKeys = Object.keys(data)
        setModels(modelKeys)
        if (modelKeys.length > 0) {
          setSelectedModel(modelKeys[0])
          setTemplates(data[modelKeys[0]])
        }
      })
      .catch(console.error)

    // Load gallery prompts
    fetch('/prompts.json')
      .then((res) => res.json())
      .then((data) => {
        let promptsList: any[] = []
        if (data.fashion_model_prompts) {
          promptsList = data.fashion_model_prompts
        } else if (Array.isArray(data)) {
          promptsList = data
        } else if (typeof data === 'object') {
          Object.values(data).forEach((value: any) => {
            if (Array.isArray(value)) {
              promptsList.push(...value)
            }
          })
        }
        const prompts = promptsList
          .map((p) => p.prompt)
          .filter(Boolean)
          .slice(0, 15)
        setGalleryPrompts(prompts)
      })
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (selectedModel && templatesData[selectedModel]) {
      const newTemplates = templatesData[selectedModel]
      setTemplates(newTemplates)
      // Always reset to first template when model changes
      if (newTemplates.length > 0) {
        setSelectedTemplate(newTemplates[0].name)
        // Clear parameters when switching models since they might not be relevant
        setParameters({})
        setGeneratedPrompt('')
        setStatus(null)
      }
    }
  }, [selectedModel, templatesData])

  const extractPlaceholders = (templateStr: string): string[] => {
    const matches = templateStr.match(/\{(\w+)\}/g)
    return matches ? matches.map((m) => m.slice(1, -1)) : []
  }

  const generatePrompt = () => {
    if (!selectedModel || !selectedTemplate) {
      setStatus({ type: 'warning', message: 'Please select a model and template.' })
      return
    }

    const template = templates.find((t) => t.name === selectedTemplate)
    if (!template) {
      setStatus({ type: 'error', message: 'Template not found.' })
      return
    }

    const placeholders = extractPlaceholders(template.template)
    let prompt = template.template
    const missing: string[] = []

    placeholders.forEach((placeholder) => {
      const value = parameters[placeholder]
      if (value) {
        prompt = prompt.replace(`{${placeholder}}`, value)
      } else {
        missing.push(placeholder)
      }
    })

    setGeneratedPrompt(prompt)
    if (missing.length > 0) {
      setStatus({
        type: 'warning',
        message: `Missing parameters: ${missing.join(', ')}`,
      })
    } else {
      setStatus({ type: 'success', message: 'Prompt generated successfully!' })
    }
  }

  const usePrompt = (prompt: string) => {
    if (!prompt.trim()) {
      setToast({
        message: 'Please generate a prompt first before using it.',
        type: 'warning',
        isVisible: true,
      })
      return
    }
    // Here you would typically send the prompt to your backend API
    setToast({
      message: 'Prompt ready to use! You can now copy it or send it to the API.',
      type: 'success',
      isVisible: true,
    })
    console.log('Final prompt:', prompt)
  }

  const showToast = (message: string, type: 'success' | 'warning' | 'error' = 'success') => {
    setToast({ message, type, isVisible: true })
  }

  const hideToast = () => {
    setToast((prev) => ({ ...prev, isVisible: false }))
  }

  const currentTemplate = templates.find((t) => t.name === selectedTemplate)
  const placeholders = currentTemplate ? extractPlaceholders(currentTemplate.template) : []

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'transparent' }}>
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-12 text-center">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold mb-4">
            <span className="bg-gradient-to-r from-primary-400 via-secondary-500 to-primary-400 bg-clip-text text-transparent">
              Fashion Model Prompt Builder
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-neutral-600 max-w-2xl mx-auto leading-relaxed">
            Create stunning fashion model prompts with our intuitive builder. 
            <span className="text-primary-400 font-semibold"> Choose your preferred method</span> to craft the perfect prompt for AI-generated fashion imagery.
          </p>
        </div>

        <Tabs defaultValue="builder">
          <div className="flex justify-center mb-6 px-2">
            <TabsList className="w-full max-w-2xl">
              <TabsTrigger value="builder" className="flex-1 min-w-0">
                <HiSparkles className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
                <span className="truncate text-xs sm:text-sm">Prompt Builder</span>
              </TabsTrigger>
              <TabsTrigger value="gallery" className="flex-1 min-w-0">
                <HiPhoto className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
                <span className="truncate text-xs sm:text-sm">Prompt Gallery</span>
              </TabsTrigger>
              <TabsTrigger value="raw" className="flex-1 min-w-0">
                <HiPencil className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
                <span className="truncate text-xs sm:text-sm">Raw Prompt</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="builder">
            <div className="space-y-6 mt-6">
              {/* Step 1: Template Selection */}
              <Card>
                <CardHeader>
                  <CardTitle>Step 1: Choose Template</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <label className={`block text-sm font-medium mb-2 ${
                        theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                      }`}>
                        Model
                      </label>
                      <Select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                      >
                        {models.map((model) => (
                          <option key={model} value={model}>
                            {model==="nano_banana" ? "Google Nano Banana" : model==="flux1_kontext_pro"? "Flux.1-Kontext Pro" : model}
                          </option>
                        ))}
                      </Select>
                    </div>
                    <div className="md:col-span-2">
                      <label className={`block text-sm font-medium mb-2 ${
                        theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                      }`}>
                        Template Style
                      </label>
                      <Select
                        value={selectedTemplate}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                      >
                        {templates.map((template) => (
                          <option key={template.name} value={template.name}>
                            {template.name}
                          </option>
                        ))}
                      </Select>
                    </div>
                  </div>
                  {currentTemplate && (
                    <div className="bg-gradient-to-r from-primary-50 to-white p-4 rounded-lg border-l-4 border-primary-400">
                      <p className={theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'}>
                        {currentTemplate.description}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Step 2: Parameters */}
              <Accordion defaultValue="">
                <AccordionItem value="params">
                  <AccordionTrigger isOpen={false} value="params">
                    <span className="flex items-center gap-2">
                      <span>Step 2: Fill Parameters</span>
                    </span>
                  </AccordionTrigger>
                  <AccordionContent isOpen={false}>
                    <div className="space-y-6 pt-2">
                      {/* Basic Information Group */}
                      {(placeholders.includes('age') || placeholders.includes('gender')) && (
                        <div className="bg-gradient-to-br from-primary-50 to-white rounded-xl p-5 border border-primary-100">
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-8 h-8 rounded-lg bg-primary-400 flex items-center justify-center text-white font-semibold">
                              1
                            </div>
                            <h4 className={`text-base font-semibold ${
                              theme === 'dark' ? 'text-white' : 'text-neutral-900'
                            }`}>Basic Information</h4>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {placeholders.includes('age') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Age <span className="text-primary-400">*</span>
                                </label>
                                <Input
                                  type="number"
                                  min={18}
                                  max={60}
                                  value={parameters.age || ''}
                                  onChange={(e) =>
                                    setParameters({ ...parameters, age: e.target.value })
                                  }
                                  placeholder="25"
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                />
                              </div>
                            )}
                            {placeholders.includes('gender') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Gender <span className="text-primary-400">*</span>
                                </label>
                                <Select
                                  value={parameters.gender || ''}
                                  onChange={(e) =>
                                    setParameters({ ...parameters, gender: e.target.value })
                                  }
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                >
                                  <option value="">Select gender...</option>
                                  <option value="male">Male</option>
                                  <option value="female">Female</option>
                                </Select>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Appearance Group */}
                      {placeholders.some((p) =>
                        ['complexion', 'hair_color', 'hair_type', 'eye_color', 'face_shape'].includes(p)
                      ) && (
                        <div className="bg-gradient-to-br from-secondary-50 to-white rounded-xl p-5 border border-secondary-100">
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-8 h-8 rounded-lg bg-secondary-500 flex items-center justify-center text-white font-semibold">
                              2
                            </div>
                            <h4 className="text-base font-semibold text-neutral-900">Appearance</h4>
                          </div>
                          <div className="space-y-4">
                            {placeholders.includes('complexion') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Complexion <span className="text-primary-400">*</span>
                                </label>
                                <Select
                                  value={parameters.complexion || ''}
                                  onChange={(e) =>
                                    setParameters({ ...parameters, complexion: e.target.value })
                                  }
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                >
                                  <option value="">Select complexion...</option>
                                  <option value="fair">Fair</option>
                                  <option value="olive">Olive</option>
                                  <option value="tan">Tan</option>
                                  <option value="medium brown">Medium Brown</option>
                                  <option value="deep brown">Deep Brown</option>
                                  <option value="pale">Pale</option>
                                  <option value="wheatish">Wheatish</option>
                                </Select>
                              </div>
                            )}

                            {placeholders.some((p) => ['hair_color', 'hair_type'].includes(p)) && (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {placeholders.includes('hair_color') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Hair Color <span className="text-primary-400">*</span>
                                    </label>
                                    <Select
                                      value={parameters.hair_color || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, hair_color: e.target.value })
                                      }
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    >
                                      <option value="">Select color...</option>
                                      <option value="blonde">Blonde</option>
                                      <option value="brown">Brown</option>
                                      <option value="black">Black</option>
                                      <option value="red">Red</option>
                                      <option value="gray">Gray</option>
                                      <option value="salt and pepper">Salt and Pepper</option>
                                    </Select>
                                  </div>
                                )}
                                {placeholders.includes('hair_type') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Hair Type <span className="text-primary-400">*</span>
                                    </label>
                                    <Select
                                      value={parameters.hair_type || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, hair_type: e.target.value })
                                      }
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    >
                                      <option value="">Select style...</option>
                                      <option value="long straight">Long Straight</option>
                                      <option value="short curly">Short Curly</option>
                                      <option value="shoulder-length wavy">Shoulder-length Wavy</option>
                                      <option value="buzz-cut">Buzz-cut</option>
                                      <option value="tied back">Tied Back</option>
                                      <option value="short">Short</option>
                                      <option value="wavy">Wavy</option>
                                    </Select>
                                  </div>
                                )}
                              </div>
                            )}

                            {placeholders.some((p) => ['eye_color', 'face_shape'].includes(p)) && (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {placeholders.includes('eye_color') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Eye Color <span className="text-primary-400">*</span>
                                    </label>
                                    <Select
                                      value={parameters.eye_color || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, eye_color: e.target.value })
                                      }
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    >
                                      <option value="">Select color...</option>
                                      <option value="blue">Blue</option>
                                      <option value="green">Green</option>
                                      <option value="brown">Brown</option>
                                      <option value="gray">Gray</option>
                                      <option value="dark brown">Dark Brown</option>
                                    </Select>
                                  </div>
                                )}
                                {placeholders.includes('face_shape') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Face Shape <span className="text-primary-400">*</span>
                                    </label>
                                    <Select
                                      value={parameters.face_shape || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, face_shape: e.target.value })
                                      }
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    >
                                      <option value="">Select shape...</option>
                                      <option value="oval">Oval</option>
                                      <option value="round">Round</option>
                                      <option value="sharp jawline">Sharp Jawline</option>
                                      <option value="heart-shaped">Heart-shaped</option>
                                      <option value="angular">Angular</option>
                                      <option value="classic masculine">Classic Masculine</option>
                                    </Select>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Styling Group */}
                      {(placeholders.includes('pose') || placeholders.includes('outfit')) && (
                        <div className="bg-gradient-to-br from-neutral-50 to-white rounded-xl p-5 border border-neutral-200">
                          <div className="flex items-center gap-2 mb-4">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white font-semibold ${
                              theme === 'dark' ? 'bg-gray-700' : 'bg-neutral-600'
                            }`}>
                              3
                            </div>
                            <h4 className="text-base font-semibold text-neutral-900">Pose & Styling</h4>
                          </div>
                          <div className="space-y-4">
                            {placeholders.includes('pose') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Pose <span className="text-primary-400">*</span>
                                </label>
                                <Input
                                  value={parameters.pose || ''}
                                  onChange={(e) =>
                                    setParameters({ ...parameters, pose: e.target.value })
                                  }
                                  placeholder="e.g., smiling softly front-facing, standing confidently"
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                />
                                <p className={`text-xs mt-1 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
                                }`}>
                                  Describe the model's pose and expression
                                </p>
                              </div>
                            )}
                            {placeholders.includes('outfit') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Outfit <span className="text-primary-400">*</span>
                                </label>
                                <Input
                                  value={parameters.outfit || ''}
                                  onChange={(e) =>
                                    setParameters({ ...parameters, outfit: e.target.value })
                                  }
                                  placeholder="e.g., floral summer dress, tailored suit, casual jeans and t-shirt"
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                />
                                <p className={`text-xs mt-1 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
                                }`}>
                                  Describe the clothing and style
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Scene Settings Group */}
                      {placeholders.some((p) =>
                        ['lighting', 'background', 'fabric_description'].includes(p)
                      ) && (
                        <div className="bg-gradient-to-br from-primary-50/50 to-white rounded-xl p-5 border border-primary-100">
                          <div className="flex items-center gap-2 mb-4">
                            <div className="w-8 h-8 rounded-lg bg-primary-400 flex items-center justify-center text-white font-semibold">
                              4
                            </div>
                            <h4 className="text-base font-semibold text-neutral-900">Scene Settings</h4>
                          </div>
                          <div className="space-y-4">
                            {placeholders.some((p) => ['lighting', 'background'].includes(p)) && (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {placeholders.includes('lighting') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Lighting <span className="text-primary-400">*</span>
                                    </label>
                                    <Select
                                      value={parameters.lighting || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, lighting: e.target.value })
                                      }
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    >
                                      <option value="">Select lighting...</option>
                                      <option value="daylight outdoors">Daylight Outdoors</option>
                                      <option value="studio lighting">Studio Lighting</option>
                                      <option value="cinematic lighting">Cinematic Lighting</option>
                                      <option value="soft natural lighting">Soft Natural Lighting</option>
                                    </Select>
                                  </div>
                                )}
                                {placeholders.includes('background') && (
                                  <div>
                                    <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                      Background <span className="text-primary-400">*</span>
                                    </label>
                                    <Input
                                      value={parameters.background || ''}
                                      onChange={(e) =>
                                        setParameters({ ...parameters, background: e.target.value })
                                      }
                                      placeholder="e.g., garden, studio backdrop, urban cityscape"
                                      className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                    />
                                  </div>
                                )}
                              </div>
                            )}
                            {placeholders.includes('fabric_description') && (
                              <div>
                                <label className={`block text-sm font-semibold mb-2 ${
                                  theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  Fabric Description
                                  <span className={`text-xs font-normal ml-2 ${
                                    theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
                                  }`}>(optional)</span>
                                </label>
                                <Input
                                  value={parameters.fabric_description || ''}
                                  onChange={(e) =>
                                    setParameters({
                                      ...parameters,
                                      fabric_description: e.target.value,
                                    })
                                  }
                                  placeholder="e.g., silk, cotton, leather, denim"
                                  className={theme === 'dark' ? 'bg-gray-800' : 'bg-white'}
                                />
                                <p className={`text-xs mt-1 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-neutral-500'
                                }`}>
                                  Add fabric details for better texture rendering
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              {/* Step 3: Generate & Preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Step 3: Generate & Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4 mb-4">
                    <Button onClick={generatePrompt} className="flex-1">
                      Generate Prompt
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setParameters({})
                        setGeneratedPrompt('')
                        setStatus(null)
                      }}
                    >
                      Clear
                    </Button>
                  </div>

                  <div className="mb-4">
                    <label className={`block text-sm font-medium mb-2 ${
                      theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                    }`}>
                      Generated Prompt
                    </label>
                    <Textarea
                      rows={8}
                      value={generatedPrompt}
                      onChange={(e) => setGeneratedPrompt(e.target.value)}
                      placeholder="Your generated prompt will appear here..."
                      className="font-mono text-sm"
                    />
                  </div>

                  {status && (
                    <div
                      className={`p-3 rounded-lg mb-4 ${
                        status.type === 'success'
                          ? 'bg-green-50 text-green-700'
                          : status.type === 'warning'
                          ? 'bg-yellow-50 text-yellow-700'
                          : 'bg-red-50 text-red-700'
                      }`}
                    >
                      {status.message}
                    </div>
                  )}

                  <Button
                    onClick={() => {
                      if (!generatedPrompt.trim()) {
                        showToast('Please generate a prompt first by clicking "Generate Prompt" button.', 'warning')
                      } else {
                        usePrompt(generatedPrompt)
                      }
                    }}
                    className="w-full"
                  >
                    Use This Prompt
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="gallery">
            <div className="mt-6 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HiPhoto className="w-5 h-5 text-primary-400" />
                    Browse Example Prompts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-primary-50 to-secondary-50 p-4 rounded-lg border border-primary-100 mb-6">
                    <p className={`text-sm ${
                      theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                    }`}>
                      <span className="font-semibold text-primary-400">💡 Tip:</span> Click on any example below to load it into the editor. You can then edit it or use it directly.
                    </p>
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-neutral-700 mb-2">
                      Selected Prompt Preview
                    </label>
                    <div className="relative">
                      <Textarea
                        rows={8}
                        value={selectedGalleryPrompt}
                        onChange={(e) => setSelectedGalleryPrompt(e.target.value)}
                        placeholder="Click an example below to load it here..."
                        className={`font-mono text-sm border-2 focus:border-primary-400 transition-colors ${
                          theme === 'dark'
                            ? 'bg-gray-800 border-gray-700 text-white'
                            : 'bg-white border-neutral-200'
                        }`}
                      />
                      {selectedGalleryPrompt && (
                        <div className="absolute top-2 right-2">
                          <span className="text-xs bg-primary-400 text-white px-2 py-1 rounded-full font-medium">
                            {selectedGalleryPrompt.split(' ').length} words
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-base font-semibold text-neutral-900">
                        Example Prompts
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        theme === 'dark'
                          ? 'text-gray-300 bg-gray-800'
                          : 'text-neutral-500 bg-neutral-100'
                      }`}>
                        {galleryPrompts.length} examples
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[500px] overflow-y-auto pr-2">
                      {galleryPrompts.map((prompt, idx) => {
                        const isSelected = selectedGalleryPrompt === prompt
                        return (
                          <button
                            key={idx}
                            onClick={() => setSelectedGalleryPrompt(prompt)}
                            className={`group relative text-left p-4 rounded-xl border-2 transition-all duration-200 ${
                              isSelected
                                ? 'border-primary-400 bg-gradient-to-br from-primary-50 to-white shadow-md shadow-primary-400/20'
                                : 'border-neutral-200 bg-white hover:border-primary-300 hover:bg-primary-50/50 hover:shadow-sm'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <div
                                className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                                  isSelected
                                    ? 'bg-primary-400 text-white'
                                    : theme === 'dark'
                                      ? 'bg-gray-800 text-gray-400 group-hover:bg-primary-600 group-hover:text-white'
                                      : 'bg-neutral-100 text-neutral-500 group-hover:bg-primary-100 group-hover:text-primary-400'
                                }`}
                              >
                                {idx + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className={`text-sm leading-relaxed line-clamp-3 ${
                                  isSelected
                                    ? theme === 'dark' ? 'text-white font-medium' : 'text-neutral-900 font-medium'
                                    : theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                                }`}>
                                  {prompt}
                                </p>
                                <div className={`mt-2 flex items-center gap-2 text-xs ${
                                  theme === 'dark' ? 'text-gray-500' : 'text-neutral-400'
                                }`}>
                                  <span>{prompt.split(' ').length} words</span>
                                  <span>•</span>
                                  <span>{prompt.length} chars</span>
                                </div>
                              </div>
                              {isSelected && (
                                <div className="flex-shrink-0">
                                  <div className="w-5 h-5 rounded-full bg-primary-400 flex items-center justify-center">
                                    <span className="text-white text-xs">✓</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-neutral-200">
                    <Button
                      onClick={() => {
                        if (!selectedGalleryPrompt.trim()) {
                          showToast('Please select a prompt from the gallery first.', 'warning')
                        } else {
                          usePrompt(selectedGalleryPrompt)
                        }
                      }}
                      className="w-full"
                    >
                      Use This Prompt
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="raw">
            <div className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HiPencil className="w-5 h-5 text-primary-400" />
                    Write Custom Prompt
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-secondary-50 to-primary-50 p-4 rounded-lg border border-secondary-100 mb-6">
                    <p className={`text-sm ${
                      theme === 'dark' ? 'text-gray-300' : 'text-neutral-700'
                    }`}>
                      <span className="font-semibold text-secondary-600">✍️ Advanced Mode:</span> For users who want full control over their prompts. Write your custom prompt from scratch or edit an existing one.
                    </p>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-semibold text-neutral-700">
                        Custom Prompt Editor
                      </label>
                      {rawPrompt && (
                        <div className="flex items-center gap-3 text-xs text-neutral-500">
                          <span className="bg-neutral-100 px-2 py-1 rounded-full">
                            {rawPrompt.split(' ').length} words
                          </span>
                          <span className="bg-neutral-100 px-2 py-1 rounded-full">
                            {rawPrompt.length} characters
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="relative">
                      <Textarea
                        rows={14}
                        value={rawPrompt}
                        onChange={(e) => setRawPrompt(e.target.value)}
                        placeholder="Enter your custom prompt here...&#10;&#10;Example:&#10;A high-quality realistic photo of a 25-year-old female fashion model with fair skin, long straight blonde hair, blue eyes, and an oval face. The model is smiling softly front-facing, wearing a floral summer dress. Captured in daylight outdoors with a garden background. Ultra-detailed, 8K, cinematic lighting, professional fashion photography."
                        className="font-mono text-sm bg-white border-2 border-neutral-200 focus:border-primary-400 transition-colors resize-y"
                      />
                      {!rawPrompt && (
                        <div className="absolute bottom-4 left-4 text-xs text-neutral-400 pointer-events-none">
                          Start typing your prompt...
                        </div>
                      )}
                    </div>
                    {rawPrompt && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-neutral-500">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-green-400"></span>
                          Prompt ready
                        </span>
                      </div>
                    )}
                  </div>

                  <Accordion defaultValue="">
                    <AccordionItem value="tips">
                      <AccordionTrigger isOpen={false} value="tips">
                        <span className="flex items-center gap-2">
                          <span className="text-lg">💡</span>
                          <span>Tips & Best Practices</span>
                        </span>
                      </AccordionTrigger>
                      <AccordionContent isOpen={false}>
                        <div className="bg-gradient-to-br from-neutral-50 to-white p-5 rounded-lg border border-neutral-200 space-y-4">
                          <div>
                            <p className="font-semibold text-neutral-900 mb-2 flex items-center gap-2">
                              <span className="w-6 h-6 rounded-full bg-primary-400 text-white flex items-center justify-center text-xs">1</span>
                              Best Practices:
                            </p>
                            <ul className="list-disc list-inside space-y-2 ml-8 text-sm text-neutral-700">
                              <li>Be specific about appearance details (age, gender, complexion, hair, eyes)</li>
                              <li>Include lighting and background settings for better results</li>
                              <li>Mention pose and outfit clearly and descriptively</li>
                              <li>Add quality keywords (ultra-detailed, 8K, cinematic, professional)</li>
                              <li>Use commas to separate different aspects of the prompt</li>
                            </ul>
                          </div>
                          
                          <div className="pt-3 border-t border-neutral-200">
                            <p className="font-semibold text-neutral-900 mb-2 flex items-center gap-2">
                              <span className="w-6 h-6 rounded-full bg-secondary-500 text-white flex items-center justify-center text-xs">2</span>
                              Recommended Structure:
                            </p>
                            <ol className="list-decimal list-inside space-y-2 ml-8 text-sm text-neutral-700">
                              <li><strong>Model description:</strong> age, gender, appearance features</li>
                              <li><strong>Outfit details:</strong> clothing, style, colors, accessories</li>
                              <li><strong>Pose and expression:</strong> body position, facial expression</li>
                              <li><strong>Lighting and background:</strong> environment and lighting conditions</li>
                              <li><strong>Quality modifiers:</strong> technical terms for image quality</li>
                            </ol>
                          </div>

                          <div className="pt-3 border-t border-neutral-200">
                            <p className="font-semibold text-neutral-900 mb-2 flex items-center gap-2">
                              <span className="w-6 h-6 rounded-full bg-primary-400 text-white flex items-center justify-center text-xs">3</span>
                              Pro Tips:
                            </p>
                            <ul className="list-disc list-inside space-y-2 ml-8 text-sm text-neutral-700">
                              <li>Longer prompts (50-100 words) often produce better results</li>
                              <li>Use descriptive adjectives to enhance image quality</li>
                              <li>Combine multiple style keywords for unique looks</li>
                              <li>Test different phrasings to find what works best</li>
                            </ul>
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>

                  <div className="mt-6 pt-6 border-t border-neutral-200">
                    <div className="flex flex-col sm:flex-row gap-4">
                      <Button
                        onClick={() => {
                          if (!rawPrompt.trim()) {
                            showToast('Please enter a custom prompt first.', 'warning')
                          } else {
                            usePrompt(rawPrompt)
                          }
                        }}
                        className="flex-1"
                      >
                        Use This Prompt
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => {
                          if (!generatedPrompt.trim()) {
                            showToast('No prompt available from builder. Please generate one first.', 'warning')
                          } else {
                            setRawPrompt(generatedPrompt)
                            showToast('Prompt loaded from builder!', 'success')
                          }
                        }}
                        className="sm:w-auto"
                      >
                        Load from Builder
                      </Button>
                    </div>
                    {rawPrompt && (
                      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-neutral-500">
                        <span>💡</span>
                        <span>Your prompt is ready to use. Click the button above to proceed.</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

