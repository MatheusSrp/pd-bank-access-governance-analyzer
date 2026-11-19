import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { EmptyState } from '../ui'
import { chartColors, severityColors, severityNames } from '../charts/palette'

function DistributionCard({ title, caption, data, kind = 'bar', horizontal = false }: { title: string; caption: string; data: Array<{ name: string; total: number }>; kind?: 'bar' | 'donut'; horizontal?: boolean }) {
  const chartHeight = Math.max(208, Math.min(290, 120 + data.length * 24))
  return <section className="card chart-card">
    <div className="card-header"><div><h2 className="card-title">{title}</h2><p className="card-subtitle">{caption}</p></div><span className="chart-live-mark" title="Distribuição recebida da API" /></div>
    <div className="chart-area" style={{ height: chartHeight }}>
      {data.length === 0 ? <EmptyState title="Dados não disponíveis" description="A API não retornou esta distribuição para as análises disponíveis." /> : kind === 'donut' ? <>
        <ResponsiveContainer width="100%" height="100%"><PieChart>
          <Pie data={data} dataKey="total" nameKey="name" cx="50%" cy="50%" innerRadius="61%" outerRadius="82%" paddingAngle={3} stroke="none">
            {data.map((entry, index) => <Cell key={`${entry.name}-${index}`} fill={severityColors[entry.name.toLowerCase()] || chartColors[index % chartColors.length]} />)}
          </Pie>
          <Tooltip contentStyle={{ background: 'var(--surface-raised)', border: '1px solid var(--border)', borderRadius: 9, color: 'var(--text)', fontSize: 11 }} formatter={(value: number, name: string) => [value.toLocaleString('pt-BR'), severityNames[name.toLowerCase()] || name]} />
        </PieChart></ResponsiveContainer>
        <div className="donut-center"><strong>{data.reduce((sum, entry) => sum + entry.total, 0).toLocaleString('pt-BR')}</strong><span>achados</span></div>
        <div className="chart-legend">{data.map((entry, index) => <div key={entry.name}><span className="legend-swatch" style={{ background: severityColors[entry.name.toLowerCase()] || chartColors[index % chartColors.length] }} /><span>{severityNames[entry.name.toLowerCase()] || entry.name}</span><strong>{entry.total.toLocaleString('pt-BR')}</strong></div>)}</div>
      </> : <ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={{ top: 6, right: 12, bottom: 4, left: horizontal ? 13 : 0 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 4" vertical={!horizontal} horizontal={horizontal} />
        {horizontal ? <><XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} axisLine={false} tickLine={false} allowDecimals={false} /><YAxis type="category" dataKey="name" width={58} tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} axisLine={false} tickLine={false} /></> : <><XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 9 }} axisLine={false} tickLine={false} interval={0} angle={data.length > 5 ? -22 : 0} textAnchor={data.length > 5 ? 'end' : 'middle'} height={data.length > 5 ? 48 : 28} /><YAxis tick={{ fill: 'var(--text-muted)', fontSize: 9 }} axisLine={false} tickLine={false} allowDecimals={false} width={30} /></>}
        <Tooltip cursor={{ fill: 'rgba(102,136,255,.08)' }} contentStyle={{ background: 'var(--surface-raised)', border: '1px solid var(--border)', borderRadius: 9, color: 'var(--text)', fontSize: 11 }} formatter={(value: number) => [value.toLocaleString('pt-BR'), 'Achados']} />
        <Bar dataKey="total" fill="#6688ff" radius={horizontal ? [0, 5, 5, 0] : [5, 5, 0, 0]} maxBarSize={24} />
      </BarChart></ResponsiveContainer>}
    </div>
  </section>
}

export function ChartsOverview({ severity, domains, rules, statuses }: { severity: Array<{ name: string; total: number }>; domains: Array<{ name: string; total: number }>; rules: Array<{ name: string; total: number }>; statuses: Array<{ name: string; total: number }> }) {
  return <div className="charts-grid">
    <DistributionCard title="Severidade dos achados" caption="Distribuição registrada nas análises" data={severity} kind="donut" />
    <DistributionCard title="Achados por domínio" caption="Concentração por domínio de governança" data={domains} />
    <DistributionCard title="Achados por regra" caption="Cobertura R01–R09 quando disponível" data={rules} horizontal />
    <DistributionCard title="Achados por status" caption="Situação de conformidade reportada" data={statuses} />
  </div>
}
