'use client'

import { ThemeProvider } from './ThemeProvider'
import { ThemeToggle } from './ThemeToggle'

export function ThemeWrapper({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <>
        <ThemeToggle />
        {children}
      </>
    </ThemeProvider>
  )
}

