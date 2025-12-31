'use client'

import { useTheme } from './ThemeProvider'
import { HiSun, HiMoon } from 'react-icons/hi2'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className={`fixed top-4 right-4 z-50 p-3 rounded-full transition-all duration-200 shadow-lg ${
        theme === 'dark' 
          ? 'bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20' 
          : 'bg-gray-800/10 hover:bg-gray-800/20 backdrop-blur-sm border border-gray-300'
      }`}
      aria-label="Toggle theme"
      suppressHydrationWarning
    >
      {theme === 'dark' ? (
        <HiSun className="w-5 h-5 text-white" />
      ) : (
        <HiMoon className="w-5 h-5 text-gray-700" />
      )}
    </button>
  )
}

