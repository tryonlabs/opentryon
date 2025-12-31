import React, { useRef, useEffect, useState } from "react";
import MessageBubble from "./MessageBubble";
import ModelUi from "./ModelUi";
import { useTheme } from "./ThemeProvider";
import {
  IoArrowUp,
  IoImageOutline,
  IoVideocamOutline,
  IoClose,
  IoAdd,
} from "react-icons/io5";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  artifacts?: any[];
  toolExecutions?: any[];
}

interface SelectedFile {
  file: File;
  preview: string;
  type: "image" | "video";
  name: string;
}

interface ConversationViewProps {
  messages: Message[];
  chatInput: string;
  setChatInput: (value: string) => void;
  onSend: () => void;
  isProcessing: boolean;
  onFileUpload: (type: "image" | "video") => void;
  showSettings: boolean;
  setShowSettings: (value: boolean) => void;
  selectedFiles?: SelectedFile[];
  onRemoveFile: (index: number) => void;
}

export default function ConversationView({
  messages,
  chatInput,
  setChatInput,
  onSend,
  isProcessing,
  onFileUpload,
  showSettings,
  setShowSettings,
  selectedFiles = [],
  onRemoveFile,
}: ConversationViewProps) {
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [selectedMode, setSelectedMode] = useState("");
  const [showMediaMenu, setShowMediaMenu] = useState(false);
  const [selectedQuality, setSelectedQuality] = useState("");
  const [selectedOutput, setSelectedOutput] = useState("");
  const { theme } = useTheme();

  // dynamic settings
  const modeSettings: Record<string, { quality: string[]; output: string[] }> = {
    "virtual-try-on": {
      quality: ["Medium", "High", "Ultra"],
      output: ["1080p", "2K", "4K"],
    },
    "model-generation": {
      quality: ["Standard", "High Fidelity"],
      output: ["2K", "4K"],
    },
    "catalog-generation": {
      quality: ["Web Optimized", "High Quality"],
      output: ["720p", "1080p"],
    },
  };

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(e.target.value);
    e.target.style.height = "48px";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (chatInput.trim() && !isProcessing) {
        onSend();
      }
    }
  };
  return (
    <div className="flex-1 flex flex-col overflow-hidden min-h-0" style={{ backgroundColor: 'transparent' }}>
      {/* Messages Area */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden p-3 sm:p-4 space-y-3 -webkit-overflow-scrolling-touch"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {/* Model UI Component */}
        <div className="mb-6">
          <ModelUi />
        </div>

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">AI</span>
            </div>
            <div className={`border rounded-lg px-4 py-3 shadow-sm ${
              theme === 'dark'
                ? 'bg-gray-800 text-white border-gray-700'
                : 'bg-white text-gray-800 border-gray-200'
            }`}>
              <div className="flex gap-1">
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className={`border-t p-2 sm:p-3 ${
        theme === 'dark' ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'
      }`}>
        <div className={`relative border rounded-lg focus-within:ring-0 focus-within:outline-none transition-all ${
          theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-300'
        }`}>
          <div className="px-2 sm:px-4 pt-2 sm:pt-3 pb-0 flex flex-wrap gap-2 items-center">
            <div className="relative">
              <button
                onClick={() => setShowMediaMenu(!showMediaMenu)}
                className="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-full transition-colors"
                title="Add media"
                suppressHydrationWarning
              >
                <IoAdd className={`w-5 h-5 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`} />
              </button>
              {showMediaMenu && (
                <div className={`absolute top-full left-0 mt-1 z-20 border shadow-lg rounded-lg py-1 w-32 ${
                  theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
                }`}>
                  <button
                    onClick={() => {
                      onFileUpload("image");
                      setShowMediaMenu(false);
                    }}
                    className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
                      theme === 'dark'
                        ? 'hover:bg-gray-700 text-gray-300'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <IoImageOutline /> Image
                  </button>
                  <button
                    onClick={() => {
                      onFileUpload("video");
                      setShowMediaMenu(false);
                    }}
                    className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
                      theme === 'dark'
                        ? 'hover:bg-gray-700 text-gray-300'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <IoVideocamOutline /> Video
                  </button>
                </div>
              )}
            </div>

            {/* Selected Files */}
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="relative w-12 h-12 sm:w-16 sm:h-16 flex-shrink-0 group"
              >
                {file.type === "image" ? (
                  <img
                    src={file.preview}
                    alt="preview"
                    className="w-full h-full object-cover rounded-lg border border-gray-200"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200 rounded-lg flex items-center justify-center border border-gray-300">
                    <IoVideocamOutline className="w-6 h-6 text-gray-500" />
                  </div>
                )}
                <button
                  onClick={() => onRemoveFile(index)}
                  className="absolute -top-1.5 -right-1.5 bg-gray-800 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                >
                  <IoClose className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
         {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={chatInput}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Describe what you'd like to do..."
            rows={1}
            className={`w-full bg-transparent border-none px-2 sm:px-4 py-2 sm:py-3 text-sm focus:ring-0 focus:outline-none resize-none overflow-y-auto ${
              theme === 'dark'
                ? 'text-white placeholder-gray-500'
                : 'text-gray-900 placeholder-gray-400'
            }`}
            style={{ minHeight: "48px", maxHeight: "120px" }}
            suppressHydrationWarning
          />

          {/* Dropdown and Settings */}
          <div className="px-2 sm:px-4 py-2 flex items-center gap-2 sm:gap-3 overflow-x-auto no-scrollbar">
            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value)}
              className={`h-8 pl-2 sm:pl-3 pr-3 sm:pr-4 rounded-full border text-xs shadow-sm cursor-pointer appearance-none w-32 sm:w-40 focus:outline-none focus:ring-2 focus:ring-primary-400 flex-shrink-0 ${
                theme === 'dark'
                  ? 'border-gray-700 text-gray-300 bg-gray-800'
                  : 'border-gray-300 text-gray-700 bg-white'
              }`}
              suppressHydrationWarning
            >
              <option value="">Select Mode</option>
              <option value="virtual-try-on">Virtual Try-On - Summer</option>
              <option value="model-generation">
                Model Generation - Fashion
              </option>
              <option value="catalog-generation">
                Catalog Generation - Prod
              </option>
            </select>

            {selectedMode && (
              <>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Quality pill dropdown */}
                  <select
                    value={selectedQuality}
                    onChange={(e) => setSelectedQuality(e.target.value)}
                    className="h-8 px-3 rounded-full border border-gray-300 text-xs text-gray-700 bg-white shadow-sm focus:ring-2 focus:ring-primary-400 cursor-pointer"
                    suppressHydrationWarning
                  >
                    <option value="">Quality</option>
                    {modeSettings[selectedMode]?.quality?.map((q: string, i: number) => (
                      <option key={i} value={q}>
                        {q}
                      </option>
                    ))}
                  </select>

                  {/* Output pill dropdown */}
                  <select
                    value={selectedOutput}
                    onChange={(e) => setSelectedOutput(e.target.value)}
                    className={`h-8 px-3 rounded-full border text-xs shadow-sm focus:ring-2 focus:ring-primary-400 cursor-pointer ${
                      theme === 'dark'
                        ? 'border-gray-700 text-gray-300 bg-gray-800'
                        : 'border-gray-300 text-gray-700 bg-white'
                    }`}
                    suppressHydrationWarning
                  >
                    <option value="">Output</option>
                    {modeSettings[selectedMode]?.output?.map((o: string, i: number) => (
                      <option key={i} value={o}>
                        {o}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>

          {/* Send Button */}
          <button
            onClick={onSend}
            disabled={
              (!chatInput.trim() && selectedFiles.length === 0) || isProcessing
            }
            className="absolute right-1 sm:right-2 bottom-1 sm:bottom-2 p-1.5 sm:p-2 bg-primary-500 hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-lg transition-colors shadow-sm"
            suppressHydrationWarning
          >
            <IoArrowUp className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>

      <style>
        {`
  select {
    border-radius: 9999px !important;  /* rounded-full */
    overflow: hidden;
  }

  select option {
    padding: 8px 12px;
    font-size: 12px;
    color: #444;
  }
  
  select option:hover,
  select option:focus,
  select option:checked {
    background-color: #eef2ff !important; /* soft purple highlight */
    color: #4f46e5;  /* indigo text */
  }

  /* hide default blue selected highlight */
  select:focus option {
    background: transparent;
  } 
`}
      </style>
    </div>
  );
}
