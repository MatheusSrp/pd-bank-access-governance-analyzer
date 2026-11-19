import { useEffect, useState } from 'react'
import { FileJson, FileSpreadsheet, FileText, ShieldCheck } from 'lucide-react'
import { exportAnalysis, getAnalysis, listAnalyses } from '../api/analyses'
import type { AnalysisRecord } from '../api/types'
import { useToast } from '../contexts/ToastContext'
import { displayValue, formatDate, formatNumber, statusLabel } from '../lib/format'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

export function ReportsPage() {
  const { notify } = useToast()
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([])
  const [selected, setSelected] = useState('')
  const [detail, setDetail] = useState<AnalysisRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState<string | null>(null)
  useEffect(() => { listAnalyses().then(items => { setAnalyses(items); if (items[0]) setSelected(String(items[0].id)) }).catch(err => setError(err instanceof Error ? err.message : 'Não foi possível carregar análises.')).finally(() => setLoading(false)) }, [])
  useEffect(() => {
    if (!selected) { setDetail(null); return }
    let alive = true
    setDetailLoading(true)
    getAnalysis(selected).then(item => { if (alive) setDetail(item) }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar o resumo da análise.') }).finally(() => { if (alive) setDetailLoading(false) })
    return () => { alive = false }
  }, [selected])
  async function handleExport(format: 'json' | 'csv') {
    if (!selected) return
    setExporting(format)
    try { await exportAnalysis(selected, format); notify('Exportação solicitada', `A API retornou o arquivo ${format.toUpperCase()}.`, 'success') }
    catch (err) { notify('Falha na exportação', err instanceof Error ? err.message : 'Não foi possível exportar.', 'error') }
    finally { setExporting(null) }
  }
  return <>
    <PageHeader eyebrow="DISTRIBUIÇÃO E AUDITORIA" title="Relatórios" description="Revise o resumo de uma execução e exporte resultados nos formatos disponibilizados pelo backend." />
    {error && <div className="inline-error page-alert">{error}</div>}
    {loading ? <section className="card reports-skeleton"><Skeleton /><Skeleton /><Skeleton /></section> : analyses.length === 0 ? <section className="card"><EmptyState title="Nenhuma análise disponível" description="Execute uma análise antes de preparar uma exportação." /></section> : <div className="reports-layout">
      <section className="card report-selector"><div className="card-header"><div><h2 className="card-title">Selecionar análise</h2><p className="card-subtitle">Escolha uma execução retornada pela API.</p></div><span className="report-icon"><FileText size={17} /></span></div><div className="card-body"><div className="form-field"><label htmlFor="report-analysis">Análise</label><select id="report-analysis" className="select" value={selected} onChange={event => setSelected(event.target.value)}>{analyses.map(item => <option value={String(item.id)} key={item.id}>#{item.id} · {formatDate(item.executed_at ?? item.created_at)}</option>)}</select></div>
        <div className="report-assurance"><ShieldCheck size={17} /><span>O arquivo é solicitado ao endpoint de exportação da análise selecionada. Nenhum relatório é montado com dados inventados.</span></div>
        <div className="report-actions"><Button className="button-full" disabled={detailLoading || exporting !== null} onClick={() => void handleExport('json')}><FileJson size={15} /> {exporting === 'json' ? 'Exportando JSON…' : 'Exportar JSON'}</Button><Button variant="secondary" className="button-full" disabled={detailLoading || exporting !== null} onClick={() => void handleExport('csv')}><FileSpreadsheet size={15} /> {exporting === 'csv' ? 'Exportando CSV…' : 'Exportar CSV'}</Button></div>
      </div></section>
      <section className="card report-preview"><div className="card-header"><div><h2 className="card-title">Resumo executivo</h2><p className="card-subtitle">Prévia baseada na resposta da análise.</p></div><Badge tone="brand">Análise {selected}</Badge></div><div className="card-body">{detailLoading ? <div className="analysis-skeleton"><Skeleton /><Skeleton /><Skeleton /></div> : detail ? <><div className="report-preview-lead"><span>Status</span><Badge tone={detail.status === 'completed' ? 'success' : 'neutral'}>{statusLabel(detail.status)}</Badge><p>{displayValue(detail.summary?.executive_summary ?? detail.summary?.summary ?? detail.summary?.overview, 'A API não retornou um resumo textual para esta análise.')}</p></div><dl className="report-facts"><div><dt>Executada em</dt><dd>{formatDate(detail.executed_at ?? detail.created_at)}</dd></div><div><dt>Dataset</dt><dd>{displayValue(detail.dataset?.name ?? detail.dataset?.filename ?? detail.dataset_id)}</dd></div><div><dt>Total de achados</dt><dd>{formatNumber(detail.summary?.total_findings)}</dd></div><div><dt>Achados críticos</dt><dd>{formatNumber(detail.summary?.critical_findings)}</dd></div><div><dt>Data de referência</dt><dd>{detail.reference_date ? formatDate(detail.reference_date) : 'Não informada'}</dd></div></dl><div className="pdf-future-note"><FileText size={16} /><span>PDF não está disponível no contrato atual da API. A interface não oferece uma exportação PDF fictícia.</span></div></> : <EmptyState title="Prévia indisponível" description="A API não retornou os detalhes desta análise." />}</div></section>
    </div>}
  </>
}
