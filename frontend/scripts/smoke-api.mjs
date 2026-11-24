// Executa os módulos reais da interface em Node; não substitui a revisão no navegador.
import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'
import { createServer } from 'vite'

const server = await createServer({ server: { middlewareMode: true, hmr: false }, appType: 'custom' })
// O cliente usa apenas os timers de window para controlar o timeout HTTP.
globalThis.window = globalThis
try {
  const { getHealth, getIndicators } = await server.ssrLoadModule('/src/api/indicators.ts')
  const { validateDataset, importDataset, listDatasets } = await server.ssrLoadModule('/src/api/datasets.ts')
  const { runAnalysis, getAnalysis } = await server.ssrLoadModule('/src/api/analyses.ts')
  const { listFindings, getFinding } = await server.ssrLoadModule('/src/api/findings.ts')
  const { apiBaseUrl } = await server.ssrLoadModule('/src/api/client.ts')
  const health = await getHealth()
  assert.equal(health.status, 'ok')
  const source = new URL('../../tests/data/PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx', import.meta.url)
  const file = new File([await readFile(source)], 'PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx')
  const validation = await validateDataset(file)
  assert.equal(validation.validation.valid, true)
  assert.equal(validation.recognized_sheets.length, 20)
  const imported = await importDataset(file)
  const datasets = await listDatasets()
  assert.equal(datasets.find(item => item.id === imported.dataset.id)?.record_count, 1890)
  const analysis = await runAnalysis(imported.dataset.id)
  assert.equal(analysis.summary.total_findings, 431)
  assert.equal((await getAnalysis(analysis.id)).summary.total_findings, 431)
  const page = await listFindings({ analysis_id: analysis.id, limit: 20, offset: 0 })
  assert.equal(page.total, 431)
  assert.equal(page.items.length, 20)
  assert.equal((await getFinding(page.items[0].id)).id, page.items[0].id)
  assert.equal((await getIndicators()).summary.total_findings, 431)
  const checks = ['saúde', 'validação multipart', 'importação', 'contagem normalizada',
    'execução da análise', 'detalhe da análise', 'paginação e X-Total-Count', 'detalhe do achado', 'indicadores']
  const report = { executed_at: new Date().toISOString(), api_base_url: apiBaseUrl(),
    runtime: process.version, mode: 'Módulos reais via Vite SSR em Node, sem navegador',
    dataset_id: imported.dataset.id, analysis_id: analysis.id, findings: page.total, checks }
  if (process.argv[2]) await writeFile(process.argv[2], JSON.stringify(report, null, 2) + '\n')
  console.log(`OK: ${checks.length} verificações do cliente frontend; achados=${page.total}`)
} finally {
  await server.close()
  delete globalThis.window
}
