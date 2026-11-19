import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import type { FindingRecord } from '../../api/types'
import { displayValue, evidenceText, objectReference, severityLabel, statusLabel } from '../../lib/format'
import { Badge, EmptyState, Skeleton } from '../ui'

const toneForSeverity: Record<string, string> = { critical: 'critical', high: 'high', medium: 'medium', low: 'low' }
const toneForStatus: Record<string, string> = { non_compliant: 'critical', insufficient_information: 'warning', valid_exception: 'violet', compliant: 'success' }

export function FindingsTable({ items, loading = false, emptyTitle = 'Nenhum achado encontrado', emptyDescription = 'Quando houver achados nas análises, eles aparecerão aqui.' }: { items: FindingRecord[]; loading?: boolean; emptyTitle?: string; emptyDescription?: string }) {
  return <div className="table-wrap"><table>
    <thead><tr><th>Regra</th><th>Domínio</th><th>Objeto</th><th>Severidade</th><th>Status</th><th>Descrição</th><th aria-label="Ações" /></tr></thead>
    <tbody>{loading ? Array.from({ length: 5 }, (_, index) => <tr key={index}>{Array.from({ length: 7 }, (_, cell) => <td key={cell}><Skeleton className="table-skeleton" /></td>)}</tr>) : items.map(item => <tr key={String(item.id)}>
      <td><span className="rule-code">{displayValue(item.rule_id ?? item.rule)}</span></td>
      <td><span className="table-domain">{displayValue(item.domain)}</span></td>
      <td><span className="table-primary">{objectReference(item)}</span><span className="table-secondary">{evidenceText(item)}</span></td>
      <td><Badge tone={toneForSeverity[String(item.severity)] || 'neutral'}>{severityLabel(item.severity)}</Badge></td>
      <td><Badge tone={toneForStatus[String(item.status)] || 'neutral'}>{statusLabel(item.status)}</Badge></td>
      <td><span className="table-description">{displayValue(item.description, evidenceText(item))}</span></td>
      <td><Link className="row-action" to={`/findings/${encodeURIComponent(String(item.id))}`} aria-label={`Inspecionar achado ${item.id}`} title="Inspecionar"><ArrowUpRight size={15} /></Link></td>
    </tr>)}</tbody>
  </table>
  {!loading && items.length === 0 && <EmptyState title={emptyTitle} description={emptyDescription} />}
  </div>
}
