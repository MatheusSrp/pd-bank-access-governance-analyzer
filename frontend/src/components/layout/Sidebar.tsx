import { NavLink } from 'react-router-dom'
import { Activity, BrainCircuit, ChevronLeft, Database, FileBarChart2, FileClock, LayoutDashboard, LockKeyhole, PanelLeftClose, PanelLeftOpen, Settings2, ShieldCheck, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavigationItem { label: string; to: string; icon: LucideIcon; section?: string }
export const navigationItems: NavigationItem[] = [
  { label: 'Visão Geral', to: '/dashboard', icon: LayoutDashboard, section: 'Área de trabalho' },
  { label: 'Datasets', to: '/datasets', icon: Database },
  { label: 'Nova Análise', to: '/analyses/new', icon: Activity },
  { label: 'Histórico', to: '/analyses', icon: FileClock, section: 'Investigações' },
  { label: 'Achados', to: '/findings', icon: ShieldCheck },
  { label: 'Governança de Acessos', to: '/governance/access', icon: LockKeyhole, section: 'Domínios' },
  { label: 'Proteção de Dados', to: '/governance/data', icon: FileBarChart2 },
  { label: 'Governança de IA', to: '/governance/ai', icon: BrainCircuit },
  { label: 'Relatórios', to: '/reports', icon: FileBarChart2, section: 'Sistema' },
  { label: 'Configurações', to: '/settings', icon: Settings2 },
]

interface SidebarProps { collapsed: boolean; onToggle: () => void; mobileOpen: boolean; onCloseMobile: () => void }
export function Sidebar({ collapsed, onToggle, mobileOpen, onCloseMobile }: SidebarProps) {
  return <>
    {mobileOpen && <button className="mobile-scrim" aria-label="Fechar navegação" onClick={onCloseMobile} />}
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`} aria-label="Navegação principal">
      <div className="brand-row">
        <NavLink to="/dashboard" className="brand-lockup" aria-label="PD Bank — Visão Geral" onClick={onCloseMobile}>
          <span className="brand-symbol"><span>PD</span></span>
          {!collapsed && <span className="brand-words"><strong>PD Bank</strong><small>INTELIGÊNCIA DE GOVERNANÇA</small></span>}
        </NavLink>
        <button className="icon-button mobile-close" aria-label="Fechar menu" onClick={onCloseMobile}><X size={18} /></button>
      </div>
      <div className="workspace-switcher">
        <span className="workspace-mark"><ShieldCheck size={16} /></span>
        {!collapsed && <span><small>AMBIENTE</small><strong>Governança</strong></span>}
        {!collapsed && <ChevronLeft className="workspace-chevron" size={15} />}
      </div>
      <nav className="side-navigation">
        {navigationItems.map(item => {
          const Icon = item.icon
          return <div key={item.to}>
            {item.section && <div className="nav-section-label">{collapsed ? <span className="nav-divider" /> : item.section}</div>}
            <NavLink to={item.to} end={item.to === '/dashboard' || item.to === '/analyses'} onClick={onCloseMobile}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              title={collapsed ? item.label : undefined} aria-label={collapsed ? item.label : undefined}>
              <Icon size={18} strokeWidth={1.8} /><span className="nav-link-label">{item.label}</span>
            </NavLink>
          </div>
        })}
      </nav>
      <div className="sidebar-bottom">
        <button className="collapse-control" onClick={onToggle} aria-label={collapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}>
          {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}{!collapsed && <span>Recolher menu</span>}
        </button>
      </div>
    </aside>
  </>
}
