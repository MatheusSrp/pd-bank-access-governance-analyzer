import type { AnalysisRecord, AnalysisSummary, DatasetRecord, FindingRecord, ImportResult } from './types'

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}
function number(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined
}
export function normalizeSummary(value: unknown): AnalysisSummary {
  const source = record(value)
  const severity = record(source.by_severity)
  return {
    ...source,
    total_findings: number(source.total_findings) ?? number(source.total),
    critical_findings: number(source.critical_findings) ?? number(severity.critical),
    high_findings: number(source.high_findings) ?? number(severity.high),
    medium_findings: number(source.medium_findings) ?? number(severity.medium),
    low_findings: number(source.low_findings) ?? number(severity.low),
    by_domain: record(source.by_domain) as Record<string, number>,
  }
}
export function normalizeAnalysis(value: AnalysisRecord): AnalysisRecord {
  const summary = normalizeSummary(value.summary)
  if (value.findings && value.findings.length) {
    const domains: Record<string, number> = {}
    for (const finding of value.findings) {
      if (finding.domain) domains[finding.domain] = (domains[finding.domain] ?? 0) + 1
    }
    summary.by_domain = domains
  }
  return { ...value, summary, findings: value.findings?.map(normalizeFinding) }
}
export function normalizeDataset(value: DatasetRecord): DatasetRecord {
  const tableCounts = record(value.table_counts)
  const total = Object.values(tableCounts).reduce<number>((sum, n) => sum + (number(n) ?? 0), 0)
  return { ...value, record_count: number(value.record_count) ?? total }
}
export function normalizeDatasetDetail(value: unknown): DatasetRecord {
  const outer = record(value)
  const inner = record(outer.dataset) as unknown as DatasetRecord
  return { ...normalizeDataset(inner), validation: record(outer.validation) }
}
export function normalizeImport(value: unknown): ImportResult {
  const raw = record(value)
  const validation = record(raw.validation)
  const importInfo = record(raw.import)
  const sheets = Array.isArray(validation.recognized_sheets) ? validation.recognized_sheets : []
  const recognized = sheets.map(item => String(record(item).source_name ?? item))
  const warnings = [...(Array.isArray(validation.warnings) ? validation.warnings : []),
    ...(Array.isArray(importInfo.warnings) ? importInfo.warnings : [])].filter((item): item is string => typeof item === 'string')
  return { ...raw, validation, warnings, recognized_sheets: recognized,
    unknown_sheets: Array.isArray(validation.unknown_sheets) ? validation.unknown_sheets as string[] : [],
    accepted_records: number(validation.records_accepted), rejected_records: number(validation.records_rejected),
    dataset: raw.dataset ? normalizeDataset(raw.dataset as DatasetRecord) : undefined }
}
export function normalizeValidation(value: unknown): ImportResult {
  const raw = record(value)
  const errors = Array.isArray(raw.errors) ? raw.errors.map(item => String(record(item).message ?? item)) : []
  return normalizeImport({ validation: { ...raw, errors } })
}
export function normalizeFinding(value: FindingRecord): FindingRecord {
  const source = value as Record<string, unknown>
  return { ...value,
    object_reference: value.object_reference ?? value.object_ref,
    potential_impact: value.potential_impact ?? (typeof source.impact === 'string' ? source.impact : undefined),
    recommended_action: value.recommended_action ?? (typeof source.recommendation === 'string' ? source.recommendation : undefined),
  }
}
