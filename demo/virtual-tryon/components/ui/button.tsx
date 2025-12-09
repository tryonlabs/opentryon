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
    primary: 'bg-primary-500 text-white hover:bg-primary-600',
    secondary: 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200',
    outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-50',
  }

  const shadowStyles = variant === 'primary' 
    ? { boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05), 0 1px 3px 0 rgb(0 0 0 / 0.1)' }
    : {}

  const hoverShadowStyles = variant === 'primary'
    ? { boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }
    : {}

  return (
    <button
      className={cn(
        'px-6 py-3 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        className
      )}
      style={shadowStyles}
      onMouseEnter={(e) => {
        if (variant === 'primary' && !props.disabled) {
          Object.assign(e.currentTarget.style, hoverShadowStyles)
        }
      }}
      onMouseLeave={(e) => {
        if (variant === 'primary') {
          Object.assign(e.currentTarget.style, shadowStyles)
        }
      }}
      {...props}
    >
      {children}
    </button>
  )
}

