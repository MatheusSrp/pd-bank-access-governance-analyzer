import { request } from './client'
import { normalizeDataset, normalizeDatasetDetail, normalizeImport, normalizeValidation } from './adapters'
import { asList } from './indicators'
import type { DatasetRecord, ImportResult } from './types'

export async function listDatasets(): Promise<DatasetRecord[]> {
  return asList<DatasetRecord>(await request<unknown>('/api/datasets'), ['datasets']).map(normalizeDataset)
}

export function getDataset(id: string | number): Promise<DatasetRecord> {
  return request<unknown>(`/api/datasets/${encodeURIComponent(String(id))}`).then(normalizeDatasetDetail)
}

export function validateDataset(file: File): Promise<ImportResult> {
  return request<unknown>('/api/datasets/validate', { method: 'POST', file }).then(normalizeValidation)
}

export function importDataset(file: File): Promise<ImportResult> {
  return request<unknown>('/api/datasets/import', { method: 'POST', file }).then(normalizeImport)
}
