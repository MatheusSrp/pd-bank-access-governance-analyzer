import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CalendarDays, CheckCircle2, Database, LoaderCircle, Play, ShieldCheck } from 'lucide-react'
import { listDatasets } from '../api/datasets'
import { runAnalysis } from '../api/analyses'
import type { DatasetRecord } from '../api/types'
import { useToast } from '../contexts/ToastContext'
import { datasetName, formatNumber } from '../lib/format'
import { Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

export function NewAnalysisPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { notify } = useToast()
  const [datasets, setDatasets] = useState<DatasetRecord[]>([])
  const [datasetId, setDatasetId] = useState(params.get('dataset') ?? '')
  const [referenceDate, setReferenceDate] = useState('')
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { listDatasets().then(setDatasets).catch(err => setError(err instanceof Error ? err.message : 'Não foi possível carregar datasets.')).finally(() => setLoading(false)) }, [])

  const selected = datasets.find(dataset => String(dataset.id) === datasetId)
  async function execute() {
    if (!selected || running) return
    setRunning(true); setError(null); setStep(3)
    try {
      const analysis = await runAnalysis(selected.id, referenceDate || undefined)
      if (analysis?.id === undefined || analysis?.id === null) throw new Error('A API concluiu a solicitação, mas não retornou o identificador da análise.')
      notify('Análise iniciada', 'O resultado foi retornado pelo backend Flask.', 'success')
      navigate(`/analyses/${encodeURIComponent(String(analysis.id))}`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Não foi possível executar a análise.'
      setError(message); setStep(2); notify('Falha ao executar análise', message, 'error')
    } finally { setRunning(false) }
  }

  return <>
    <PageHeader eyebrow="EXECUÇÃO CONTROLADA" title="Nova análise" description="Selecione uma base e revise os parâmetros antes de enviar a execução ao backend." />
    <div className="workflow-steps" aria-label="Etapas do fluxo de análise">
      {[['01', 'Dataset'], ['02', 'Revisão'], ['03', 'Execução']].map(([num, label], index) => <div key={num} className={`workflow-step ${step >= index + 1 ? 'workflow-step-active' : ''}`}><span>{step > index + 1 ? <CheckCircle2 size={15} /> : num}</span><strong>{label}</strong>{index < 2 && <i />}</div>)}
    </div>
    <div className="analysis-workspace">
      <section className="card analysis-config-card">
        <div className="card-header"><div><h2 className="card-title">Configuração da análise</h2><p className="card-subtitle">A execução aplica as regras de governança disponíveis no backend.</p></div><span className="config-shield"><ShieldCheck size={18} /></span></div>
        <div className="card-body">
          {error && step === 1 && <div className="inline-error"><span>{error}</span></div>}
          {loading ? <div className="analysis-skeleton"><Skeleton /><Skeleton /><Skeleton /></div> : datasets.length === 0 ? <EmptyState title="Nenhum dataset disponível" description="Importe um dataset antes de iniciar uma análise." action={<Button onClick={() => navigate('/datasets')}><Database size={14} /> Ir para datasets</Button>} /> : <>
            <div className="form-field"><label htmlFor="analysis-dataset">Dataset de origem</label><select id="analysis-dataset" className="select" value={datasetId} onChange={event => setDatasetId(event.target.value)}><option value="">Selecione um dataset importado</option>{datasets.map(dataset => <option key={dataset.id} value={String(dataset.id)}>{datasetName(dataset)} · ID {dataset.id}</option>)}</select><p className="form-help">{selected ? `${formatNumber(selected.record_count ?? selected.accepted_records)} registros informados pelo backend.` : 'A lista contém apenas datasets retornados pela API.'}</p></div>
            <div className="form-field reference-date-field"><label htmlFor="reference-date">Data de referência <span className="optional-label">OPCIONAL</span></label><div className="date-input-wrap"><CalendarDays size={15} /><input id="reference-date" className="input" type="date" value={referenceDate} onChange={event => setReferenceDate(event.target.value)} /></div><p className="form-help">Se informada, será enviada como `reference_date` para o endpoint de análise.</p></div>
            <div className="analysis-review-toggle"><span className="review-check"><CheckCircle2 size={17} /></span><div><strong>Revisão antes da execução</strong><p>O backend determina as regras e a lógica de análise. Nenhuma regra é executada no navegador.</p></div></div>
            <div className="analysis-actions"><Button variant="secondary" onClick={() => navigate('/datasets')}><ArrowLeft size={14} /> Voltar aos datasets</Button><Button disabled={!selected || running} onClick={() => setStep(2)}>Revisar configuração <ArrowRight size={14} /></Button></div>
          </>}
        </div>
      </section>
      <aside className="analysis-side-panel"><div className="card analysis-side-card"><p className="eyebrow">ANTES DE EXECUTAR</p><h3>Uma análise, dados verificáveis.</h3><p>O resultado será produzido pelo serviço Flask existente. A interface não simula resultados nem altera os dados da origem.</p><div className="side-fact"><Database size={15} /><span>Dataset selecionado</span><strong>{selected ? datasetName(selected) : '—'}</strong></div><div className="side-fact"><CalendarDays size={15} /><span>Data de referência</span><strong>{referenceDate || 'Não informada'}</strong></div></div></aside>
    </div>
    {step >= 2 && <div className="modal-backdrop" role="presentation"><div className="review-dialog card" role="dialog" aria-modal="true" aria-labelledby="review-title">
      <span className="review-modal-icon">{running ? <LoaderCircle className="spin" size={22} /> : <ShieldCheck size={22} />}</span><p className="eyebrow">{running ? 'EXECUÇÃO EM ANDAMENTO' : 'REVISÃO DA SOLICITAÇÃO'}</p><h2 id="review-title">{running ? 'Análise em execução' : 'Executar análise?'}</h2><p>{running ? 'Aguardando a resposta do backend Flask. Não há estimativa artificial de progresso.' : 'Esta solicitação será enviada à API Flask configurada.'}</p>
      <div className="review-summary"><span>Dataset<strong>{selected ? datasetName(selected) : '—'}</strong></span><span>Data de referência<strong>{referenceDate || 'Não informada'}</strong></span><span>Endpoint<strong>POST /api/analyses</strong></span></div>
      {error && <div className="inline-error">{error}</div>}
      {running ? <div className="execution-wait"><LoaderCircle className="spin" size={15} /> Aguardando retorno da API…</div> : <div className="analysis-actions"><Button variant="secondary" onClick={() => setStep(1)}>Voltar</Button><Button disabled={!selected} onClick={() => void execute()}><Play size={14} /> Confirmar execução</Button></div>}
    </div></div>}
  </>
}
