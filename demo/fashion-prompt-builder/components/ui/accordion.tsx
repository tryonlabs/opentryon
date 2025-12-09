'use client'

import React, { useState, createContext, useContext } from 'react'
import { cn } from '@/lib/utils'

interface AccordionContextType {
  openItem: string | undefined
  setOpenItem: (value: string | undefined) => void
}

const AccordionContext = createContext<AccordionContextType | undefined>(undefined)

export function Accordion({
  children,
  defaultValue,
}: {
  children: React.ReactNode
  defaultValue?: string
}) {
  const [openItem, setOpenItem] = useState<string | undefined>(defaultValue)

  return (
    <AccordionContext.Provider value={{ openItem, setOpenItem }}>
      <div className="w-full">{children}</div>
    </AccordionContext.Provider>
  )
}

export function AccordionItem({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = useContext(AccordionContext)
  if (!context) throw new Error('AccordionItem must be used within Accordion')
  const { openItem } = context
  const isOpen = openItem === value

  return (
    <div className={cn('border-b border-neutral-200', className)}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { isOpen, value } as any)
        }
        return child
      })}
    </div>
  )
}

export function AccordionTrigger({
  children,
  isOpen,
  value,
  className,
}: {
  children: React.ReactNode
  isOpen: boolean
  value: string
  className?: string
}) {
  const context = useContext(AccordionContext)
  if (!context) throw new Error('AccordionTrigger must be used within Accordion')
  const { setOpenItem } = context

  return (
    <button
      onClick={() => setOpenItem(isOpen ? undefined : value)}
      className={cn(
        'flex w-full items-center justify-between py-4 text-left font-medium transition-all',
        'hover:text-primary-400',
        className
      )}
    >
      {children}
      <svg
        className={cn(
          'h-4 w-4 shrink-0 transition-transform duration-200',
          isOpen && 'rotate-180'
        )}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
}

export function AccordionContent({
  children,
  isOpen,
  className,
}: {
  children: React.ReactNode
  isOpen: boolean
  className?: string
}) {
  if (!isOpen) return null

  return (
    <div className={cn('pb-4 pt-0', className)}>
      {children}
    </div>
  )
}

