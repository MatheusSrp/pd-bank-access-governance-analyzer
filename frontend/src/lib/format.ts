import type { FindingRecord } from '../api/types'

const dateFormatter = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium', timeStyle: 'short' })
const numberFormatter = new Intl.NumberFormat('pt-BR')

export function formatDate(value: unknown): string {
  if (typeof value !== 'string' && typeof value !== 'number') return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : dateFormatter.format(date)
}

export function formatNumber(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? numberFormatter.format(value) : '—'
}

export function displayValue(value: unknown, fallback = '—'): string {
  if (typeof value === 'string' && value.trim()) return value
  if (typeof value === 'number' && Number.isFinite(value)) return numberFormatter.format(value)
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  return fallback
}

export function idOf(value: { id?: string | number; rule_id?: string; rule?: string }): string {
  return String(value.id ?? value.rule_id ?? value.rule ?? '—')
}

export function datasetName(dataset?: { name?: string; filename?: string; id?: string | number } | null): string {
  return dataset?.name || dataset?.filename || (dataset?.id !== undefined ? `Dataset ${dataset.id}` : 'Dataset')
}

export function severityLabel(value: unknown): string {
  const labels: Record<string, string> = { critical: 'Crítica', high: 'Alta', medium: 'Média', low: 'Baixa' }
  return typeof value === 'string' ? labels[value.toLowerCase()] ?? value : 'Não informada'
}

export function statusLabel(value: unknown): string {
  const labels: Record<string, string> = {
    non_compliant: 'Não conforme', insufficient_information: 'Informação insuficiente',
    valid_exception: 'Exceção válida', compliant: 'Conforme', completed: 'Concluída',
    failed: 'Falhou', running: 'Em execução', pending: 'Pendente',
  }
  return typeof value === 'string' ? labels[value.toLowerCase()] ?? value : 'Não informado'
}

export function exceptionLabel(value: unknown): string {
  const labels: Record<string, string> = { none: 'Sem exceção', valid: 'Válida', expired: 'Expirada', future: 'Futura' }
  return typeof value === 'string' ? labels[value.toLowerCase()] ?? value : 'Não informada'
}

export function objectReference(finding: FindingRecord): string {
  return displayValue(finding.object_reference ?? finding.object_ref)
}

export function evidenceText(finding: FindingRecord): string {
  if (typeof finding.evidence_summary === 'string' && finding.evidence_summary.trim()) return finding.evidence_summary
  if (typeof finding.evidence === 'string') return finding.evidence
  if (finding.evidence && typeof finding.evidence === 'object') {
    try { return JSON.stringify(finding.evidence) } catch { return 'Evidência disponível' }
  }
  return 'Sem resumo de evidência'
}

export function asObject(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null
}

export function numericMetric(source: unknown, candidates: string[]): number | null {
  const record = asObject(source)
  if (!record) return null
  for (const key of candidates) {
    const value = record[key]
    if (typeof value === 'number' && Number.isFinite(value)) return value
  }
  return null
}

export function countMap(source: unknown, candidates: string[]): Array<{ name: string; total: number }> {
  const record = asObject(source)
  if (!record) return []
  for (const key of candidates) {
    const value = record[key]
    if (Array.isArray(value)) {
      return value.flatMap(item => {
        const entry = asObject(item)
        if (!entry) return []
        const name = entry.name ?? entry.label ?? entry.domain ?? entry.rule_id ?? entry.status ?? entry.severity
        const total = entry.total ?? entry.count ?? entry.findings ?? entry.value
        return typeof name === 'string' && typeof total === 'number' && Number.isFinite(total) ? [{ name, total }] : []
      })
    }
    const map = asObject(value)
    if (map) return Object.entries(map).flatMap(([name, total]) => typeof total === 'number' && Number.isFinite(total) ? [{ name, total }] : [])
  }
  return []
}
