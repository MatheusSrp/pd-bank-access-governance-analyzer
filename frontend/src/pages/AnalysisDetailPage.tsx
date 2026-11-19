import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowDownToLine, ArrowLeft, FileJson, FileSpreadsheet, RefreshCw } from 'lucide-react'
import { exportAnalysis, getAnalysis } from '../api/analyses'
import { getDataset } from '../api/datasets'
import { listFindings } from '../api/findings'
import type { AnalysisRecord, DatasetRecord, FindingRecord } from '../api/types'
import { useToast } from '../contexts/ToastContext'
import { asObject, countMap, datasetName, displayValue, formatDate, formatNumber, statusLabel } from '../lib/format'
import { ChartsOverview } from '../components/dashboard/ChartsOverview'
import { RuleCoverage, coverageEntries } from '../components/dashboard/RuleCoverage'
import { FindingsTable } from '../components/tables/FindingsTable'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

const PAGE_SIZE = 20
export function AnalysisDetailPage() {
  const { id = '' } = useParams()
  const { notify } = useToast()
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null)
  const [dataset, setDataset] = useState<DatasetRecord | null>(null)
  const [findings, setFindings] = useState<FindingRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [findingsLoading, setFindingsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<'json' | 'csv' | null>(null)

  useEffect(() => {
    let alive = true
    setLoading(true); setError(null)
    getAnalysis(id).then(async record => {
      if (!alive) return
      setAnalysis(record)
      if (record.dataset) setDataset(record.dataset)
      else if (record.dataset_id !== undefined) {
        try { const value = await getDataset(record.dataset_id); if (alive) setDataset(value) } catch { /* O detalhe da análise continua disponível mesmo sem associação expandida. */ }
      }
    }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar a análise.') }).finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [id])

  useEffect(() => {
    let alive = true
    setFindingsLoading(true)
    listFindings({ analysis_id: id, limit: PAGE_SIZE, offset: page * PAGE_SIZE }).then(result => { if (alive) { setFindings(result.items); setTotal(result.total) } }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar os achados da análise.') }).finally(() => { if (alive) setFindingsLoading(false) })
    return () => { alive = false }
  }, [id, page])

  const summary = asObject(analysis?.summary)
  const charts = useMemo(() => ({
    severity: countMap(summary, ['by_severity', 'severity_distribution', 'findings_by_severity']),
    domains: countMap(summary, ['by_domain', 'domain_distribution', 'findings_by_domain']),
    rules: countMap(summary, ['by_rule', 'rule_distribution', 'findings_by_rule']),
    statuses: countMap(summary, ['by_status', 'status_distribution', 'findings_by_status']),
  }), [summary])
  async function handleExport(format: 'json' | 'csv') {
    setExporting(format)
    try { await exportAnalysis(id, format); notify('Exportação iniciada', `O arquivo ${format.toUpperCase()} foi solicitado à API.`, 'success') }
    catch (err) { notify('Falha na exportação', err instanceof Error ? err.message : 'Não foi possível exportar.', 'error') }
    finally { setExporting(null) }
  }
  const coverage = coverageEntries(analysis?.coverage)
  const maxPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1)
  const summaryFacts: Array<{ label: string; value: unknown }> = [
    { label: 'Total de achados', value: summary?.total_findings },
    { label: 'Críticos', value: summary?.critical_findings },
    { label: 'Alta severidade', value: summary?.high_findings },
    { label: 'Data de referência', value: analysis?.reference_date },
  ]

  if (loading) return <><PageHeader title="Detalhe da análise" description="Carregando informações retornadas pelo backend…" /><div className="detail-skeleton-grid"><Skeleton /><Skeleton /><Skeleton /></div></>
  if (error && !analysis) return <><PageHeader eyebrow="INVESTIGAÇÃO" title="Análise indisponível" /><div className="inline-error page-alert">{error}</div><Link to="/analyses"><Button variant="secondary"><ArrowLeft size={14} /> Voltar ao histórico</Button></Link></>

  return <>
    <PageHeader eyebrow={`ANÁLISE ${id}`} title="Resultado da análise" description={`Execução registrada ${formatDate(analysis?.executed_at ?? analysis?.created_at)} · referência ${analysis?.reference_date ? formatDate(analysis.reference_date) : 'não informada'}`}
      action={<div className="export-actions"><Button variant="secondary" disabled={exporting !== null} onClick={() => void handleExport('json')}><FileJson size={14} /> {exporting === 'json' ? 'Exportando…' : 'JSON'}</Button><Button variant="secondary" disabled={exporting !== null} onClick={() => void handleExport('csv')}><FileSpreadsheet size={14} /> {exporting === 'csv' ? 'Exportando…' : 'CSV'}</Button></div>} />
    {error && <div className="inline-error page-alert">{error}</div>}
    <section className="analysis-summary-banner card"><div className="summary-banner-mark"><RefreshCw size={18} /></div><div className="summary-banner-content"><span className="eyebrow">RESUMO EXECUTIVO</span><h2>{displayValue(summary?.executive_summary ?? summary?.summary ?? summary?.overview, 'Resumo não retornado pela API')}</h2><span>Análise <strong>{id}</strong> · Status <Badge tone="neutral">{statusLabel(analysis?.status)}</Badge></span></div><div className="summary-banner-metrics"><span><small>Achados</small><strong>{formatNumber(summary?.total_findings)}</strong></span><span><small>Críticos</small><strong className="critical-text">{formatNumber(summary?.critical_findings)}</strong></span><span><small>Alta severidade</small><strong className="warning-text">{formatNumber(summary?.high_findings)}</strong></span></div></section>
    <div className="analysis-meta-grid"><section className="card meta-card"><span>Dataset associado</span><strong>{dataset ? datasetName(dataset) : displayValue(analysis?.dataset_id)}</strong><small>ID {displayValue(dataset?.id ?? analysis?.dataset_id)}</small></section><section className="card meta-card"><span>Data de execução</span><strong>{formatDate(analysis?.executed_at ?? analysis?.created_at)}</strong><small>Data de referência: {analysis?.reference_date ? formatDate(analysis.reference_date) : 'não informada'}</small></section><section className="card meta-card"><span>Estado da execução</span><strong><Badge tone={analysis?.status === 'completed' ? 'success' : 'neutral'}>{statusLabel(analysis?.status)}</Badge></strong><small>Estado retornado pelo backend</small></section></div>
    <ChartsOverview {...charts} />
    <div className="analysis-detail-grid"><section className="card"><div className="card-header"><div><h2 className="card-title">Cobertura de regras</h2><p className="card-subtitle">Regras avaliadas e motivos de não avaliação</p></div><span className="coverage-label">R01–R09</span></div><div className="card-body"><RuleCoverage coverage={coverage} /></div></section>
      <section className="card analysis-facts"><div className="card-header"><div><h2 className="card-title">Resumo reportado</h2><p className="card-subtitle">Campos disponíveis na resposta da análise</p></div></div><div className="card-body"><dl>{summaryFacts.map(({ label, value }) => <div key={label}><dt>{label}</dt><dd>{label === 'Data de referência' ? (value ? formatDate(value) : '—') : formatNumber(value)}</dd></div>)}</dl></div></section></div>
    <section className="card findings-section"><div className="card-header"><div><h2 className="card-title">Achados associados</h2><p className="card-subtitle">{formatNumber(total)} resultados vinculados a esta análise, paginados pelo backend</p></div><Link className="subtle-link" to={`/findings?analysis_id=${encodeURIComponent(id)}`}>Abrir no explorador <ArrowDownToLine size={13} /></Link></div><FindingsTable items={findings} loading={findingsLoading} />
      {total > PAGE_SIZE && <div className="pagination"><span>Página {page + 1} de {maxPage + 1}</span><div className="pagination-actions"><Button variant="secondary" disabled={page === 0 || findingsLoading} onClick={() => setPage(current => current - 1)}>Anterior</Button><Button variant="secondary" disabled={page >= maxPage || findingsLoading} onClick={() => setPage(current => current + 1)}>Próxima</Button></div></div>}
      {!findingsLoading && total === 0 && !error && <EmptyState title="Nenhum achado associado" description="A API não retornou achados para esta análise." />}
    </section>
  </>
}
