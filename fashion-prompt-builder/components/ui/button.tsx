import { cn } from '@/lib/utils'

export function Button({
  children,
  variant = 'primary',
  className,
  ...props
}: {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline'
  className?: string
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const variants = {
    primary: 'bg-primary-400 text-white hover:bg-primary-500',
    secondary: 'bg-secondary-500 text-white hover:bg-secondary-600',
    outline: 'border-2 border-primary-400 text-primary-400 hover:bg-primary-50',
  }

  return (
    <button
      className={cn(
        'px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

