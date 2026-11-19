import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ListFilter, RefreshCw, Search, X } from 'lucide-react'
import { listFindings } from '../api/findings'
import { getRules } from '../api/indicators'
import type { ExceptionStatus, FindingQuery, FindingRecord, FindingStatus, RuleRecord, Severity } from '../api/types'
import { Button, EmptyState, PageHeader, Skeleton } from '../components/ui'
import { displayValue, formatNumber, objectReference, severityLabel, statusLabel, exceptionLabel, evidenceText } from '../lib/format'
import { Badge } from '../components/ui'
import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'

const PAGE_SIZE = 20
const severities: Severity[] = ['critical', 'high', 'medium', 'low']
const statuses: FindingStatus[] = ['non_compliant', 'insufficient_information', 'valid_exception', 'compliant']
const exceptions: ExceptionStatus[] = ['none', 'valid', 'expired', 'future']
const severityTone: Record<string, string> = { critical: 'critical', high: 'high', medium: 'medium', low: 'low' }
const statusTone: Record<string, string> = { non_compliant: 'critical', insufficient_information: 'warning', valid_exception: 'violet', compliant: 'success' }

export function FindingsPage() {
  const [params, setParams] = useSearchParams()
  const [items, setItems] = useState<FindingRecord[]>([])
  const [total, setTotal] = useState(0)
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchDraft, setSearchDraft] = useState(params.get('q') ?? '')
  const [filters, setFilters] = useState({ severity: params.get('severity') ?? '', rule_id: params.get('rule_id') ?? '', domain: params.get('domain') ?? '', status: params.get('status') ?? '', exception_status: params.get('exception_status') ?? '', q: params.get('q') ?? '', analysis_id: params.get('analysis_id') ?? '' })
  const [page, setPage] = useState(0)
  useEffect(() => { getRules().then(setRules).catch(() => setRules([])) }, [])
  useEffect(() => { const timer = window.setTimeout(() => setFilters(current => ({ ...current, q: searchDraft })), 350); return () => window.clearTimeout(timer) }, [searchDraft])
  useEffect(() => {
    let alive = true
    setLoading(true); setError(null)
    const query: FindingQuery = { ...filters, severity: filters.severity as Severity | '', status: filters.status as FindingStatus | '', exception_status: filters.exception_status as ExceptionStatus | '', limit: PAGE_SIZE, offset: page * PAGE_SIZE }
    listFindings(query).then(result => { if (alive) { setItems(result.items); setTotal(result.total) } }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar os achados.') }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [filters, page])
  useEffect(() => {
    const next = new URLSearchParams()
    for (const [key, value] of Object.entries(filters)) if (value) next.set(key, value)
    if (params.toString() !== next.toString()) setParams(next, { replace: true })
  }, [filters])
  const domains = useMemo(() => Array.from(new Set(rules.map(rule => rule.domain).filter((domain): domain is string => typeof domain === 'string' && domain.trim() !== ''))).sort(), [rules])
  const maxPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1)
  function updateFilter(key: keyof typeof filters, value: string) { setPage(0); setFilters(current => ({ ...current, [key]: value })) }
  function clearFilters() { setSearchDraft(''); setPage(0); setFilters({ severity: '', rule_id: '', domain: '', status: '', exception_status: '', q: '', analysis_id: '' }) }
  const hasFilters = Object.values(filters).some(Boolean)

  return <>
    <PageHeader eyebrow="INVESTIGAÇÃO E EVIDÊNCIAS" title="Explorador de achados" description="Filtre os registros diretamente no backend e investigue evidências com rastreabilidade." />
    {error && <div className="inline-error page-alert">{error}</div>}
    <section className="card findings-explorer-card">
      <div className="explorer-toolbar"><div className="explorer-result-label"><ListFilter size={15} /><strong>{loading ? 'Consultando API…' : `${formatNumber(total)} achados`}</strong><span>retornados pelo filtro</span></div><Button variant="ghost" onClick={clearFilters} disabled={!hasFilters}><X size={13} /> Limpar filtros</Button></div>
      <div className="filter-bar">
        <div className="filter-control search-control"><label className="field-label" htmlFor="finding-search">Objeto ou evidência</label><div className="filter-search"><Search size={14} /><input id="finding-search" className="input" placeholder="Buscar referência do objeto…" value={searchDraft} onChange={event => setSearchDraft(event.target.value)} /></div></div>
        <div className="filter-control"><label className="field-label" htmlFor="filter-severity">Severidade</label><select id="filter-severity" className="select" value={filters.severity} onChange={event => updateFilter('severity', event.target.value)}><option value="">Todas</option>{severities.map(value => <option key={value} value={value}>{severityLabel(value)}</option>)}</select></div>
        <div className="filter-control"><label className="field-label" htmlFor="filter-rule">Regra</label><select id="filter-rule" className="select" value={filters.rule_id} onChange={event => updateFilter('rule_id', event.target.value)}><option value="">Todas</option>{rules.map((rule, index) => { const id = rule.rule_id ?? rule.id; return id ? <option key={`${id}-${index}`} value={id}>{id}{rule.name || rule.title ? ` · ${rule.name ?? rule.title}` : ''}</option> : null })}</select></div>
        <div className="filter-control"><label className="field-label" htmlFor="filter-domain">Domínio</label><select id="filter-domain" className="select" value={filters.domain} onChange={event => updateFilter('domain', event.target.value)}><option value="">Todos</option>{domains.map(value => <option key={value} value={value}>{value}</option>)}</select></div>
        <div className="filter-control"><label className="field-label" htmlFor="filter-status">Status</label><select id="filter-status" className="select" value={filters.status} onChange={event => updateFilter('status', event.target.value)}><option value="">Todos</option>{statuses.map(value => <option key={value} value={value}>{statusLabel(value)}</option>)}</select></div>
        <div className="filter-control"><label className="field-label" htmlFor="filter-exception">Exceção</label><select id="filter-exception" className="select" value={filters.exception_status} onChange={event => updateFilter('exception_status', event.target.value)}><option value="">Todas</option>{exceptions.map(value => <option key={value} value={value}>{exceptionLabel(value)}</option>)}</select></div>
      </div>
      {filters.analysis_id && <div className="active-analysis-filter">Filtro de análise: <strong>{filters.analysis_id}</strong><button onClick={() => updateFilter('analysis_id', '')} aria-label="Remover filtro de análise"><X size={13} /></button></div>}
      <div className="table-wrap"><table className="findings-data-table"><thead><tr><th>ID</th><th>Regra</th><th>Domínio</th><th>Severidade</th><th>Status</th><th>Objeto de referência</th><th>Resumo da evidência</th><th /></tr></thead><tbody>
        {loading ? Array.from({ length: 7 }, (_, row) => <tr key={row}>{Array.from({ length: 8 }, (_, column) => <td key={column}><Skeleton className="table-skeleton" /></td>)}</tr>) : items.map(item => <tr key={item.id}>
          <td><span className="rule-code">{item.id}</span></td><td><span className="rule-code">{displayValue(item.rule_id ?? item.rule)}</span></td><td>{displayValue(item.domain)}</td>
          <td><Badge tone={severityTone[String(item.severity)] ?? 'neutral'}>{severityLabel(item.severity)}</Badge></td><td><Badge tone={statusTone[String(item.status)] ?? 'neutral'}>{statusLabel(item.status)}</Badge></td>
          <td><span className="table-primary">{objectReference(item)}</span></td><td><span className="table-evidence">{evidenceText(item)}</span></td>
          <td><Link className="row-action" to={`/findings/${encodeURIComponent(String(item.id))}`} aria-label={`Inspecionar achado ${item.id}`}><ArrowUpRight size={15} /></Link></td>
        </tr>)}</tbody></table>
        {!loading && items.length === 0 && <EmptyState title={hasFilters ? 'Nenhum achado corresponde aos filtros' : 'Nenhum achado disponível'} description={hasFilters ? 'Ajuste ou limpe os filtros para consultar outros registros.' : 'Quando a API retornar achados, eles serão listados aqui.'} action={hasFilters ? <Button variant="secondary" onClick={clearFilters}>Limpar filtros</Button> : undefined} />}
      </div>
      <div className="pagination"><span>Exibindo {items.length ? page * PAGE_SIZE + 1 : 0}–{Math.min((page + 1) * PAGE_SIZE, total)} de {formatNumber(total)}</span><div className="pagination-actions"><Button variant="secondary" disabled={page === 0 || loading} onClick={() => setPage(current => current - 1)}>Anterior</Button><span>Página {page + 1} de {Math.max(1, maxPage + 1)}</span><Button variant="secondary" disabled={page >= maxPage || loading} onClick={() => setPage(current => current + 1)}>Próxima</Button><Button variant="ghost" onClick={() => { setLoading(true); setFilters(current => ({ ...current })) }}><RefreshCw size={13} /></Button></div></div>
    </section>
  </>
}
