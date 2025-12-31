'use client';

import React from 'react';
import { useTheme } from './ThemeProvider';

const ModelUi = () => {
  const { theme } = useTheme();
    // Default data
    const defaultPrompt = "Any text...";
    const defaultReferenceImages = [
        "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=200&h=200&fit=crop",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=200&h=200&fit=crop",
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=200&h=200&fit=crop",
        "https://images.unsplash.com/photo-1445205170230-053b73816037?w=200&h=200&fit=crop",
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=200&h=200&fit=crop",
        "https://images.unsplash.com/photo-1445205170230-053b73816037?w=200&h=200&fit=crop"
    ];
    const defaultMainImage = defaultReferenceImages[0];
    const defaultSettings = {
        mode: "virtual-try-on",
        quality: "high",
        output: "2k"
    };

    return (
        <div className="flex gap-2 justify-start mb-3 w-full">
            {/* AI Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">AI</span>
            </div>
            
            {/* Message Bubble with all content */}
            <div className="flex flex-col items-start max-w-full sm:max-w-md md:max-w-lg flex-1 min-w-0">
                <div className={`border rounded-lg px-3 py-2 shadow-sm w-full ${
                  theme === 'dark'
                    ? 'bg-gray-800 text-white border-gray-700'
                    : 'bg-white text-gray-800 border-gray-200'
                }`}>
                    {/* Prompt Text */}
                    <p className="text-xs whitespace-pre-wrap mb-2">
                        Great! I can help you with virtual try-on. I see you've uploaded a dress image. Would you like me to:
                    </p>

                    {/* Main Image - Commented */}
                    <div className="mb-2">
                        <div className={`relative w-full border-2 border-dashed rounded-lg overflow-hidden flex items-center justify-center min-h-48 ${
                          theme === 'dark'
                            ? 'bg-gray-900 border-gray-700'
                            : 'bg-gray-50 border-gray-300'
                        }`}>
                            <img
                                src={defaultMainImage}
                                alt="Main"
                                className="w-full h-auto max-h-64 object-contain"
                            />
                        </div>
                    </div>

                    {/* Main Image - Two Images Side by Side */}
                    {/* <div className="mb-2">
                        <div className="relative w-full bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg overflow-hidden flex flex-col sm:flex-row gap-1.5 sm:gap-2 p-1.5 sm:p-2">
                            <div className="flex-1 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center min-h-32 sm:min-h-40 md:min-h-48">
                                <img
                                    src={defaultMainImage}
                                    alt="Main Left"
                                    className="w-full h-auto max-h-32 sm:max-h-40 md:max-h-48 object-contain"
                                />
                            </div>
                            <div className="flex-1 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center min-h-32 sm:min-h-40 md:min-h-48">
                                <img
                                    src={defaultReferenceImages[1] || defaultMainImage}
                                    alt="Main Right"
                                    className="w-full h-auto max-h-32 sm:max-h-40 md:max-h-48 object-contain"
                                />
                            </div>
                            <div className="flex-1 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center min-h-32 sm:min-h-40 md:min-h-48">
                                <img
                                    src={defaultReferenceImages[1] || defaultMainImage}
                                    alt="Main Right"
                                    className="w-full h-auto max-h-32 sm:max-h-40 md:max-h-48 object-contain"
                                />
                            </div>
                        </div>
                    </div> */}

                    {/* Reference Images */}
                    <div className="mb-2">
                        <label className={`block text-xs font-semibold mb-1 ${
                          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                            Reference Image ({defaultReferenceImages.length})
                        </label>
                        {defaultReferenceImages.length < 6 ? (
                            <div className="flex gap-1 sm:gap-1.5 overflow-x-auto pb-1">
                                {defaultReferenceImages.map((imgSrc, index) => (
                                    <div
                                        key={index}
                                        className="relative w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 flex-shrink-0"
                                    >
                                        <img
                                            src={imgSrc}
                                            alt={`Reference ${index + 1}`}
                                            className={`w-full h-full object-cover rounded-lg border-2 ${
                                              theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                                            }`}
                                        />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="grid grid-cols-3 gap-1.5">
                                {defaultReferenceImages.map((imgSrc, index) => (
                                    <div
                                        key={index}
                                        className="relative w-full aspect-square"
                                    >
                                        <img
                                            src={imgSrc}
                                            alt={`Reference ${index + 1}`}
                                            className={`w-full h-full object-cover rounded-lg border-2 ${
                                              theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
                                            }`}
                                        />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Image Settings */}
                    <div>
                        <label className={`block text-xs font-semibold mb-1 ${
                          theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                        }`}>
                            Settings → Images
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                            <div>
                                <label className={`block text-xs mb-0.5 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                                }`}>Mode</label>
                                <select
                                    value={defaultSettings.mode}
                                    className={`w-full px-2 py-1.5 border rounded-lg text-xs focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                                      theme === 'dark'
                                        ? 'bg-gray-800 border-gray-700 text-white'
                                        : 'border-gray-300'
                                    }`}
                                    disabled
                                    suppressHydrationWarning
                                >
                                    <option value="virtual-try-on">Virtual Try-On</option>
                                    <option value="model-generation">Model Generation</option>
                                    <option value="catalog-generation">Catalog Generation</option>
                                </select>
                            </div>
                            <div>
                                <label className={`block text-xs mb-0.5 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                                }`}>Quality</label>
                                <select
                                    value={defaultSettings.quality}
                                    className={`w-full px-2 py-1.5 border rounded-lg text-xs focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                                      theme === 'dark'
                                        ? 'bg-gray-800 border-gray-700 text-white'
                                        : 'border-gray-300'
                                    }`}
                                    disabled
                                    suppressHydrationWarning
                                >
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="ultra">Ultra</option>
                                </select>
                            </div>
                            <div>
                                <label className={`block text-xs mb-0.5 ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                                }`}>Output</label>
                                <select
                                    value={defaultSettings.output}
                                    className={`w-full px-2 py-1.5 border rounded-lg text-xs focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                                      theme === 'dark'
                                        ? 'bg-gray-800 border-gray-700 text-white'
                                        : 'border-gray-300'
                                    }`}
                                    disabled
                                    suppressHydrationWarning
                                >
                                    <option value="1080p">1080p</option>
                                    <option value="2k">2K</option>
                                    <option value="4k">4K</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ModelUi;
