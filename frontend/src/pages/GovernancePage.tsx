import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { BrainCircuit, Database, LockKeyhole, ShieldCheck } from 'lucide-react'
import { getRules } from '../api/indicators'
import { listFindings } from '../api/findings'
import type { FindingRecord, RuleRecord } from '../api/types'
import { FindingsTable } from '../components/tables/FindingsTable'
import { Badge, EmptyState, PageHeader } from '../components/ui'
import { formatNumber } from '../lib/format'

const views = {
  access: { title: 'Governança de Acessos', eyebrow: 'IDENTIDADE · RBAC · SoD', description: 'Investigue desvios de RBAC, conflitos de segregação de funções, contas inativas com acesso e revisões de acesso.', icon: LockKeyhole, focus: ['Desvios de RBAC', 'Conflitos de SoD', 'Acessos de identidades inativas', 'Revisões de acesso'] },
  data: { title: 'Proteção de Dados', eyebrow: 'CLASSIFICAÇÃO · COMPARTILHAMENTO', description: 'Analise classificação, ownership, compartilhamento, retenção e controles de proteção de dados.', icon: Database, focus: ['Classificação', 'Ownership', 'Compartilhamento', 'Retenção e proteção'] },
  ai: { title: 'Governança de IA', eyebrow: 'CONTROLES · SUPERVISÃO HUMANA', description: 'Acompanhe guardrails, controles de IA, supervisão humana e níveis de autonomia identificados.', icon: BrainCircuit, focus: ['Guardrails ausentes', 'Controles de IA', 'Supervisão humana', 'Autonomia'] },
}
type ViewKey = keyof typeof views

export function GovernancePage({ kind }: { kind: ViewKey }) {
  const view = views[kind]
  const [params, setParams] = useSearchParams()
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [domainOptions, setDomainOptions] = useState<string[]>([])
  const [domain, setDomain] = useState(params.get('domain') ?? '')
  const [items, setItems] = useState<FindingRecord[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let alive = true
    Promise.all([getRules(), listFindings({ limit: 100, offset: 0 })]).then(([catalog, findings]) => {
      if (!alive) return
      setRules(catalog)
      const names = new Set<string>()
      catalog.forEach(rule => { if (rule.domain) names.add(rule.domain) })
      findings.items.forEach(finding => { if (finding.domain) names.add(finding.domain) })
      const available = Array.from(names).sort((a, b) => a.localeCompare(b, 'pt-BR'))
      setDomainOptions(available)
      setDomain(current => current || params.get('domain') || '')
    }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível consultar o catálogo de regras.') }).finally(() => { if (alive) setCatalogLoading(false) })
    return () => { alive = false }
  }, [])
  useEffect(() => {
    let alive = true
    setLoading(true)
    listFindings({ domain, limit: 20, offset: 0 }).then(result => { if (alive) { setItems(result.items); setTotal(result.total) } }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar os achados deste domínio.') }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [domain])
  useEffect(() => { if (domain) setParams({ domain }, { replace: true }) }, [domain])
  const Icon = view.icon
  const ruleCount = useMemo(() => rules.filter(rule => !domain || rule.domain === domain).length, [rules, domain])

  return <>
    <PageHeader eyebrow={view.eyebrow} title={view.title} description={view.description} action={<Badge tone="brand"><ShieldCheck size={12} /> Domínio analítico</Badge>} />
    {error && <div className="inline-error page-alert">{error}</div>}
    <div className="governance-intro card"><div className="governance-mark"><Icon size={21} /></div><div><span className="eyebrow">FOCOS DE INVESTIGAÇÃO</span><p>{view.focus.join(' · ')}</p></div><Link to="/findings">Abrir explorador geral</Link></div>
    <section className="card governance-domains-card"><div className="card-header"><div><h2 className="card-title">Domínios informados pela API</h2><p className="card-subtitle">Selecione uma opção retornada pelo catálogo de regras ou pelos achados. Nenhuma regra de classificação é presumida.</p></div><span className="dataset-count"><Database size={14} /> {catalogLoading ? '—' : domainOptions.length}</span></div>
      <div className="domain-chip-list"><button className={`domain-chip ${!domain ? 'domain-chip-active' : ''}`} onClick={() => setDomain('')}>Todos os domínios</button>{domainOptions.map(name => <button key={name} className={`domain-chip ${domain === name ? 'domain-chip-active' : ''}`} onClick={() => setDomain(name)}>{name}<span>{rules.filter(rule => rule.domain === name).length}</span></button>)}</div>
      {domainOptions.length === 0 && !catalogLoading && <div className="card-body"><EmptyState title="Catálogo sem domínios" description="A API de regras e os achados consultados não informaram domínios para filtrar." /></div>}
    </section>
    <div className="governance-kpis"><section className="card governance-kpi"><span>Domínio selecionado</span><strong>{domain || 'Todos'}</strong></section><section className="card governance-kpi"><span>Regras no catálogo</span><strong>{ruleCount.toLocaleString('pt-BR')}</strong></section><section className="card governance-kpi"><span>Achados encontrados</span><strong>{loading ? '—' : formatNumber(total)}</strong></section></div>
    <section className="card governance-findings"><div className="card-header"><div><h2 className="card-title">Achados de governança</h2><p className="card-subtitle">Resultados filtrados no backend por domínio</p></div><Link className="subtle-link" to={`/findings${domain ? `?domain=${encodeURIComponent(domain)}` : ''}`}>Ver filtros avançados</Link></div><FindingsTable items={items} loading={loading} emptyTitle={domain ? 'Nenhum achado neste domínio' : 'Nenhum achado encontrado'} emptyDescription="A consulta usa apenas os registros retornados pelo backend." /></section>
    {!catalogLoading && domainOptions.length > 0 && <div className="callout governance-callout"><Icon size={16} /><span>Os domínios acima foram derivados das respostas reais do endpoint de regras e dos achados. A associação entre regra e domínio é a declarada pela própria API.</span></div>}
  </>
}
