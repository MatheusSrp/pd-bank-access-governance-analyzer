import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, AlertOctagon, ArrowRight, Database, FileClock, ShieldAlert, Sparkles } from 'lucide-react'
import { listAnalyses, getAnalysis } from '../api/analyses'
import { listDatasets } from '../api/datasets'
import { listFindings } from '../api/findings'
import { getIndicators } from '../api/indicators'
import type { AnalysisRecord, DatasetRecord, FindingRecord } from '../api/types'
import { ChartsOverview } from '../components/dashboard/ChartsOverview'
import { RuleCoverage, coverageEntries } from '../components/dashboard/RuleCoverage'
import { StatCard } from '../components/dashboard/StatCard'
import { FindingsTable } from '../components/tables/FindingsTable'
import { Button, PageHeader } from '../components/ui'
import { asObject, countMap, datasetName, formatDate, numericMetric } from '../lib/format'

interface DashboardData { datasets: DatasetRecord[]; analyses: AnalysisRecord[]; findings: FindingRecord[]; totalFindings: number; indicators: Record<string, unknown>; datasetsAvailable: boolean; analysesAvailable: boolean; latest?: AnalysisRecord; latestDetail?: AnalysisRecord }
function distributions(sources: unknown[], keys: string[]) {
  for (const source of sources) {
    const result = countMap(source, keys)
    if (result.length) return result
  }
  return []
}
function metric(sources: unknown[], keys: string[]) {
  for (const source of sources) {
    const value = numericMetric(source, keys)
    if (value !== null) return value
  }
  return null
}
function sortedAnalyses(items: AnalysisRecord[]) {
  return [...items].sort((a, b) => {
    const aDate = new Date(String(a.executed_at ?? a.created_at ?? '')).getTime()
    const bDate = new Date(String(b.executed_at ?? b.created_at ?? '')).getTime()
    if (!Number.isFinite(aDate) || !Number.isFinite(bDate)) return 0
    return bDate - aDate
  })
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let alive = true
    async function load() {
      setLoading(true); setError(null)
      const results = await Promise.allSettled([listDatasets(), listAnalyses(), getIndicators(), listFindings({ limit: 8, offset: 0 })])
      if (!alive) return
      const errors = results.flatMap(result => result.status === 'rejected' ? [result.reason] : [])
      const datasets = results[0].status === 'fulfilled' ? results[0].value : []
      const analyses = results[1].status === 'fulfilled' ? sortedAnalyses(results[1].value) : []
      const indicators = results[2].status === 'fulfilled' ? results[2].value : {}
      const findingPage = results[3].status === 'fulfilled' ? results[3].value : { items: [], total: 0 }
      const latest = analyses[0]
      let latestDetail: AnalysisRecord | undefined
      if (latest) {
        try { latestDetail = await getAnalysis(latest.id) } catch { latestDetail = undefined }
      }
      if (!alive) return
      setData({ datasets, analyses, findings: findingPage.items, totalFindings: findingPage.total, indicators, datasetsAvailable: results[0].status === 'fulfilled', analysesAvailable: results[1].status === 'fulfilled', latest, latestDetail })
      if (errors.length) setError(errors[0] instanceof Error ? errors[0].message : 'Não foi possível carregar todos os dados do painel.')
      setLoading(false)
    }
    void load()
    return () => { alive = false }
  }, [])

  const chartData = useMemo(() => {
    const sources = [data?.indicators, data?.latestDetail?.summary, data?.latest?.summary]
    const root = asObject(data?.indicators)
    const summary = asObject(root?.summary)
    return {
      severity: distributions([summary, ...sources], ['findings_by_severity', 'by_severity', 'severity_distribution', 'severity']),
      domains: distributions([summary, ...sources], ['findings_by_domain', 'by_domain', 'domain_distribution', 'domains']),
      rules: distributions([summary, ...sources], ['findings_by_rule', 'by_rule', 'rule_distribution', 'rules']),
      statuses: distributions([summary, ...sources], ['findings_by_status', 'by_status', 'status_distribution', 'statuses']),
    }
  }, [data])
  const metricSources = [asObject(data?.indicators)?.summary, data?.indicators, data?.latestDetail?.summary, data?.latest?.summary]
  const critical = metric(metricSources, ['critical_findings', 'critical', 'findings_critical'])
  const high = metric(metricSources, ['high_findings', 'high', 'findings_high'])
  const expired = metric(metricSources, ['expired_exceptions', 'exceptions_expired', 'expired'])
  const coverage = coverageEntries(data?.latestDetail?.coverage ?? data?.latest?.coverage)
  const noAnalysis = Boolean(data && !loading && data.datasetsAvailable && data.analysesAvailable && data.datasets.length === 0 && data.analyses.length === 0)

  return <>
    <PageHeader eyebrow="CENTRO DE COMANDO · GOVERNANÇA" title="Visão Geral" description="Uma leitura executiva da postura de acesso, dados e inteligência artificial da instituição."
      action={<Link to="/analyses/new"><Button><Activity size={15} /> Nova análise</Button></Link>} />
    {error && <div className="inline-error dashboard-error"><AlertOctagon size={17} /><p>{error}{data && ' Os demais dados disponíveis permanecem visíveis.'}</p></div>}
    {noAnalysis ? <section className="onboarding-card card">
      <div className="onboarding-art"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="onboarding-shield"><ShieldAlert size={32} /></div><span className="orbit-dot dot-a" /><span className="orbit-dot dot-b" /><span className="orbit-dot dot-c" /></div>
      <div className="onboarding-copy"><p className="eyebrow">COMECE PELA SUA BASE</p><h2>Nenhuma análise realizada</h2><p>Importe um dataset para iniciar a leitura de controles de acesso, proteção de dados e governança de IA.</p><Link to="/datasets"><Button><Database size={15} /> Importar primeiro dataset <ArrowRight size={15} /></Button></Link><span>Formatos aceitos: XLSX, CSV e ZIP · até 50 MB</span></div>
    </section> : <>
      <section className="welcome-strip">
        <div className="welcome-mark"><Sparkles size={17} /></div><div><strong>Inteligência de governança em um só lugar</strong><span>{data?.latest ? `Última análise: ${formatDate(data.latest.executed_at ?? data.latest.created_at)}` : 'Sem análises registradas no momento.'}</span></div>
        {data?.latest && <Link to={`/analyses/${data.latest.id}`}>Ver análise <ArrowRight size={14} /></Link>}
      </section>
      <div className="stats-grid">
        <StatCard label="Total de datasets" value={data?.datasets.length ?? null} description="Bases importadas" icon={Database} tone="cyan" />
        <StatCard label="Análises executadas" value={data?.analyses.length ?? null} description="Execuções registradas" icon={Activity} tone="brand" />
        <StatCard label="Total de achados" value={data ? data.totalFindings : null} description="Resultados retornados pela API" icon={FileClock} tone="violet" />
        <StatCard label="Achados críticos" value={critical} description="Severidade crítica" icon={ShieldAlert} tone="critical" />
        <StatCard label="Alta severidade" value={high} description="Severidade alta" icon={AlertOctagon} tone="warning" />
        <StatCard label="Exceções expiradas" value={expired} description="Exceções fora da validade" icon={AlertOctagon} tone="critical" />
      </div>
      <ChartsOverview {...chartData} />
      <div className="dashboard-lower-grid">
        <section className="card recent-card"><div className="card-header"><div><h2 className="card-title">Achados recentes</h2><p className="card-subtitle">Registros mais recentes retornados pela API</p></div><Link className="subtle-link" to="/findings">Explorar achados <ArrowRight size={13} /></Link></div><FindingsTable items={data?.findings ?? []} loading={loading} emptyTitle="Nenhum achado registrado" emptyDescription="A API não retornou achados para esta consulta." /></section>
        <section className="card coverage-card"><div className="card-header"><div><h2 className="card-title">Cobertura de regras</h2><p className="card-subtitle">Avaliação da análise mais recente</p></div><span className="coverage-label">R01–R09</span></div><div className="card-body"><RuleCoverage coverage={coverage} /></div></section>
      </div>
      {data?.latest && <div className="dashboard-meta"><span>Dataset mais recente: <strong>{datasetName(data.latest.dataset)}</strong></span><Link to="/analyses">Ver histórico <ArrowRight size={13} /></Link></div>}
    </>}
  </>
}
