import { download, request } from './client'
import { normalizeAnalysis } from './adapters'
import { asList } from './indicators'
import type { AnalysisRecord, EntityId } from './types'

export async function listAnalyses(): Promise<AnalysisRecord[]> {
  return asList<AnalysisRecord>(await request<unknown>('/api/analyses'), ['analyses']).map(normalizeAnalysis)
}

export function getAnalysis(id: EntityId): Promise<AnalysisRecord> {
  return request<AnalysisRecord>(`/api/analyses/${encodeURIComponent(String(id))}`).then(normalizeAnalysis)
}

export function runAnalysis(datasetId: EntityId, referenceDate?: string): Promise<AnalysisRecord> {
  return request<AnalysisRecord>('/api/analyses', {
    method: 'POST',
    body: referenceDate ? { dataset_id: Number(datasetId), reference_date: referenceDate } : { dataset_id: Number(datasetId) },
  }).then(normalizeAnalysis)
}

export function exportAnalysis(id: EntityId, format: 'json' | 'csv'): Promise<void> {
  return download(`/api/analyses/${encodeURIComponent(String(id))}/export?format=${format}`, `analise-${id}.${format}`)
}
