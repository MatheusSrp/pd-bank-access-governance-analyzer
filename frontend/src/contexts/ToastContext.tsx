import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react'

type ToastKind = 'success' | 'error' | 'info'
interface ToastMessage { id: number; title: string; message?: string; kind: ToastKind }
interface ToastContextValue { notify: (title: string, message?: string, kind?: ToastKind) => void }
const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastMessage[]>([])
  const dismiss = useCallback((id: number) => setItems(current => current.filter(item => item.id !== id)), [])
  const notify = useCallback((title: string, message?: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.random()
    setItems(current => [...current, { id, title, message, kind }])
    window.setTimeout(() => dismiss(id), 5200)
  }, [dismiss])
  const value = useMemo(() => ({ notify }), [notify])
  return <ToastContext.Provider value={value}>
    {children}
    <div className="toast-stack" aria-live="polite" aria-relevant="additions">
      {items.map(item => {
        const Icon = item.kind === 'success' ? CheckCircle2 : item.kind === 'error' ? AlertCircle : Info
        return <div className={`toast toast-${item.kind}`} key={item.id} role={item.kind === 'error' ? 'alert' : 'status'}>
          <Icon size={18} aria-hidden="true" />
          <div><strong>{item.title}</strong>{item.message && <p>{item.message}</p>}</div>
          <button className="icon-button toast-close" aria-label="Dispensar notificação" onClick={() => dismiss(item.id)}><X size={15} /></button>
        </div>
      })}
    </div>
  </ToastContext.Provider>
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast deve ser usado dentro de ToastProvider.')
  return context
}
