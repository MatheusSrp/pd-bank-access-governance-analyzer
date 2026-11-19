import { useEffect, useState } from 'react'
import { Activity, CheckCircle2, CircleAlert, ExternalLink, Moon, Sun, Terminal } from 'lucide-react'
import { apiBaseUrl } from '../api/client'
import { getHealth, getRules } from '../api/indicators'
import type { ApiHealth, RuleRecord } from '../api/types'
import { useTheme } from '../contexts/ThemeContext'
import { displayValue } from '../lib/format'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

export function SettingsPage() {
  const { theme, toggleTheme } = useTheme()
  const [health, setHealth] = useState<ApiHealth | null>(null)
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  async function refresh() {
    setLoading(true); setError(null)
    const [healthResult, rulesResult] = await Promise.allSettled([getHealth(), getRules()])
    const failures: string[] = []
    if (healthResult.status === 'fulfilled') { setHealth(healthResult.value); setConnected(true) } else { setConnected(false); setError(healthResult.reason instanceof Error ? healthResult.reason.message : 'A API está indisponível.') }
    if (rulesResult.status === 'fulfilled') setRules(rulesResult.value)
    else failures.push(rulesResult.reason instanceof Error ? rulesResult.reason.message : 'Não foi possível consultar as regras.')
    if (healthResult.status === 'rejected') failures.unshift(healthResult.reason instanceof Error ? healthResult.reason.message : 'A API está indisponível.')
    setError(failures[0] ?? null)
    setLoading(false)
  }
  useEffect(() => { void refresh() }, [])
  const version = import.meta.env.VITE_APP_VERSION || '1.0.0'
  return <>
    <PageHeader eyebrow="PREFERÊNCIAS E SISTEMA" title="Configurações" description="Informações técnicas e preferências locais da interface. O backend permanece sob gestão do serviço Flask." action={<Button variant="secondary" onClick={() => void refresh()}><Activity size={14} /> Verificar conexão</Button>} />
    {error && <div className="inline-error page-alert">{error}</div>}
    <div className="settings-grid">
      <section className="card settings-card"><div className="card-header"><div><h2 className="card-title">Conexão com o backend</h2><p className="card-subtitle">Endpoint configurado no ambiente de execução</p></div><span className={`settings-status-icon ${connected === true ? 'status-ok' : connected === false ? 'status-error' : ''}`}>{connected ? <CheckCircle2 size={18} /> : <CircleAlert size={18} />}</span></div><div className="card-body"><div className="setting-row"><div><strong>URL da API</strong><span>VITE_API_BASE_URL</span></div><code className="api-url">{apiBaseUrl()}</code></div><div className="setting-row"><div><strong>Saúde do sistema</strong><span>GET /api/health</span></div>{loading ? <Skeleton className="setting-skeleton" /> : <Badge tone={connected ? 'success' : 'critical'}>{connected ? displayValue(health?.status, 'Conectado') : 'Indisponível'}</Badge>}</div><div className="setting-row"><div><strong>Serviço</strong><span>Informação reportada pela API</span></div><span>{displayValue(health?.service)}</span></div><div className="setting-row"><div><strong>Versão do backend</strong><span>Informação reportada pela API</span></div><span>{displayValue(health?.version)}</span></div></div></section>
      <section className="card settings-card"><div className="card-header"><div><h2 className="card-title">Aparência</h2><p className="card-subtitle">Preferência armazenada somente neste navegador</p></div></div><div className="card-body"><div className="theme-setting"><div className="theme-setting-icon">{theme === 'dark' ? <Moon size={17} /> : <Sun size={17} />}</div><div><strong>Tema {theme === 'dark' ? 'escuro' : 'claro'}</strong><span>O modo escuro é o padrão inicial.</span></div><Button variant="secondary" onClick={toggleTheme}>Alternar para {theme === 'dark' ? 'claro' : 'escuro'}</Button></div></div></section>
      <section className="card settings-card"><div className="card-header"><div><h2 className="card-title">Regras disponíveis</h2><p className="card-subtitle">Catálogo retornado pelo endpoint GET /api/rules</p></div><Badge tone="brand">{loading ? '—' : rules.length} regras</Badge></div><div className="card-body">{loading ? <div className="analysis-skeleton"><Skeleton /><Skeleton /><Skeleton /></div> : rules.length ? <div className="settings-rule-list">{rules.map((rule, index) => <div key={rule.rule_id ?? rule.id ?? index}><code>{rule.rule_id ?? rule.id ?? '—'}</code><span><strong>{rule.name ?? rule.title ?? 'Nome não informado'}</strong><small>{rule.description ?? 'Descrição não informada'}</small></span><Badge tone="neutral">{rule.domain ?? 'Domínio não informado'}</Badge></div>)}</div> : <EmptyState title="Catálogo indisponível" description="A API não retornou regras para apresentar." />}</div></section>
      <section className="card settings-card"><div className="card-header"><div><h2 className="card-title">Informações técnicas</h2><p className="card-subtitle">Configuração da interface em execução</p></div><Terminal size={17} className="settings-muted-icon" /></div><div className="card-body"><div className="setting-row"><div><strong>Aplicação</strong><span>PD Bank — Analisador de Acesso e Governança</span></div><Badge tone="neutral">v{version}</Badge></div><div className="setting-row"><div><strong>Aplicação web</strong><span>React + TypeScript + Vite</span></div><span>REST · JSON</span></div><div className="setting-row"><div><strong>Serviço de dados</strong><span>API Flask existente</span></div><a className="setting-link" href={apiBaseUrl()} target="_blank" rel="noreferrer">Abrir URL <ExternalLink size={12} /></a></div><p className="settings-disclaimer">A chave de API do navegador, quando configurada, não é um segredo seguro. Não use essa opção como autenticação de produção.</p></div></section>
    </div>
  </>
}
