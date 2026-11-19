import { request } from './client'
import { normalizeSummary } from './adapters'
import type { ApiHealth, RuleRecord } from './types'

export function getHealth(): Promise<ApiHealth> {
  return request<ApiHealth>('/api/health')
}

export async function getRules(): Promise<RuleRecord[]> {
  return asList<RuleRecord>(await request<unknown>('/api/rules'), ['rules'])
}

export async function getIndicators(): Promise<Record<string, unknown>> {
  const result = await request<Record<string, unknown>>('/api/indicators')
  return { ...result, summary: normalizeSummary(result.latest) }
}

export function asList<T>(payload: unknown, collectionKeys: string[] = []): T[] {
  if (Array.isArray(payload)) return payload as T[]
  if (payload && typeof payload === 'object') {
    const record = payload as Record<string, unknown>
    for (const key of [...collectionKeys, 'items', 'results', 'data']) {
      if (Array.isArray(record[key])) return record[key] as T[]
    }
  }
  throw new Error('A API retornou uma coleção em formato inesperado. Consulte o contrato do backend.')
}
