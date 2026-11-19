import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Database, ExternalLink, FileSearch, Fingerprint, ShieldAlert } from 'lucide-react'
import { getFinding } from '../api/findings'
import type { FindingRecord } from '../api/types'
import { displayValue, evidenceText, exceptionLabel, objectReference, severityLabel, statusLabel } from '../lib/format'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

const severityTone: Record<string, string> = { critical: 'critical', high: 'high', medium: 'medium', low: 'low' }
const statusTone: Record<string, string> = { non_compliant: 'critical', insufficient_information: 'warning', valid_exception: 'violet', compliant: 'success' }
function SectionCard({ title, icon: Icon, children }: { title: string; icon: typeof ShieldAlert; children: React.ReactNode }) { return <section className="card investigation-section"><div className="investigation-section-heading"><span><Icon size={16} /></span><h2>{title}</h2></div><div className="investigation-section-content">{children}</div></section> }

export function FindingDetailPage() {
  const { id = '' } = useParams()
  const [finding, setFinding] = useState<FindingRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { let alive = true; setLoading(true); setError(null); getFinding(id).then(value => { if (alive) setFinding(value) }).catch(err => { if (alive) setError(err instanceof Error ? err.message : 'Não foi possível carregar o achado.') }).finally(() => { if (alive) setLoading(false) }); return () => { alive = false } }, [id])
  if (loading) return <><PageHeader title="Investigação do achado" /><div className="detail-skeleton-grid"><Skeleton /><Skeleton /><Skeleton /></div></>
  if (!finding) return <><PageHeader eyebrow="EVIDÊNCIA" title="Achado indisponível" /><div className="inline-error page-alert">{error ?? 'A API não retornou este achado.'}</div><Link to="/findings"><Button variant="secondary"><ArrowLeft size={14} /> Voltar aos achados</Button></Link></>

  const evidence = finding.evidence && typeof finding.evidence === 'object' ? JSON.stringify(finding.evidence, null, 2) : evidenceText(finding)
  return <>
    <div className="detail-back"><Link to="/findings"><ArrowLeft size={14} /> Voltar ao explorador</Link><span>Investigações <i>/</i> Achado {finding.id}</span></div>
    <PageHeader eyebrow={`ACHADO ${finding.id}`} title={displayValue(finding.description, `Investigação ${finding.id}`)} description="Evidências e contexto fornecidos pela análise de governança." action={<Badge tone={severityTone[String(finding.severity)] ?? 'neutral'}>{severityLabel(finding.severity)}</Badge>} />
    <div className="finding-overview card"><div className="finding-overview-id"><span className="finding-id-icon"><Fingerprint size={19} /></span><div><span>IDENTIFICADOR DO ACHADO</span><strong>{finding.id}</strong></div></div><div className="finding-overview-badges"><Badge tone={severityTone[String(finding.severity)] ?? 'neutral'}>{severityLabel(finding.severity)}</Badge><Badge tone={statusTone[String(finding.status)] ?? 'neutral'}>{statusLabel(finding.status)}</Badge></div><div className="finding-overview-rule"><small>REGRA</small><strong>{displayValue(finding.rule_id ?? finding.rule)}</strong></div></div>
    <div className="investigation-grid">
      <div className="investigation-main">
        <SectionCard title="Descrição e contexto" icon={FileSearch}><p className="investigation-description">{displayValue(finding.description, 'Descrição não informada pela API.')}</p><div className="investigation-facts"><div><small>Domínio de governança</small><strong>{displayValue(finding.domain)}</strong></div><div><small>Objeto afetado</small><strong>{objectReference(finding)}</strong></div><div><small>Status do achado</small><strong>{statusLabel(finding.status)}</strong></div></div></SectionCard>
        <SectionCard title="Evidência da análise" icon={Database}><p className="evidence-intro">Conteúdo da evidência retornado pela API, sem interpretação adicional no navegador.</p><pre className="evidence-block">{evidence}</pre></SectionCard>
        <SectionCard title="Risco e ação recomendada" icon={ShieldAlert}><div className="risk-detail"><div><small>IMPACTO POTENCIAL</small><p>{displayValue(finding.potential_impact, 'Impacto não informado pela API.')}</p></div><div><small>AÇÃO CORRETIVA RECOMENDADA</small><p>{displayValue(finding.recommended_action, 'Ação corretiva não informada pela API.')}</p></div></div></SectionCard>
      </div>
      <aside className="investigation-aside">
        <section className="card investigation-section"><div className="investigation-section-heading"><span><Database size={16} /></span><h2>Origem dos dados</h2></div><div className="investigation-section-content"><dl className="source-facts"><div><dt>Planilha</dt><dd>{displayValue(finding.source_sheet)}</dd></div><div><dt>Linha original</dt><dd>{displayValue(finding.source_row)}</dd></div><div><dt>Objeto de referência</dt><dd>{objectReference(finding)}</dd></div></dl></div></section>
        <section className="card investigation-section"><div className="investigation-section-heading"><span><ShieldAlert size={16} /></span><h2>Exceção</h2></div><div className="investigation-section-content"><Badge tone={finding.exception_status === 'expired' ? 'critical' : finding.exception_status === 'valid' ? 'success' : 'neutral'}>{exceptionLabel(finding.exception_status)}</Badge><p className="sidebar-detail-copy">Situação registrada na resposta do backend.</p></div></section>
        <section className="card investigation-section"><div className="investigation-section-heading"><span><Fingerprint size={16} /></span><h2>Análise associada</h2></div><div className="investigation-section-content">{finding.analysis_id !== undefined ? <><strong className="associated-id">{finding.analysis_id}</strong><Link className="subtle-link" to={`/analyses/${encodeURIComponent(String(finding.analysis_id))}`}>Abrir análise <ExternalLink size={13} /></Link></> : <EmptyState title="Vínculo não informado" description="A API não retornou o identificador da análise associada." />}</div></section>
        <div className="readonly-note">As ações de alteração de status e atribuição de revisores não estão disponíveis, pois não fazem parte do contrato da API.</div>
      </aside>
    </div>
  </>
}
