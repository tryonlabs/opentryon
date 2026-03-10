'use client';

import React, { useState } from "react";
import { IoGridOutline, IoListOutline, IoTimeOutline } from "react-icons/io5";
import { AiOutlineCloudUpload } from "react-icons/ai";
import ArtifactCard from "./ArtifactCard";
import { useTheme } from "./ThemeProvider";

interface Artifact {
  id: string;
  type: "image" | "video";
  source: "uploaded" | "generated" | "intermediate";
  url: string;
  thumbnail?: string;
  metadata?: {
    dimensions: { width: number; height: number };
    size: number;
    format?: string;
    createdAt: Date;
  };
  tags?: string[];
  sessionId?: string;
}

interface ArtifactGalleryProps {
  artifacts: Artifact[];
  onUpload?: () => void;
  onView?: (artifact: Artifact) => void;
  onDownload?: (artifact: Artifact) => void;
  onRemove?: (id: string) => void;
  onUse?: (artifact: Artifact) => void;
  onClose?: () => void;
}

export default function ArtifactGallery({ artifacts, onUpload, onView, onDownload, onRemove, onUse, onClose }: ArtifactGalleryProps) {
  const [viewMode, setViewMode] = useState("grid"); // grid, list
  const [filter, setFilter] = useState("all"); // all, uploaded, generated, intermediate
  const { theme } = useTheme();

  const filteredArtifacts = artifacts.filter(artifact => {
    if (filter === "all") return true;
    return artifact.source === filter;
  });

  const uploadedCount = artifacts.filter(a => a.source === "uploaded").length;
  const generatedCount = artifacts.filter(a => a.source === "generated").length;
  const intermediateCount = artifacts.filter(a => a.source === "intermediate").length;

  // Extract main images (first 2 generated images) and reference images (uploaded images)
  const generatedImages = artifacts.filter(a => a.source === "generated" && a.type === "image");
  const mainImages = generatedImages.slice(0, 2); // Get first 2 generated images
  const allReferenceImages = artifacts.filter(a => a.source === "uploaded" && a.type === "image");
  
  // Get reference images - first main image gets 5, second gets 3
  const getReferenceImages = (baseImages: Artifact[], count: number) => {
    if (baseImages.length >= count) {
      return baseImages.slice(0, count);
    }
    // Duplicate to get required count
    const duplicated = [];
    while (duplicated.length < count) {
      duplicated.push(...baseImages);
    }
    return duplicated.slice(0, count);
  };
  
  // First main image gets 5 reference images, second gets 3
  const referenceImages1 = getReferenceImages(allReferenceImages, 5);
  const referenceImages2 = getReferenceImages(allReferenceImages, 3);

  return (
    <div className="w-full lg:w-96 border-l border-[var(--border-primary)] flex flex-col h-full lg:h-screen flex-shrink-0 shadow-lg lg:shadow-none overflow-hidden bg-[var(--background)]">
      {/* Header */}
      <div className="p-3 border-b border-[var(--border-primary)] bg-[var(--card-bg)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-lg transition-colors hover:bg-[var(--bg-secondary)]"
              aria-label="Close Artifacts"
              suppressHydrationWarning
            >
              <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-primary)]">
              Artifacts
            </h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded transition-colors ${
                viewMode === "grid"
                  ? "bg-primary-600 text-white"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
              title="Grid view"
              suppressHydrationWarning
            >
              <IoGridOutline className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded transition-colors ${
                viewMode === "list"
                  ? "bg-primary-600 text-white"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
              title="List view"
              suppressHydrationWarning
            >
              <IoListOutline className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setFilter("all")}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              filter === "all"
                ? "bg-primary-600 text-white font-medium"
                : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
            }`}
            suppressHydrationWarning
          >
            All ({artifacts.length})
          </button>
          <button
            onClick={() => setFilter("uploaded")}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              filter === "uploaded"
                ? "bg-primary-600 text-white font-medium"
                : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
            }`}
            suppressHydrationWarning
          >
            Input ({uploadedCount})
          </button>
          <button
            onClick={() => setFilter("generated")}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              filter === "generated"
                ? theme === 'dark'
                  ? "bg-green-600 text-white font-medium"
                  : "bg-green-100 text-green-700 font-medium"
                : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
            }`}
            suppressHydrationWarning
          >
            Output ({generatedCount})
          </button>
          {intermediateCount > 0 && (
            <button
              onClick={() => setFilter("intermediate")}
              className={`text-xs px-2 py-1 rounded transition-colors ${
                filter === "intermediate"
                  ? theme === 'dark'
                    ? "bg-amber-600 text-white font-medium"
                    : "bg-amber-100 text-amber-700 font-medium"
                  : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
              }`}
              suppressHydrationWarning
            >
              Intermediate ({intermediateCount})
            </button>
          )}
        </div>
      </div>

      {/* Gallery Content */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 -webkit-overflow-scrolling-touch" style={{ WebkitOverflowScrolling: 'touch' }}>
        {/* Gallery UI Section - Two Main Images with Reference Images in 2-column Grid */}
        {mainImages.length > 0 && (
          <div className="mb-4 pb-4 border-b border-[var(--border-primary)]">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* First Main Image */}
              <div className="flex flex-col">
                {/* Main Image */}
                <div className="mb-2">
                  <div className="relative w-full border-2 border-dashed rounded-lg overflow-hidden flex items-center justify-center bg-[var(--bg-tertiary)] border-[var(--border-primary)]" style={{ maxHeight: '200px', minHeight: '150px' }}>
                    <img
                      src={mainImages[0]?.url || mainImages[0]?.thumbnail}
                      alt="Generated Image 1"
                      className="w-full h-auto max-h-[200px] object-contain"
                    />
                  </div>
                </div>
                
                {/* Reference Images - Horizontal scroll, 5 images */}
                {referenceImages1.length > 0 && (
                  <div>
                    <label className="block text-xs font-semibold text-[var(--text-primary)] mb-1">
                      Reference ({referenceImages1.length})
                    </label>
                    <div className="overflow-x-auto">
                      <div className="flex gap-1.5 pb-1">
                        {referenceImages1.map((artifact, index) => (
                          <div
                            key={`ref1-${artifact.id}-${index}`}
                            className="relative w-16 h-16 flex-shrink-0 border border-[var(--border-primary)]"
                          >
                            <img
                              src={artifact.thumbnail || artifact.url}
                              alt={`Reference ${index + 1}`}
                              className="w-full h-full object-cover rounded-lg border border-[var(--border-primary)]"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Second Main Image */}
              {mainImages[1] && (
                <div className="flex flex-col">
                  {/* Main Image */}
                  <div className="mb-2">
                    <div className={`relative w-full border-2 border-dashed rounded-lg overflow-hidden ${
                      theme === 'dark'
                        ? 'bg-gray-900 border-gray-700'
                        : 'bg-gray-50 border-gray-300'
                    }`} style={{ maxHeight: '200px', minHeight: '150px' }}>
                      <img
                        src={mainImages[1]?.url || mainImages[1]?.thumbnail}
                        alt="Generated Image 2"
                        className="w-full h-full object-cover"
                        style={{ maxHeight: '200px' }}
                      />
                    </div>
                  </div>
                  
                  {/* Reference Images - Horizontal scroll, 3 images */}
                  {referenceImages2.length > 0 && (
                    <div>
                      <label className="block text-xs font-semibold text-[var(--text-primary)] mb-1">
                        Reference ({referenceImages2.length})
                      </label>
                      <div className="overflow-x-auto">
                        <div className="flex gap-1.5 pb-1">
                          {referenceImages2.map((artifact, index) => (
                            <div
                              key={`ref2-${artifact.id}-${index}`}
                              className="relative w-16 h-16 flex-shrink-0 border border-[var(--border-primary)]"
                            >
                              <img
                                src={artifact.thumbnail || artifact.url}
                                alt={`Reference ${index + 1}`}
                                className="w-full h-full object-cover rounded-lg border border-[var(--border-primary)]"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {filteredArtifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-[var(--text-tertiary)] to-[var(--text-secondary)] flex items-center justify-center">
              <AiOutlineCloudUpload className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
              No artifacts yet
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mb-4">
              Upload images or generate content to see artifacts here
            </p>
            <button
              onClick={() => onUpload?.()}
              className="px-4 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg text-sm font-medium transition-colors text-white"
            >
              Upload Files
            </button>
          </div>
        ) : (
          <div className={
            viewMode === "grid"
              ? "grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-2 gap-2"
              : "space-y-2"
          }>
            {filteredArtifacts.map((artifact) => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                onView={onView}
                onDownload={onDownload}
                onRemove={onRemove}
                onUse={onUse}
              />
            ))}
          </div>
        )}
      </div>

      {/* Upload Zone (if empty) */}
      {artifacts.length === 0 && (
        <div className="p-4 border-t border-[var(--border-primary)] bg-[var(--card-bg)]">
          <button
            onClick={() => onUpload?.()}
            className="w-full px-4 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg text-sm font-medium transition-colors text-white flex items-center justify-center gap-2"
          >
            <AiOutlineCloudUpload className="w-4 h-4" />
            Upload Files
          </button>
        </div>
      )}
    </div>
  );
}

