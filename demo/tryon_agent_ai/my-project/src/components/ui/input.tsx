'use client'

import { cn } from '../../lib/utils'
import { useTheme } from '../ThemeProvider'

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  const { theme } = useTheme()
  return (
    <input
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500 disabled:bg-gray-900 disabled:cursor-not-allowed'
          : 'border-neutral-300 disabled:bg-neutral-100 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  )
}

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const { theme } = useTheme()
  return (
    <textarea
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'resize-none',
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500 disabled:bg-gray-900 disabled:cursor-not-allowed'
          : 'border-neutral-300 disabled:bg-neutral-100 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  )
}

export function Select({
  children,
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  const { theme } = useTheme()
  return (
    <select
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700 text-white disabled:bg-gray-900 disabled:cursor-not-allowed'
          : 'border-neutral-300 disabled:bg-neutral-100 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

