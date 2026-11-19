import { request, requestWithHeaders } from './client'
import { normalizeFinding } from './adapters'
import type { EntityId, FindingPage, FindingQuery, FindingRecord } from './types'

export async function listFindings(query: FindingQuery): Promise<FindingPage> {
  const params = new URLSearchParams()
  for (const key of ['analysis_id', 'domain', 'rule_id', 'severity', 'status', 'exception_status', 'q'] as const) {
    const value = query[key]
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  params.set('limit', String(query.limit))
  params.set('offset', String(query.offset))
  const { data, headers } = await requestWithHeaders<unknown>(`/api/findings?${params.toString()}`)
  if (!Array.isArray(data)) throw new Error('A API retornou uma lista de achados em formato inesperado.')
  const totalHeader = headers.get('X-Total-Count')
  const total = totalHeader === null ? Number.NaN : Number(totalHeader)
  if (!Number.isFinite(total) || total < 0) throw new Error('A API não informou um valor válido no header X-Total-Count, necessário para paginar os achados.')
  return { items: (data as FindingRecord[]).map(normalizeFinding), total }
}

export function getFinding(id: EntityId): Promise<FindingRecord> {
  return request<FindingRecord>(`/api/findings/${encodeURIComponent(String(id))}`).then(normalizeFinding)
}
