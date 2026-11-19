# Entregas e critérios — PD Bank

## 1. Fundação do app, design system e integração
- [x] Entregar aplicação React + TypeScript, Vite, Tailwind CSS, React Router, Recharts e Lucide React, exportável e executável dentro de `/frontend` no repositório Flask existente; não criar backend.
- [x] Organizar código reutilizável em API, layout, dashboard, charts, tables, feedback, UI, páginas, hooks, contexts, lib e styles, com tipos de resposta fortemente tipados e sem componentes monolíticos.
- [x] Centralizar todas as chamadas HTTP em `src/api/client.ts`; usar `VITE_API_BASE_URL=http://localhost:8080` e `VITE_API_KEY` opcional local, sem credenciais hardcoded nem alegar que chave enviada pelo navegador é segredo seguro.
- [x] Restringir integrações aos endpoints documentados: `GET /api/health`, `GET /api/rules`; `POST /api/datasets/import`, `POST /api/datasets/validate`, `GET /api/datasets`, `GET /api/datasets/:id`; `POST /api/analyses`, `GET /api/analyses`, `GET /api/analyses/:id`, `GET /api/analyses/:id/export?format=json|csv`; `GET /api/findings`, `GET /api/findings/:id`; `GET /api/indicators`. Não inventar endpoints, armazenamento, autenticação ou regras de negócio.
- [x] Tornar todo texto visível da interface pt-BR, com formatação brasileira de datas/números; manter responsividade desktop/tablet/mobile, navegação por teclado, foco visível, contraste, tooltips, transições discretas, respeito a `prefers-reduced-motion`, error boundary, skeletons, toasts, diálogos quando pertinentes e estados vazios/erro.
- [x] Incluir temas escuro (padrão) e claro, identidade premium navy com acentos azul/ciano/violeta, bordas/sombras contidas e componentes de severidade/status consistentes.
- [x] Não fabricar métricas, datasets, análises, achados, usuários, tendências, dados históricos, percentuais de progresso ou violações. Indisponibilidade deve ser erro de conexão; ausência de análises deve ser estado vazio; métricas indisponíveis devem usar placeholder. Modo de demonstração, se existir, isolado, desativado por padrão e rotulado “Demonstração”.
- [x] Tratar backend indisponível, dataset inválido/ausente, upload excessivo, falha de validação, análise/achado ausente, erro de API, resposta vazia e timeout com mensagens úteis em português.

## 2. Shell e dashboard executivo (`/dashboard`)
- [x] Shell inclui sidebar recolhível com Visão Geral, Datasets, Nova Análise, Histórico, Achados, Governança de Acessos, Proteção de Dados, Governança de IA, Relatórios e Configurações, todos com ícones apropriados.
- [x] Navegação superior mostra título da página, breadcrumbs, busca global/contextual, estado da conexão do backend, alternância de tema e avatar apenas visual (sem autenticação fictícia).
- [x] Dashboard exibe Total de Datasets, Análises Executadas, Total de Achados, Achados Críticos, Achados de Alta Severidade e Exceções Expiradas usando dados reais; sinaliza severidade, ícones e descrições úteis.
- [x] Incluir visualizações de achados por severidade (donut), domínio (barras), regra R01–R09 (barras horizontais) e status (categórica/empilhada), apenas com dados disponíveis na API; sem tendências históricas inventadas.
- [x] Tabela de achados recentes inclui regra, domínio, objeto, severidade, status, descrição e ação de inspeção.
- [x] Exibir cobertura das regras avaliadas e não avaliadas; regra não avaliada nunca pode ser tratada como zero violações.
- [x] Sem dataset/análise: mensagem “Nenhuma análise realizada” e ação “Importar primeiro dataset”.

## 3. Datasets (`/datasets`)
- [x] Listar datasets reais com nome, data de importação, contagens de registros, detalhes e resumo da validação; oferecer importação.
- [x] Upload drag-and-drop real para XLSX, CSV e ZIP, limite 50 MB; usar `multipart/form-data`, endpoint `POST /api/datasets/import` e campo chamado exatamente `file`.
- [x] Apresentar estados de envio, sucesso, erros e alertas de validação, planilhas reconhecidas/desconhecidas e registros aceitos/rejeitados; não mostrar percentual fictício quando progresso não estiver disponível.
- [x] Após importação, permitir iniciar análise do dataset.

## 4. Execução, histórico e detalhe da análise (`/analyses/new`, `/analyses`, `/analyses/:id`)
- [x] Fluxo guiado de nova análise: selecionar dataset importado, data de referência opcional, revisar configuração, executar pelo endpoint real e apresentar resultado; corpo JSON `{dataset_id, reference_date?}`; mostrar carregamento/erros significativos e navegar ao resultado após sucesso; nunca simular análise.
- [x] Histórico mostra ID, ID do dataset, data de execução, status, total de achados, críticos, data de referência e ação para detalhes.
- [x] Detalhe mostra resumo executivo, distribuição de severidade, achados por regra, cobertura, dataset associado, lista completa de achados e ações de exportação.
- [x] Cobertura do detalhe usa `coverage` real e apresenta razão quando regra não foi avaliada, sem tratar não avaliada como resultado zero.

## 5. Explorador e detalhe de achados (`/findings`, `/findings/:id`)
- [x] Tabela avançada inclui ID, regra, domínio, severidade, status, referência do objeto, resumo da evidência e ação.
- [x] Filtros server-side por severidade, regra, domínio, status e situação da exceção; pesquisa `q` por referência do objeto; paginação, limpar filtros, skeletons e vazios.
- [x] Consultas devem suportar `analysis_id`, `domain`, `rule_id`, `severity`, `status`, `exception_status`, `q`, `limit` e `offset`; lista é array e total vem do header `X-Total-Count`, não de filtragem de subconjunto local.
- [x] Valores reconhecidos: severidade `critical`, `high`, `medium`, `low`; status `non_compliant`, `insufficient_information`, `valid_exception`, `compliant`; exceção `none`, `valid`, `expired`, `future`.
- [x] Detalhe de investigação exibe identificador, regra, badges de severidade/status, domínio, objeto afetado, descrição, evidência, impacto potencial, ação corretiva recomendada, planilha e linha originais, estado da exceção e análise associada.
- [x] Não expor botões fictícios para alterar status ou designar revisores se a API não suportar essas operações.

## 6. Governança por domínio
- [x] Criar `/governance/access` para desvios RBAC, conflitos SoD, usuários inativos com acesso e problemas de revisão de acesso.
- [x] Criar `/governance/data` para classificação, ownership, compartilhamento, retenção e proteção de dados.
- [x] Criar `/governance/ai` para guardrails ausentes, controles de IA, supervisão humana e autonomia excessiva.
- [x] Reutilizar componentes do explorador quando útil; usar catálogo real `/api/rules` e domínios dos achados para decidir pertinência, sem presumir mapeamento hardcoded não confirmado pelas respostas.

## 7. Relatórios (`/reports`)
- [x] Permitir escolher análise existente e revisar resumo executivo.
- [x] Exportar JSON e CSV por `GET /api/analyses/:id/export?format=json|csv`, com download/resposta real.
- [x] Não oferecer PDF sem suporte da API; interface pode deixar claro que PDF é evolução futura, sem afirmar que existe.

## 8. Configurações (`/settings`)
- [x] Exibir URL da API, estado de conexão, preferência de tema, versão, informação técnica, regras disponíveis e saúde do sistema usando respostas reais.
- [x] Não criar configurações backend nem funções de gestão de usuários sem suporte.

## 9. Entrega e execução
- [x] Incluir Vite, configuração Tailwind, `.env.example`, README em português com instalação e execução, estrutura modular, rotas, gráficos, upload, filtros/paginação server-side, execução, exportações, tema e responsividade.
- [x] Criar `public/manus-routes.json` sincronizado às rotas implementadas, incluindo padrões dinâmicos.
- [x] Garantir execução `npm install`, `npm run dev` e `npm run build`, com TypeScript sem erros; documentar integração à API Flask existente e requisitos de CORS no backend.


## Observação de verificação externa

O frontend foi compilado e servido no Preview, e a revisão independente não encontrou bloqueios. O Flask em `localhost:8080` não estava acessível neste Sandbox e nenhum `docs/API.md`/schema de resposta foi anexado; portanto, upload, validação, análise, exportação e campos opcionais não puderam ser confirmados ponta a ponta contra uma instância real. Os estados de indisponibilidade e os placeholders são mantidos deliberadamente, sem dados simulados.
