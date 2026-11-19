import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowUpRight, CalendarDays, RefreshCw } from 'lucide-react'
import { listAnalyses } from '../api/analyses'
import type { AnalysisRecord } from '../api/types'
import { displayValue, formatDate, formatNumber, statusLabel } from '../lib/format'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

function statusTone(status?: string) { return status === 'completed' ? 'success' : status === 'failed' ? 'critical' : status === 'running' ? 'brand' : 'neutral' }
export function AnalysesPage() {
  const [items, setItems] = useState<AnalysisRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  async function load() { setLoading(true); setError(null); try { setItems(await listAnalyses()) } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível carregar o histórico.') } finally { setLoading(false) } }
  useEffect(() => { void load() }, [])
  return <>
    <PageHeader eyebrow="RASTREABILIDADE" title="Histórico de análises" description="Consulte as execuções retornadas pelo serviço de governança e abra seus resultados." action={<Link to="/analyses/new"><Button><Activity size={14} /> Nova análise</Button></Link>} />
    {error && <div className="inline-error page-alert">{error}</div>}
    <section className="card history-card">
      <div className="card-header"><div><h2 className="card-title">Execuções registradas</h2><p className="card-subtitle">Nenhum histórico é armazenado localmente pelo frontend.</p></div><Button variant="ghost" onClick={() => void load()}><RefreshCw size={14} /> Atualizar</Button></div>
      <div className="table-wrap"><table><thead><tr><th>ID da análise</th><th>Dataset</th><th>Executada em</th><th>Status</th><th>Achados</th><th>Críticos</th><th>Referência</th><th /></tr></thead><tbody>
        {loading ? Array.from({ length: 5 }, (_, row) => <tr key={row}>{Array.from({ length: 8 }, (_, cell) => <td key={cell}><Skeleton className="table-skeleton" /></td>)}</tr>) : items.map(item => <tr key={item.id}>
          <td><span className="rule-code">{item.id}</span></td><td>{displayValue(item.dataset_id ?? item.dataset?.id)}</td><td><span className="history-date"><CalendarDays size={13} />{formatDate(item.executed_at ?? item.created_at)}</span></td>
          <td><Badge tone={statusTone(item.status)}>{statusLabel(item.status)}</Badge></td><td>{formatNumber(item.summary?.total_findings)}</td><td>{formatNumber(item.summary?.critical_findings)}</td><td>{item.reference_date ? formatDate(item.reference_date) : '—'}</td>
          <td><Link className="row-action" to={`/analyses/${encodeURIComponent(String(item.id))}`} aria-label={`Ver análise ${item.id}`}><ArrowUpRight size={15} /></Link></td>
        </tr>)}</tbody></table>
        {!loading && items.length === 0 && !error && <EmptyState title="Nenhuma análise realizada" description="As análises concluídas no backend aparecerão neste histórico." action={<Link to="/analyses/new"><Button>Iniciar primeira análise</Button></Link>} />}
      </div>
    </section>
  </>
}
