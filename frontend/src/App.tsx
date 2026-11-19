import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import { ErrorBoundary } from './components/feedback/ErrorBoundary'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DatasetsPage } from './pages/DatasetsPage'
import { NewAnalysisPage } from './pages/NewAnalysisPage'
import { AnalysesPage } from './pages/AnalysesPage'
import { AnalysisDetailPage } from './pages/AnalysisDetailPage'
import { FindingsPage } from './pages/FindingsPage'
import { FindingDetailPage } from './pages/FindingDetailPage'
import { GovernancePage } from './pages/GovernancePage'
import { ReportsPage } from './pages/ReportsPage'
import { SettingsPage } from './pages/SettingsPage'

function NotFoundPage() {
  return <section className="not-found card"><p className="eyebrow">PÁGINA NÃO ENCONTRADA</p><h1>Este caminho não existe</h1><p>Confira o endereço ou volte à visão geral do PD Bank.</p><a className="button button-primary" href="/dashboard">Ir para a visão geral</a></section>
}

function AppRoutes() {
  return <BrowserRouter><Routes><Route element={<AppShell />}>
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/datasets" element={<DatasetsPage />} />
    <Route path="/analyses/new" element={<NewAnalysisPage />} />
    <Route path="/analyses" element={<AnalysesPage />} />
    <Route path="/analyses/:id" element={<AnalysisDetailPage />} />
    <Route path="/findings" element={<FindingsPage />} />
    <Route path="/findings/:id" element={<FindingDetailPage />} />
    <Route path="/governance/access" element={<GovernancePage kind="access" />} />
    <Route path="/governance/data" element={<GovernancePage kind="data" />} />
    <Route path="/governance/ai" element={<GovernancePage kind="ai" />} />
    <Route path="/reports" element={<ReportsPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    <Route path="*" element={<NotFoundPage />} />
  </Route></Routes></BrowserRouter>
}

export default function App() {
  return <ErrorBoundary><ThemeProvider><ToastProvider><AppRoutes /></ToastProvider></ThemeProvider></ErrorBoundary>
}
