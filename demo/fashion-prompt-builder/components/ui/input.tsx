import { cn } from '@/lib/utils'

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'w-full px-3 py-2 border border-neutral-300 rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'disabled:bg-neutral-100 disabled:cursor-not-allowed',
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
        'w-full px-3 py-2 border border-neutral-300 rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'disabled:bg-neutral-100 disabled:cursor-not-allowed',
        'resize-none',
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
        'w-full px-3 py-2 border border-neutral-300 rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent',
        'disabled:bg-neutral-100 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

