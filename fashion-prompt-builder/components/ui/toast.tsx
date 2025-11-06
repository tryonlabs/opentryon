'use client'

import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface ToastProps {
  message: string
  type: 'success' | 'warning' | 'error'
  isVisible: boolean
  onClose: () => void
}

export function Toast({ message, type, isVisible, onClose }: ToastProps) {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose()
      }, 4000) // Auto-close after 4 seconds
      return () => clearTimeout(timer)
    }
  }, [isVisible, onClose])

  if (!isVisible) return null

  const styles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  }

  const icons = {
    success: '✓',
    warning: '⚠',
    error: '✕',
  }

  return (
    <div
      className={cn(
        'fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg',
        'animate-in slide-in-from-top-5 fade-in-0 duration-300',
        styles[type]
      )}
    >
      <span className="text-lg font-semibold">{icons[type]}</span>
      <span className="text-sm font-medium">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 text-current opacity-70 hover:opacity-100 transition-opacity"
      >
        <span className="sr-only">Close</span>
        <span className="text-lg">×</span>
      </button>
    </div>
  )
}

