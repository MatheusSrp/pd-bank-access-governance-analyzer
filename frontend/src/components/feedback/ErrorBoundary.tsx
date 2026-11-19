import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }
  static getDerivedStateFromError(): State { return { hasError: true } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Falha inesperada na interface:', error, info.componentStack) }
  render() {
    if (this.state.hasError) return <main className="fatal-state"><div className="fatal-card">
      <span className="fatal-icon"><AlertTriangle size={22} /></span>
      <p className="eyebrow">ERRO INESPERADO</p><h1>Não foi possível carregar esta tela</h1>
      <p>Ocorreu uma falha ao apresentar os dados. Tente recarregar a página.</p>
      <button className="button button-primary" onClick={() => window.location.reload()}><RefreshCw size={16} /> Recarregar página</button>
    </div></main>
    return this.props.children
  }
}
