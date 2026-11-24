# PD Bank — frontend

Interface React/TypeScript da API Flask v0.4.0. O caminho oficial usa SQLite no
backend e Vite neste diretório, em dois terminais. A instalação completa do backend
está no [README raiz](../README.md#-instalação-oficial-sqlite--frontend).

## Instalar e executar

Requer Node.js 20+ com npm (validado com Node 24.21.0 / npm 11.19.0). Partindo da raiz:

```bash
cd frontend
npm ci
npm run dev
```

Abra **http://localhost:5173**. Mantenha a API ativa em **http://localhost:8080**,
com `CORS_ORIGINS=http://localhost:5173`. Os padrões funcionam sem arquivo `.env`.
A porta é estrita: se estiver ocupada, o Vite encerra com erro.

Para outra configuração, copie o exemplo e edite-o antes de iniciar:

```bash
cp .env.example .env.local
```

No Windows PowerShell: `Copy-Item .env.example .env.local`.

| Variável | Finalidade |
|---|---|
| `VITE_API_BASE_URL` | Padrão `http://localhost:8080`, sem `/api` no final. Deve ser acessível pelo navegador |
| `VITE_API_KEY` | Opcional; enviada em `X-API-Key` quando a API exige `API_KEY` |
| `VITE_APP_VERSION` | Padrão `1.0.0`, versão exibida da interface, independente do backend |

**Variáveis `VITE_*` ficam públicas no JavaScript.** Não use credenciais de produção.
A chave opcional serve apenas à demonstração local. Reinicie o Vite após mudanças;
para arquivos de produção, gere um novo build. O frontend não lê o `.env` da raiz.

## Demonstrar

1. Abra **Datasets** e selecione o Excel original em
   `../tests/data/PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx`.
2. Aguarde a validação, clique em **Importar dataset** e execute uma análise desse dataset.
3. Deixe a data de referência vazia, revise e confirme a execução.
4. Confira 431 achados e a referência 2026-11-05, consulte a paginação e o detalhe de um achado.
5. Exporte **JSON** e **CSV** pelo resultado ou pela página **Relatórios**.

Os valores acima correspondem ao Excel oficial original e ao motor v0.4.0. A
planilha corrigida de César é outro cenário e pode produzir resultados diferentes.

## Verificar o build

```bash
npm run build
npm run preview -- --port 5173
```

O build executa TypeScript e Vite e gera `dist/`. Pare o servidor de desenvolvimento
antes do preview na mesma porta. O preview padrão usa **http://localhost:3000**;
para usá-lo sem `--port 5173`, permita também essa origem no `CORS_ORIGINS` do backend.
O script `npm run dev:preview` também usa 3000.

Para hospedar `dist/`, configure o servidor estático para devolver `index.html` nas
rotas da aplicação (React Router). A API continua sendo um processo separado.
Nenhum arquivo de `dist/` deve ser enviado no PR ou no pacote de código-fonte.

## Teste reproduzível do cliente HTTP

Com a API ativa, execute neste diretório:

```bash
npm run smoke:api
```

O teste carrega os módulos reais de `src/api/` por Vite SSR em Node e verifica upload,
validação, análise, normalização, paginação e indicadores com o Excel oficial. Ele
usa as mesmas variáveis `VITE_*` da aplicação e cria um dataset e uma análise.
Para salvar evidência, passe um caminho: `npm run smoke:api -- ../evidencia-frontend.json`.
Use somente uma API de demonstração. Não executa a UI nem emula a política CORS do
navegador; o [teste HTTP do backend](../scripts/smoke_test.py) confere os cabeçalhos
CORS e as exportações. A revisão visual deve seguir o roteiro de demonstração.

## Contrato da API

As chamadas ficam em `src/api/client.ts`; os adaptadores estão em `src/api/adapters.ts`.
A interface usa upload multipart no campo `file`, endpoints REST para análise e
achados, `X-Total-Count` para paginação e `Content-Disposition` para downloads.
O backend deve expor ambos os cabeçalhos via CORS. Não há proxy nem regras de negócio
executadas no navegador. Sem API ou registros, são exibidos erros ou estados vazios.

Rotas: `/dashboard`, `/datasets`, `/analyses/new`, `/analyses`, `/analyses/:id`,
`/findings`, `/findings/:id`, `/governance/access`, `/governance/data`,
`/governance/ai`, `/reports` e `/settings`.

## Troubleshooting

| Sintoma | Verificação |
|---|---|
| Não conecta à API | Abra `/api/health` na porta 8080 e confira `VITE_API_BASE_URL`; reinicie o Vite após editar |
| Erro CORS | Permita a origem exata da página na API, incluindo a porta. `localhost` difere de `127.0.0.1` |
| HTTP 401 | Confira se `VITE_API_KEY` corresponde à `API_KEY` do backend |
| Porta ocupada | Libere 5173 ou ajuste a porta do Vite e CORS em conjunto |
| Build falha | Execute `npm ci` neste diretório e use Node 20+; não remova o lockfile |
| Preview falha na API | Use `--port 5173` ou adicione a origem 3000 no backend |
| HTTP 413 | O limite de upload da interface é 50 MB; confira também `MAX_UPLOAD_MB` na API |

Resultados de execução, alertas de dependências e limites da validação:
[entrega de Boniek](../docs/entregas/boniek/relatorio_execucao.md).
