import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

type Theme = 'dark' | 'light'
interface ThemeContextValue { theme: Theme; toggleTheme: () => void; setTheme: (theme: Theme) => void }
const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    try { return localStorage.getItem('pd-bank-theme') === 'light' ? 'light' : 'dark' } catch { return 'dark' }
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.classList.toggle('theme-light', theme === 'light')
    try { localStorage.setItem('pd-bank-theme', theme) } catch { /* Preferência continua válida na sessão. */ }
  }, [theme])
  const value = useMemo(() => ({ theme, setTheme, toggleTheme: () => setTheme(current => current === 'dark' ? 'light' : 'dark') }), [theme])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme deve ser usado dentro de ThemeProvider.')
  return context
}
