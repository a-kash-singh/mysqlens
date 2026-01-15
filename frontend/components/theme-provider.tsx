'use client'

import * as React from 'react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

interface ThemeProviderProps {
  children: React.ReactNode
  attribute?: string
  defaultTheme?: string
  enableSystem?: boolean
  disableTransitionOnChange?: boolean
}

export function ThemeProvider({ 
  children, 
  attribute, 
  defaultTheme, 
  enableSystem, 
  disableTransitionOnChange 
}: ThemeProviderProps) {
  const providerProps: Record<string, unknown> = {
    children,
  }
  
  if (attribute !== undefined) providerProps.attribute = attribute
  if (defaultTheme !== undefined) providerProps.defaultTheme = defaultTheme
  if (enableSystem !== undefined) providerProps.enableSystem = enableSystem
  if (disableTransitionOnChange !== undefined) providerProps.disableTransitionOnChange = disableTransitionOnChange

  return <NextThemesProvider {...providerProps} />
}
