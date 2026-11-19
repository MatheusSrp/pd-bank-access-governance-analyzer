import { Fragment, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Check, ChevronDown, ChevronUp, Database, FileSpreadsheet, FileUp, LoaderCircle, Play, RefreshCw, UploadCloud } from 'lucide-react'
import { getDataset, importDataset, listDatasets, validateDataset } from '../api/datasets'
import type { DatasetRecord, ImportResult } from '../api/types'
import { useToast } from '../contexts/ToastContext'
import { datasetName, formatDate, formatNumber } from '../lib/format'
import { Badge, Button, EmptyState, PageHeader, Skeleton } from '../components/ui'

const MAX_SIZE = 50 * 1024 * 1024
const ACCEPTED = ['.xlsx', '.csv', '.zip']
function asRecord(value: unknown): Record<string, unknown> { return value && typeof value === 'object' ? value as Record<string, unknown> : {} }
function textList(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [] }
function resultList(result: ImportResult | null, keys: string[]): string[] {
  if (!result) return []
  for (const key of keys) {
    const direct = result[key]
    if (Array.isArray(direct)) return textList(direct)
    const nested = asRecord(result.validation)[key]
    if (Array.isArray(nested)) return textList(nested)
  }
  return []
}

export function DatasetsPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const { notify } = useToast()
  const [datasets, setDatasets] = useState<DatasetRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [validation, setValidation] = useState<ImportResult | null>(null)
  const [validating, setValidating] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [dragging, setDragging] = useState(false)
  const [expandedId, setExpandedId] = useState<string | number | null>(null)
  const [datasetDetail, setDatasetDetail] = useState<DatasetRecord | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  async function loadDatasets() {
    setLoading(true); setLoadError(null)
    try { setDatasets(await listDatasets()) } catch (error) { setLoadError(error instanceof Error ? error.message : 'Não foi possível carregar os datasets.') }
    finally { setLoading(false) }
  }
  useEffect(() => { void loadDatasets() }, [])

  async function selectFile(next: File | undefined) {
    if (!next) return
    setFileError(null); setValidation(null); setImportResult(null)
    const extension = `.${next.name.split('.').pop()?.toLowerCase()}`
    if (!ACCEPTED.includes(extension)) { setFile(null); setFileError('Formato não suportado. Selecione um arquivo XLSX, CSV ou ZIP.'); return }
    if (next.size > MAX_SIZE) { setFile(null); setFileError('O arquivo excede o limite máximo de 50 MB.'); return }
    setFile(next); setValidating(true)
    try { setValidation(await validateDataset(next)) }
    catch (error) { setFileError(error instanceof Error ? error.message : 'Não foi possível validar o arquivo.'); }
    finally { setValidating(false) }
  }

  async function handleImport() {
    if (!file || uploading || validating) return
    setUploading(true); setFileError(null)
    try {
      const result = await importDataset(file)
      setImportResult(result)
      notify('Dataset importado', 'A API confirmou a importação do arquivo.', 'success')
      setFile(null); setValidation(null)
      await loadDatasets()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Não foi possível importar o dataset.'
      setFileError(message); notify('Falha na importação', message, 'error')
    } finally { setUploading(false) }
  }

  async function toggleDetails(dataset: DatasetRecord) {
    if (expandedId === dataset.id) { setExpandedId(null); setDatasetDetail(null); return }
    setExpandedId(dataset.id); setDatasetDetail(null); setDetailLoading(true)
    try { setDatasetDetail(await getDataset(dataset.id)) }
    catch (error) { setDatasetDetail({ id: dataset.id, detail_error: error instanceof Error ? error.message : 'Não foi possível carregar detalhes.' }) }
    finally { setDetailLoading(false) }
  }

  const warnings = resultList(importResult ?? validation, ['warnings', 'validation_warnings'])
  const recognized = resultList(importResult ?? validation, ['recognized_sheets', 'sheets_recognized'])
  const unknown = resultList(importResult ?? validation, ['unknown_sheets', 'sheets_unknown'])
  const accepted = (importResult ?? validation)?.accepted_records
  const rejected = (importResult ?? validation)?.rejected_records
  const validationErrors = resultList(validation, ['errors', 'validation_errors'])

  return <>
    <PageHeader eyebrow="FONTES DE DADOS" title="Datasets" description="Gerencie as bases importadas que alimentam as análises de governança."
      action={<Button variant="secondary" onClick={() => void loadDatasets()}><RefreshCw size={14} /> Atualizar</Button>} />
    <div className="datasets-layout">
      <section className="card upload-card">
        <div className="card-header"><div><h2 className="card-title">Importar dataset</h2><p className="card-subtitle">Valide sua base antes de iniciar uma análise.</p></div><span className="upload-header-icon"><UploadCloud size={17} /></span></div>
        <div className="card-body">
          <button type="button" className={`dropzone ${dragging ? 'dropzone-active' : ''}`} onClick={() => inputRef.current?.click()}
            onDragOver={event => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); void selectFile(event.dataTransfer.files[0]) }} aria-label="Selecionar ou arrastar arquivo para upload">
            <span className="dropzone-icon"><FileUp size={22} /></span><strong>Arraste seu arquivo até aqui</strong><span>ou <em>selecione no computador</em></span>
            <small>XLSX · CSV · ZIP <i /> Limite 50 MB</small>
          </button>
          <input ref={inputRef} type="file" accept=".xlsx,.csv,.zip" className="visually-hidden" onChange={event => { void selectFile(event.target.files?.[0]); event.target.value = '' }} />
          {file && <div className="selected-file"><FileSpreadsheet size={17} /><div><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toLocaleString('pt-BR', { maximumFractionDigits: 2 })} MB</span></div><button className="icon-button" aria-label="Remover arquivo selecionado" onClick={() => { setFile(null); setValidation(null); setFileError(null) }}>×</button></div>}
          {fileError && <div className="inline-error upload-message"><AlertCircle size={15} /><p>{fileError}</p></div>}
          {validating && <div className="upload-progress"><LoaderCircle size={15} className="spin" /><span>Validando arquivo com a API…</span></div>}
          {file && validation && <div className="validation-panel">
            <div className="validation-title"><Check size={15} /><strong>Validação recebida</strong><span>Resposta do backend</span></div>
            {validationErrors.length > 0 && <div className="validation-list validation-errors"><strong>Erros</strong>{validationErrors.map((item, index) => <span key={index}>• {item}</span>)}</div>}
            {warnings.length > 0 && <div className="validation-list"><strong>Avisos</strong>{warnings.map((item, index) => <span key={index}>• {item}</span>)}</div>}
            <div className="validation-chips"><span>Planilhas reconhecidas <b>{recognized.length ? recognized.join(', ') : 'Não informado'}</b></span><span>Planilhas desconhecidas <b>{unknown.length ? unknown.join(', ') : 'Não informado'}</b></span></div>
            {(accepted !== undefined || rejected !== undefined) && <div className="validation-counts"><span>Registros aceitos <b>{formatNumber(accepted)}</b></span><span>Registros rejeitados <b>{formatNumber(rejected)}</b></span></div>}
          </div>}
          {importResult && <div className="import-success"><Check size={15} /><span>Importação concluída com retorno da API.</span></div>}
          <Button className="button-full import-button" disabled={!file || validating || uploading} onClick={() => void handleImport()}>
            {uploading ? <><LoaderCircle size={15} className="spin" /> Enviando arquivo…</> : <><UploadCloud size={15} /> Importar dataset</>}
          </Button>
          <p className="upload-note">O processamento é realizado pelo backend Flask. A interface não estima o progresso do envio.</p>
        </div>
      </section>

      <section className="card datasets-table-card">
        <div className="card-header"><div><h2 className="card-title">Datasets importados</h2><p className="card-subtitle">{loading ? 'Consultando API…' : `${datasets.length.toLocaleString('pt-BR')} registros retornados`}</p></div><span className="dataset-count"><Database size={14} /> {loading ? '—' : datasets.length}</span></div>
        {loadError && <div className="inline-error card-inline-error"><AlertCircle size={15} /><p>{loadError}</p></div>}
        <div className="table-wrap"><table><thead><tr><th>Dataset</th><th>Importado em</th><th>Registros</th><th>Validação</th><th>Ações</th></tr></thead><tbody>
          {loading ? Array.from({ length: 4 }, (_, index) => <tr key={index}>{Array.from({ length: 5 }, (_, column) => <td key={column}><Skeleton className="table-skeleton" /></td>)}</tr>) : datasets.map(dataset => <Fragment key={dataset.id}>
            <tr key={dataset.id}>
              <td><button className="dataset-name-button" onClick={() => void toggleDetails(dataset)} aria-expanded={expandedId === dataset.id}><span className="dataset-file-icon"><FileSpreadsheet size={15} /></span><span><strong>{datasetName(dataset)}</strong><small>ID {dataset.id}</small></span></button></td>
              <td>{formatDate(dataset.imported_at ?? dataset.created_at)}</td>
              <td>{formatNumber(dataset.record_count ?? dataset.accepted_records)}</td>
              <td><Badge tone="neutral">Importado</Badge></td>
              <td><div className="table-actions"><Link className="row-action" to={`/analyses/new?dataset=${encodeURIComponent(String(dataset.id))}`} title="Executar análise" aria-label={`Executar análise do dataset ${datasetName(dataset)}`}><Play size={14} /></Link><button className="row-action" onClick={() => void toggleDetails(dataset)} aria-label="Ver detalhes do dataset">{expandedId === dataset.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</button></div></td>
            </tr>
            {expandedId === dataset.id && <tr key={`${dataset.id}-detail`}><td colSpan={5}><div className="dataset-detail">
              {detailLoading ? <Skeleton className="detail-skeleton" /> : <><strong>Detalhes do dataset</strong><pre>{JSON.stringify(datasetDetail ?? dataset, null, 2)}</pre></>}
            </div></td></tr>}
          </Fragment>)}</tbody></table>
          {!loading && datasets.length === 0 && !loadError && <EmptyState title="Nenhum dataset importado" description="Importe uma base para começar a análise de governança." />}
        </div>
      </section>
    </div>
  </>
}
