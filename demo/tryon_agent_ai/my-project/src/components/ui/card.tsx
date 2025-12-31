'use client'

import { cn } from '../../lib/utils'
import { useTheme } from '../ThemeProvider'

export function Card({
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
        'rounded-lg border p-6 shadow-sm',
        theme === 'dark'
          ? 'bg-gray-800 border-gray-700'
          : 'bg-white border-neutral-200',
        className
      )}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('mb-4', className)}>
      {children}
    </div>
  )
}

export function CardTitle({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const { theme } = useTheme()
  return (
    <h3 className={cn(
      'text-lg font-semibold',
      theme === 'dark' ? 'text-primary-300' : 'text-primary-400',
      className
    )}>
      {children}
    </h3>
  )
}

export function CardContent({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  )
}

