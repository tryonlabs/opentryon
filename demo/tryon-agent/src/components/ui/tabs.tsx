'use client'

import React, { useState, createContext, useContext } from 'react'
import { cn } from '../../lib/utils'
import { useTheme } from '../ThemeProvider'

interface TabsContextType {
  activeTab: string
  setActiveTab: (value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

export function Tabs({
  defaultValue,
  children,
}: {
  defaultValue: string
  children: React.ReactNode
}) {
  const [activeTab, setActiveTab] = useState(defaultValue)

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="w-full">{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const { theme } = useTheme()
  return (
    <div
      className={cn(
        'inline-flex w-full h-auto sm:h-12 items-center justify-center rounded-xl p-1 sm:p-1.5 shadow-sm border',
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700'
          : 'bg-gradient-to-r from-neutral-50 via-white to-neutral-50 border-neutral-200',
        className
      )}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = useContext(TabsContext)
  const { theme } = useTheme()
  if (!context) throw new Error('TabsTrigger must be used within Tabs')
  const { activeTab, setActiveTab } = context
  const isActive = activeTab === value

  return (
    <button
      onClick={() => setActiveTab(value)}
      className={cn(
        'relative inline-flex items-center justify-center whitespace-nowrap rounded-lg px-2 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold transition-all duration-200 gap-1 sm:gap-2',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-2',
        isActive
          ? 'bg-gradient-to-br from-primary-400 to-primary-500 text-white shadow-lg shadow-primary-400/30 scale-105'
          : theme === 'dark'
            ? 'text-gray-400 hover:text-white hover:bg-gray-700'
            : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100/50',
        className
      )}
    >
      <span className="relative z-10 flex items-center gap-1 sm:gap-2">
        {children}
      </span>
      {isActive && (
        <span className="absolute inset-0 rounded-lg bg-gradient-to-br from-primary-400/20 to-primary-500/20 blur-sm -z-0" />
      )}
    </button>
  )
}

export function TabsContent({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = useContext(TabsContext)
  if (!context) throw new Error('TabsContent must be used within Tabs')
  const { activeTab } = context

  if (activeTab !== value) return null

  return (
    <div className={cn('mt-4', className)}>
      {children}
    </div>
  )
}

