'use client'

import { cn } from '../../lib/utils'

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'bg-[var(--card-bg)] border-[var(--border-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)]',
        'disabled:bg-[var(--bg-tertiary)] disabled:cursor-not-allowed',
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
  return (
    <textarea
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'resize-none',
        'bg-[var(--card-bg)] border-[var(--border-primary)] text-[var(--text-primary)] placeholder-[var(--text-tertiary)]',
        'disabled:bg-[var(--bg-tertiary)] disabled:cursor-not-allowed',
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
  return (
    <select
      className={cn(
        'w-full px-3 py-2 border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'bg-[var(--card-bg)] border-[var(--border-primary)] text-[var(--text-primary)]',
        'disabled:bg-[var(--bg-tertiary)] disabled:cursor-not-allowed',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

