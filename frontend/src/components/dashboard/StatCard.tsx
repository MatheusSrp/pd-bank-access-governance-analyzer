import type { LucideIcon } from 'lucide-react'

export function StatCard({ label, value, description, icon: Icon, tone = 'brand' }: { label: string; value: number | null; description: string; icon: LucideIcon; tone?: string }) {
  return <article className="stat-card card">
    <div className={`stat-icon stat-icon-${tone}`}><Icon size={17} strokeWidth={1.8} /></div>
    <div className="stat-heading"><span>{label}</span><span className={`stat-tone-dot dot-${tone}`} /></div>
    <strong className="stat-value">{value === null ? '—' : value.toLocaleString('pt-BR')}</strong>
    <span className="stat-description">{description}</span>
  </article>
}
