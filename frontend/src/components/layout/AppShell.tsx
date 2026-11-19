import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { useApiHealth } from '../../hooks/useApiHealth'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppShell() {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem('pd-bank-sidebar') === 'collapsed' } catch { return false }
  })
  const [mobileOpen, setMobileOpen] = useState(false)
  const connected = useApiHealth()
  function toggleSidebar() {
    setCollapsed(current => {
      const next = !current
      try { localStorage.setItem('pd-bank-sidebar', next ? 'collapsed' : 'expanded') } catch { /* Preferência apenas visual. */ }
      return next
    })
  }
  return <div className="app-shell">
    <Sidebar collapsed={collapsed} onToggle={toggleSidebar} mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
    <div className={`main-frame ${collapsed ? 'main-frame-collapsed' : ''}`}>
      <Topbar connected={connected} onMenu={() => setMobileOpen(true)} />
      <main className="page-content"><Outlet /></main>
      <footer className="app-footer"><span>PD Bank · Analisador de Acesso e Governança</span><span>Ambiente de análise · Dados fornecidos pela API Flask</span></footer>
    </div>
  </div>
}
