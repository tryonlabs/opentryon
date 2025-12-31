'use client';

import React, { useState, useEffect } from "react";
import { IoClose, IoDownloadOutline, IoEyeOutline, IoImageOutline, IoVideocamOutline } from "react-icons/io5";
import { formatDistanceToNow } from "../utils/dateUtils";
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

interface ArtifactCardProps {
  artifact: Artifact;
  onView?: (artifact: Artifact) => void;
  onDownload?: (artifact: Artifact) => void;
  onRemove?: (id: string) => void;
  onUse?: (artifact: Artifact) => void;
}

export default function ArtifactCard({ artifact, onView, onDownload, onRemove, onUse }: ArtifactCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [timeAgo, setTimeAgo] = useState("");
  const { theme } = useTheme();

  useEffect(() => {
    // Calculate time only on client to avoid hydration mismatch
    if (artifact.metadata?.createdAt) {
      const createdAt = artifact.metadata.createdAt;
      setTimeAgo(formatDistanceToNow(createdAt));
      
      // Update every minute
      const interval = setInterval(() => {
        setTimeAgo(formatDistanceToNow(createdAt));
      }, 60000);

      return () => clearInterval(interval);
    } else {
      setTimeAgo("Unknown");
    }
  }, [artifact.metadata?.createdAt]);

  const getSourceBadge = (source: string) => {
    switch (source) {
      case "uploaded":
        return { label: "Input", color: "bg-blue-500" };
      case "generated":
        return { label: "Output", color: "bg-green-500" };
      case "intermediate":
        return { label: "Intermediate", color: "bg-amber-500" };
      default:
        return { label: "Artifact", color: "bg-gray-500" };
    }
  };

  const badge = getSourceBadge(artifact.source);

  return (
    <div
      className={`relative group border rounded-lg overflow-hidden hover:shadow-md transition-all cursor-pointer ${
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700'
          : 'bg-white border-gray-200'
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onView?.(artifact)}
    >
      {/* Image/Video Preview */}
      <div className="relative aspect-square bg-gray-100">
        {artifact.type === "image" && (
          <img
            src={artifact.thumbnail || artifact.url}
            alt="Artifact"
            className="w-full h-full object-cover"
          />
        )}
        {artifact.type === "video" && (
          <div className="w-full h-full flex items-center justify-center bg-gray-900">
            <IoVideocamOutline className="w-12 h-12 text-white opacity-50" />
            <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
              Video
            </div>
          </div>
        )}

        {/* Source Badge */}
        <div className={`absolute top-2 left-2 ${badge.color} text-white text-xs px-2 py-0.5 rounded-full font-medium`}>
          {badge.label}
        </div>

        {/* Hover Overlay */}
        {isHovered && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onView?.(artifact);
              }}
              className="p-2 bg-white/90 hover:bg-white rounded-lg transition-colors"
              title="View"
            >
              <IoEyeOutline className="w-5 h-5 text-gray-700" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDownload?.(artifact);
              }}
              className="p-2 bg-white/90 hover:bg-white rounded-lg transition-colors"
              title="Download"
            >
              <IoDownloadOutline className="w-5 h-5 text-gray-700" />
            </button>
            {onRemove && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove?.(artifact.id);
                }}
                className="p-2 bg-red-500/90 hover:bg-red-600 rounded-lg transition-colors"
                title="Remove"
              >
                <IoClose className="w-5 h-5 text-white" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="p-3">
        <div className="flex items-center justify-between mb-1">
          <span className={`text-xs font-medium capitalize ${
            theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            {artifact.type}
          </span>
          {artifact.metadata?.dimensions && (
            <span className={`text-xs ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {artifact.metadata.dimensions.width}×{artifact.metadata.dimensions.height}
            </span>
          )}
        </div>
        <div className={`flex items-center justify-between text-xs ${
          theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
        }`}>
          {artifact.metadata?.size && <span>{artifact.metadata.size} MB</span>}
          <span suppressHydrationWarning>{timeAgo || "Unknown"}</span>
        </div>

        {/* Tags */}
        {artifact.tags && artifact.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {artifact.tags.slice(0, 2).map((tag, index) => (
              <span
                key={index}
                className={`text-xs px-1.5 py-0.5 rounded ${
                  theme === 'dark'
                    ? 'bg-gray-700 text-gray-300'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {tag}
              </span>
            ))}
            {artifact.tags.length > 2 && (
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                theme === 'dark'
                  ? 'bg-gray-700 text-gray-300'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                +{artifact.tags.length - 2}
              </span>
            )}
          </div>
        )}

        {/* Use Button */}
        {onUse && artifact.source === "generated" && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onUse?.(artifact);
            }}
            className={`w-full mt-2 text-xs px-2 py-1 rounded transition-colors ${
              theme === 'dark'
                ? 'bg-primary-600 hover:bg-primary-700 text-white'
                : 'bg-primary-50 hover:bg-primary-100 text-primary-700'
            }`}
            suppressHydrationWarning
          >
            Use in prompt
          </button>
        )}
      </div>
    </div>
  );
}

