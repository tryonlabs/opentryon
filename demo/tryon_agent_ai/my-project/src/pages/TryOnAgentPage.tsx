'use client';

import React, { useState, useRef } from "react";
import SessionsPanel from "../components/SessionsPanel";
import ConversationView from "../components/ConversationView";
import ArtifactGallery from "../components/ArtifactGallery";
import { dummyMessages, dummyArtifacts } from "../data/dummyData";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  artifacts?: any[];
  toolExecutions?: any[];
}

interface Artifact {
  id: string;
  type: "image" | "video";
  source: "uploaded" | "generated" | "intermediate";
  url: string;
  thumbnail?: string;
  metadata: {
    dimensions: { width: number; height: number };
    size: number;
    format?: string;
    createdAt: Date;
  };
  tags?: string[];
  sessionId?: string;
}

interface SelectedFile {
  file: File;
  preview: string;
  type: "image" | "video";
  name: string;
}

export default function TryOnAgentPage() {

  const [activeSessionId, setActiveSessionId] = useState("session-1");
  const [chatMessages, setChatMessages] = useState(dummyMessages);
  const [chatInput, setChatInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedArtifact, setSelectedArtifact] = useState<any>(null);
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [uploadType, setUploadType] = useState<"image" | "video" | "all">("all");
  const [showSessionsPanel, setShowSessionsPanel] = useState(false);
  const [showArtifactGallery, setShowArtifactGallery] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSessionSelect = (sessionId: string) => {
    setActiveSessionId(sessionId);
    // In real implementation, load session data
    // For now, keep using dummy data
  };

  const handleCreateSession = () => {
    // In real implementation, open modal to create new session
    alert("New session creation - to be implemented");
  };

  const handleSendMessage = () => {
    if ((!chatInput.trim() && selectedFiles.length === 0) || isProcessing) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user" as const,
      content: chatInput,
      timestamp: new Date(),
      artifacts: [],
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setSelectedFiles([]);
    setIsProcessing(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "assistant" as const,
        content: "I understand your request. Processing...",
        timestamp: new Date(),
        artifacts: [],
        toolExecutions: [{ tool: "processing", status: "completed" as const }]
      };
      setChatMessages(prev => [...prev, assistantMessage]);
      setIsProcessing(false);
    }, 1500);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => {
      const newFiles = [...prev];
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview);
      }
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const handleFileUpload = (type: "image" | "video") => {
    setUploadType(type || "all");
    // Use setTimeout to ensure state update is processed before click
    setTimeout(() => {
      fileInputRef.current?.click();
    }, 0);
  };

  const handleArtifactView = (artifact: any) => {
    setSelectedArtifact(artifact);
    // In real implementation, open full-screen viewer
  };

  const handleArtifactDownload = (artifact: any) => {
    // In real implementation, download artifact
    alert(`Downloading ${artifact.type}: ${artifact.id}`);
  };

  const handleArtifactRemove = (artifactId: string) => {
    // In real implementation, remove artifact
    alert(`Removing artifact: ${artifactId}`);
  };

  const handleArtifactUse = (artifact: any) => {
    // In real implementation, use artifact in prompt
    setChatInput(`Use this ${artifact.type} in the next step`);
  };

  const getAcceptAttribute = () => {
    switch (uploadType) {
      case 'image':
        return "image/*";
      case 'video':
        return "video/*";
      default:
        return "image/*,video/*";
    }
  };

  return (
    <div className="relative flex flex-col lg:flex-row w-full h-screen lg:overflow-hidden overflow-auto" style={{ backgroundColor: 'transparent' }}>
      {/* Mobile Overlay */}
      {(showSessionsPanel || showArtifactGallery) && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => {
            setShowSessionsPanel(false);
            setShowArtifactGallery(false);
          }}
        />
      )}

      {/* Left Panel - Sessions */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50 lg:z-auto
        transform transition-transform duration-300 ease-in-out
        ${showSessionsPanel ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <SessionsPanel
          activeSessionId={activeSessionId}
          onSessionSelect={(id: string) => {
            handleSessionSelect(id);
            setShowSessionsPanel(false);
          }}
          onCreateSession={handleCreateSession}
          onClose={() => setShowSessionsPanel(false)}
        />
      </div>

      {/* Center Panel - Conversation */}
      <div className="flex-1 flex flex-col min-w-0 relative min-h-0 lg:min-h-screen">
        {/* Mobile Header with Toggle Buttons */}
        <div className="lg:hidden flex items-center justify-between p-3 border-b border-gray-200 z-30 sticky top-0 flex-shrink-0" style={{ backgroundColor: 'transparent' }}>
          <button
            onClick={() => setShowSessionsPanel(!showSessionsPanel)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Toggle Sessions"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-sm font-semibold text-gray-700">TryOn Agent</h1>
          <button
            onClick={() => setShowArtifactGallery(!showArtifactGallery)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Toggle Artifacts"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
        </div>

        <ConversationView
          messages={chatMessages}
          chatInput={chatInput}
          setChatInput={setChatInput}
          onSend={handleSendMessage}
          isProcessing={isProcessing}
          onFileUpload={handleFileUpload}
          showSettings={showSettings}
          setShowSettings={setShowSettings}
          selectedFiles={selectedFiles}
          onRemoveFile={handleRemoveFile}
        />
      </div>

      {/* Right Panel - Artifact Gallery */}
      <div className={`
        fixed lg:static inset-y-0 right-0 z-50 lg:z-auto
        transform transition-transform duration-300 ease-in-out
        ${showArtifactGallery ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
        h-screen lg:h-auto
      `}>
        <ArtifactGallery
          artifacts={dummyArtifacts}
          onUpload={() => handleFileUpload("image")}
          onView={handleArtifactView}
          onDownload={handleArtifactDownload}
          onRemove={handleArtifactRemove}
          onUse={handleArtifactUse}
          onClose={() => setShowArtifactGallery(false)}
        />
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={getAcceptAttribute()}
        className="hidden"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            const newFiles = Array.from(e.target.files).map(file => ({
              file,
              preview: URL.createObjectURL(file),
              type: (file.type.startsWith('image/') ? 'image' : 'video') as "image" | "video",
              name: file.name
            }));
            setSelectedFiles(prev => [...prev, ...newFiles]);
          }
          // Reset input value to allow selecting the same file again
          e.target.value = '';
        }}
      />
    </div>
  );
}
