'use client';

import React, { useState } from "react";
import { IoAddCircleOutline, IoSearchOutline } from "react-icons/io5";
import { HiOutlineArchive } from "react-icons/hi";
import SessionCard from "./SessionCard";
import { dummySessions } from "../data/dummyData";
import { useTheme } from "./ThemeProvider";

export default function SessionsPanel({ activeSessionId, onSessionSelect, onCreateSession, onClose }: any) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const { theme } = useTheme();

  const activeSessions = dummySessions.filter(s => s.status !== "archived");
  const archivedSessions = dummySessions.filter(s => s.status === "archived");

  const filteredActive = activeSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredArchived = archivedSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full lg:w-72 border-r border-gray-200 flex flex-col h-full lg:h-screen shadow-lg lg:shadow-none overflow-hidden" style={{ backgroundColor: 'transparent' }}>
      {/* Header */}
      <div className={`p-3 lg:p-4 border-b ${
        theme === 'dark' ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-gray-50'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className={`lg:hidden p-1.5 rounded-lg transition-colors ${
                theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-gray-200'
              }`}
              aria-label="Close Sessions"
              suppressHydrationWarning
            >
              <svg className={`w-5 h-5 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <h2 className={`text-sm font-semibold uppercase tracking-wider ${
              theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Sessions
            </h2>
          </div>
          <button
            onClick={onCreateSession}
            className={`p-1.5 rounded-lg transition-colors ${
              theme === 'dark' ? 'hover:bg-gray-800' : 'hover:bg-gray-200'
            }`}
            title="New Session"
            suppressHydrationWarning
          >
            <IoAddCircleOutline className="w-5 h-5 text-primary-600" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <IoSearchOutline className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${
            theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
          }`} />
          <input
            type="text"
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`w-full pl-9 pr-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
              theme === 'dark'
                ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500'
                : 'border-gray-300 text-gray-900'
            }`}
            suppressHydrationWarning
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 lg:p-3 space-y-2 -webkit-overflow-scrolling-touch" style={{ WebkitOverflowScrolling: 'touch' }}>
        {/* Active Sessions */}
        {filteredActive.length > 0 && (
          <div>
            <h3 className={`text-xs font-semibold uppercase tracking-wider mb-2 px-1 ${
              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Active
            </h3>
            <div className="space-y-2">
              {filteredActive.map((session) => (
                <SessionCard
                  key={session.id}
                  session={session}
                  isActive={session.id === activeSessionId}
                  onClick={() => onSessionSelect(session.id)}
                  onArchive={undefined}
                />
              ))}
            </div>
          </div>
        )}

        {/* Archived Sessions */}
        {filteredArchived.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowArchived(!showArchived)}
              className={`flex items-center gap-2 text-xs font-semibold uppercase tracking-wider mb-2 px-1 transition-colors w-full ${
                theme === 'dark'
                  ? 'text-gray-400 hover:text-gray-300'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              suppressHydrationWarning
            >
              <HiOutlineArchive className="w-4 h-4" />
              <span>Archived</span>
              <span className={`ml-auto ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                ({filteredArchived.length})
              </span>
            </button>
            {showArchived && (
              <div className="space-y-2">
                {filteredArchived.map((session) => (
                  <SessionCard
                    key={session.id}
                    session={session}
                    isActive={session.id === activeSessionId}
                    onClick={() => onSessionSelect(session.id)}
                    onArchive={undefined}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {filteredActive.length === 0 && filteredArchived.length === 0 && (
          <div className={`text-center py-8 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
            <p className="text-sm">No sessions found</p>
            <button
              onClick={onCreateSession}
              className="mt-2 text-xs text-primary-600 hover:text-primary-700"
            >
              Create your first session
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

