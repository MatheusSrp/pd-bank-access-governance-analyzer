import { useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ChevronRight, Menu, Moon, Search, Sun } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { navigationItems } from './Sidebar'

interface TopbarProps { connected: boolean | null; onMenu: () => void }
function pageTitle(path: string): string {
  if (path.startsWith('/findings/')) return 'Detalhe do achado'
  if (path.startsWith('/analyses/new')) return 'Nova Análise'
  if (path.startsWith('/analyses/')) return 'Detalhe da análise'
  return navigationItems.find(item => item.to === path)?.label ?? 'Visão Geral'
}

export function Topbar({ connected, onMenu }: TopbarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()
  const searchRef = useRef<HTMLInputElement>(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState(new URLSearchParams(location.search).get('q') || '')
  const title = pageTitle(location.pathname)
  function submitSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = search.trim()
    navigate(value ? `/findings?q=${encodeURIComponent(value)}` : '/findings')
    setSearchOpen(false)
  }
  function openMobileSearch() {
    if (!window.matchMedia('(max-width: 600px)').matches) return
    setSearchOpen(true)
    window.setTimeout(() => searchRef.current?.focus(), 0)
  }
  return <header className="topbar">
    <div className="topbar-left">
      <button className="icon-button mobile-menu-button" aria-label="Abrir menu de navegação" onClick={onMenu}><Menu size={19} /></button>
      <div className="breadcrumbs"><span>PD Bank</span><ChevronRight size={13} /><strong>{title}</strong></div>
      <h1 className="topbar-title">{title}</h1>
    </div>
    <div className="topbar-actions">
      <form className={`global-search ${searchOpen ? 'global-search-open' : ''}`} role="search" onSubmit={submitSearch} onClick={openMobileSearch}>
        <Search size={16} aria-hidden="true" /><input ref={searchRef} aria-label="Buscar achados por objeto" placeholder="Buscar objeto ou achado..." value={search} onChange={event => setSearch(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') { setSearchOpen(false); searchRef.current?.blur() } }} />
        <kbd>↵</kbd>
      </form>
      <div className={`connection-status ${connected === null ? 'connection-checking' : connected ? 'connection-online' : 'connection-offline'}`} role="status" title={connected === true ? 'API Flask conectada' : connected === false ? 'API Flask indisponível' : 'Verificando API Flask'}>
        <span className="connection-dot" /><span>{connected === null ? 'Verificando' : connected ? 'API conectada' : 'API desconectada'}</span>
      </div>
      <button className="icon-button topbar-icon" aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'} title={theme === 'dark' ? 'Tema claro' : 'Tema escuro'} onClick={toggleTheme}>
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>
      <div className="avatar" aria-label="Perfil visual, autenticação não implementada" title="Ambiente acadêmico"><span>PD</span></div>
    </div>
  </header>
}
