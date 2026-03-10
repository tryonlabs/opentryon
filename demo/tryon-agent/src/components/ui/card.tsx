'use client'

import { cn } from '../../lib/utils'

export function Card({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'rounded-lg border p-6 shadow-sm bg-[var(--card-bg)] border-[var(--border-primary)]',
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
  return (
    <h3 className={cn(
      'text-lg font-semibold text-[var(--primary-400)]',
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

