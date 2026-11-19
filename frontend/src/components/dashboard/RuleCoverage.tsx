import type { CoverageEntry } from '../../api/types'
import { Badge, EmptyState } from '../ui'

export function coverageEntries(value: CoverageEntry[] | Record<string, unknown> | undefined): CoverageEntry[] {
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object') {
    return Object.entries(value).map(([rule_id, detail]) => {
      if (detail && typeof detail === 'object') return { rule_id, ...(detail as Record<string, unknown>) } as CoverageEntry
      return { rule_id, evaluated: detail === true, reason: typeof detail === 'string' ? detail : undefined }
    })
  }
  return []
}

export function RuleCoverage({ coverage }: { coverage: CoverageEntry[] }) {
  if (!coverage.length) return <EmptyState title="Cobertura não informada" description="O backend não retornou a cobertura de regras desta análise." />
  return <div className="coverage-list">{coverage.map((entry, index) => {
    const rule = entry.rule_id ?? entry.id ?? `Regra ${index + 1}`
    const evaluated = entry.evaluated === true || entry.status === 'evaluated' || entry.status === 'evaluado'
    return <div className="coverage-row" key={`${rule}-${index}`}>
      <span className="rule-code">{rule}</span>
      <span className="coverage-reason">{evaluated ? 'Executada nesta análise' : entry.reason || 'Não avaliada'}</span>
      <Badge tone={evaluated ? 'success' : 'warning'}>{evaluated ? 'Avaliada' : 'Não avaliada'}</Badge>
    </div>
  })}</div>
}
