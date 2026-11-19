export type EntityId = string | number
export type Severity = 'critical' | 'high' | 'medium' | 'low'
export type FindingStatus = 'non_compliant' | 'insufficient_information' | 'valid_exception' | 'compliant'
export type ExceptionStatus = 'none' | 'valid' | 'expired' | 'future'

export interface DatasetRecord {
  id: EntityId
  name?: string
  filename?: string
  created_at?: string
  imported_at?: string
  record_count?: number
  accepted_records?: number
  rejected_records?: number
  validation?: Record<string, unknown>
  [key: string]: unknown
}

export interface AnalysisSummary {
  total_findings?: number
  critical_findings?: number
  high_findings?: number
  medium_findings?: number
  low_findings?: number
  expired_exceptions?: number
  by_severity?: Record<string, number>
  by_domain?: Record<string, number>
  by_rule?: Record<string, number>
  by_status?: Record<string, number>
  [key: string]: unknown
}

export interface AnalysisRecord {
  id: EntityId
  dataset_id?: EntityId
  dataset?: DatasetRecord
  created_at?: string
  executed_at?: string
  status?: string
  reference_date?: string | null
  summary?: AnalysisSummary
  coverage?: CoverageEntry[] | Record<string, unknown>
  findings?: FindingRecord[]
  [key: string]: unknown
}

export interface CoverageEntry {
  rule_id?: string
  id?: string
  evaluated?: boolean
  status?: string
  reason?: string
  [key: string]: unknown
}

export interface FindingRecord {
  id: EntityId
  analysis_id?: EntityId
  rule_id?: string
  rule?: string
  domain?: string
  severity?: Severity | string
  status?: FindingStatus | string
  exception_status?: ExceptionStatus | string
  object_reference?: string
  object_ref?: string
  description?: string
  evidence?: unknown
  evidence_summary?: string
  potential_impact?: string
  recommended_action?: string
  source_sheet?: string
  source_row?: number | string
  [key: string]: unknown
}

export interface RuleRecord {
  id?: string
  rule_id?: string
  name?: string
  title?: string
  description?: string
  domain?: string
  [key: string]: unknown
}

export interface FindingQuery {
  analysis_id?: EntityId
  domain?: string
  rule_id?: string
  severity?: Severity | ''
  status?: FindingStatus | ''
  exception_status?: ExceptionStatus | ''
  q?: string
  limit: number
  offset: number
}

export interface FindingPage {
  items: FindingRecord[]
  total: number
}

export interface ApiHealth {
  status?: string
  service?: string
  version?: string
  [key: string]: unknown
}

export interface ImportResult {
  dataset?: DatasetRecord
  validation?: Record<string, unknown>
  warnings?: string[]
  recognized_sheets?: string[]
  unknown_sheets?: string[]
  accepted_records?: number
  rejected_records?: number
  [key: string]: unknown
}
