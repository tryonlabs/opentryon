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
    <div className="w-full lg:w-72 border-r border-[var(--border-primary)] flex flex-col h-full lg:h-screen shadow-lg lg:shadow-none overflow-hidden bg-[var(--background)]">
      {/* Header */}
      <div className="p-3 lg:p-4 border-b border-[var(--border-primary)] bg-[var(--card-bg)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 rounded-lg transition-colors hover:bg-[var(--bg-secondary)]"
              aria-label="Close Sessions"
              suppressHydrationWarning
            >
              <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-primary)]">
              Sessions
            </h2>
          </div>
          <button
            onClick={onCreateSession}
            className="p-1.5 rounded-lg transition-colors hover:bg-[var(--bg-secondary)]"
            title="New Session"
            suppressHydrationWarning
          >
            <IoAddCircleOutline className="w-5 h-5 text-primary-600" />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <IoSearchOutline className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-[var(--card-bg)] border-[var(--border-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)]"
            suppressHydrationWarning
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 lg:p-3 space-y-2 -webkit-overflow-scrolling-touch" style={{ WebkitOverflowScrolling: 'touch' }}>
        {/* Active Sessions */}
        {filteredActive.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider mb-2 px-1 text-[var(--text-secondary)]">
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
              className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider mb-2 px-1 transition-colors w-full text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              suppressHydrationWarning
            >
              <HiOutlineArchive className="w-4 h-4" />
              <span>Archived</span>
              <span className="ml-auto text-[var(--text-tertiary)]">
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
          <div className="text-center py-8 text-[var(--text-secondary)]">
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

