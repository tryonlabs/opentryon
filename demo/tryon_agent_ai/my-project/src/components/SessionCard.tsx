'use client';

import React, { useState, useEffect } from "react";
import { 
  IoShirtOutline,
  IoColorPaletteOutline,
  IoPeopleOutline,
  IoGridOutline,
  IoCameraOutline,
  IoImageOutline,
  IoSparklesOutline,
  IoVideocamOutline
} from "react-icons/io5";
import { HiOutlineClock, HiOutlineArchive } from "react-icons/hi";
import { formatDistanceToNow } from "../utils/dateUtils";
import { useTheme } from "./ThemeProvider";

const iconMap = {
  IoShirtOutline,
  IoColorPaletteOutline,
  IoPeopleOutline,
  IoGridOutline,
  IoCameraOutline,
  IoImageOutline,
  IoSparklesOutline,
  IoVideocamOutline
};

export default function SessionCard({ session, isActive, onClick, onArchive }: any) {
  const Icon = iconMap[session.icon as keyof typeof iconMap] || IoShirtOutline;
  const [timeAgo, setTimeAgo] = useState("");
  const { theme } = useTheme();

  useEffect(() => {
    // Calculate time only on client to avoid hydration mismatch
    setTimeAgo(formatDistanceToNow(session.updatedAt));
    
    // Update every minute
    const interval = setInterval(() => {
      setTimeAgo(formatDistanceToNow(session.updatedAt));
    }, 60000);

    return () => clearInterval(interval);
  }, [session.updatedAt]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-700 border-green-200";
      case "processing":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "completed":
        return "bg-gray-100 text-gray-700 border-gray-200";
      case "archived":
        return "bg-amber-100 text-amber-700 border-amber-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  return (
    <div
      onClick={onClick}
      className={`relative p-2.5 sm:p-3 rounded-lg border-2 cursor-pointer transition-all ${
        isActive
          ? theme === 'dark'
            ? "bg-gray-800 border-primary-500 shadow-md"
            : "bg-primary-50 border-primary-300 shadow-md"
          : theme === 'dark'
            ? "bg-gray-900 border-gray-700 hover:border-gray-600 hover:shadow-sm"
            : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
      }`}
    >
      {/* Status indicator */}
      <div className={`absolute top-2 right-2 w-2 h-2 rounded-full ${
        session.status === "active" ? "bg-green-500" :
        session.status === "processing" ? "bg-blue-500 animate-pulse" :
        session.status === "completed" ? "bg-gray-400" :
        "bg-amber-400"
      }`} />

      {/* Icon and Title */}
      <div className="flex items-start gap-2 sm:gap-3 mb-2">
        <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br ${session.color} flex items-center justify-center flex-shrink-0`}>
          <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`text-xs sm:text-sm font-semibold truncate ${
            isActive 
              ? theme === 'dark' ? "text-primary-300" : "text-primary-700"
              : theme === 'dark' ? "text-white" : "text-gray-900"
          }`}>
            {session.title}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(session.status)}`}>
              {session.status}
            </span>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between text-[10px] sm:text-xs mt-2 sm:mt-3 gap-1 sm:gap-0 ${
        theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
      }`}>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="flex items-center gap-1">
            <HiOutlineClock className="w-3 h-3" />
            <span suppressHydrationWarning>{timeAgo || "just now"}</span>
          </span>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="whitespace-nowrap">{session.artifactCount} artifacts</span>
          <span className="hidden sm:inline">•</span>
          <span className="whitespace-nowrap">{session.messageCount} messages</span>
        </div>
      </div>

      {/* Actions */}
      {isActive && (
        <div className={`flex items-center gap-2 mt-2 pt-2 border-t ${
          theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onArchive?.(session.id);
            }}
            className={`flex-1 text-xs px-2 py-1 rounded transition-colors ${
              theme === 'dark'
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            }`}
            suppressHydrationWarning
          >
            Archive
          </button>
        </div>
      )}
    </div>
  );
}

