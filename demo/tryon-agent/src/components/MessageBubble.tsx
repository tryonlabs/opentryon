'use client';

import React, { useState, useEffect } from "react";
import { IoCheckmarkCircle, IoTimeOutline } from "react-icons/io5";
import { formatDistanceToNow } from "../utils/dateUtils";
import { useTheme } from "./ThemeProvider";

interface Artifact {
  id: string;
  type: "image" | "video";
  url: string;
  thumbnail?: string;
  source?: string;
}

interface ToolExecution {
  tool: string;
  status: "processing" | "completed" | "queued";
  progress?: number;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  artifacts?: Artifact[];
  toolExecutions?: ToolExecution[];
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const [timeAgo, setTimeAgo] = useState("");
  const { theme } = useTheme();

  useEffect(() => {
    // Calculate time only on client to avoid hydration mismatch
    setTimeAgo(formatDistanceToNow(message.timestamp));
    
    // Update every minute
    const interval = setInterval(() => {
      setTimeAgo(formatDistanceToNow(message.timestamp));
    }, 60000);

    return () => clearInterval(interval);
  }, [message.timestamp]);

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className={`text-xs px-3 py-1.5 rounded-full border ${
          theme === 'dark' 
            ? 'bg-gray-800 text-gray-300 border-gray-700' 
            : 'bg-gray-100 text-gray-600 border-gray-200'
        }`}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2 ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0">
          <span className="text-[10px] sm:text-xs font-bold text-white">AI</span>
        </div>
      )}

      {/* Message Content */}
      <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] md:max-w-2xl ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-lg px-2.5 sm:px-3 py-1.5 sm:py-2 ${
            isUser
              ? "bg-red-500 text-white"
              : theme === 'dark'
                ? "bg-gray-800 text-white border border-gray-700 shadow-sm"
                : "bg-white text-gray-800 border border-gray-200 shadow-sm"
          }`}
        >
          {/* Message Text */}
          <p className="text-xs sm:text-sm whitespace-pre-wrap break-words">{message.content}</p>

          {/* Artifacts */}
          {message.artifacts && message.artifacts.length > 0 && (
            <div className={`mt-2 sm:mt-3 grid gap-1.5 sm:gap-2 ${
              message.artifacts.length === 1 ? "grid-cols-1" :
              message.artifacts.length === 2 ? "grid-cols-2" :
              "grid-cols-2 sm:grid-cols-3"
            }`}>
              {message.artifacts.map((artifact) => (
                <div key={artifact.id} className="relative group">
                  <img
                    src={artifact.thumbnail || artifact.url}
                    alt="Artifact"
                    className="w-full h-24 sm:h-32 object-cover rounded-lg border border-gray-200 cursor-pointer hover:opacity-90 transition-opacity"
                  />
                  {artifact.source === "generated" && (
                    <div className="absolute top-1 right-1 bg-green-500 text-white text-xs px-1.5 py-0.5 rounded">
                      New
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Tool Executions */}
          {message.toolExecutions && message.toolExecutions.length > 0 && (
            <div className="mt-3 space-y-1.5">
              {message.toolExecutions.map((tool, index) => (
                <div key={index} className="flex items-center gap-2 text-xs">
                  {tool.status === "processing" && (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-300 border-t-primary-500"></div>
                      <span className={isUser ? "text-red-100" : theme === 'dark' ? "text-gray-300" : "text-gray-600"}>
                        {tool.tool} - {tool.progress}%
                      </span>
                    </>
                  )}
                  {tool.status === "completed" && (
                    <>
                      <IoCheckmarkCircle className="w-3 h-3 text-green-500" />
                      <span className={isUser ? "text-red-100" : theme === 'dark' ? "text-gray-300" : "text-gray-600"}>
                        {tool.tool} completed
                      </span>
                    </>
                  )}
                  {tool.status === "queued" && (
                    <>
                      <IoTimeOutline className="w-3 h-3 text-gray-400" />
                      <span className={isUser ? "text-red-100" : theme === 'dark' ? "text-gray-300" : "text-gray-600"}>
                        {tool.tool} queued
                      </span>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className={`text-[10px] sm:text-xs mt-1 px-1 ${
          theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
        }`} suppressHydrationWarning>
          {timeAgo || "just now"}
        </span>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
          <span className="text-[10px] sm:text-xs text-gray-700">U</span>
        </div>
      )}
    </div>
  );
}

