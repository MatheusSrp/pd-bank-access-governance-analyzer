# PD Bank — Access & Governance Analyzer

Frontend empresarial de análise de governança, riscos e controles. Este projeto contém somente a aplicação web React/TypeScript e integra-se à API Flask existente; não inclui nem cria um backend.

## Requisitos

- Node.js 20 ou superior e npm.
- Backend Flask existente disponível em `http://localhost:8080` (ou URL configurada).
- Para acessar a API a partir do browser, o Flask precisa permitir via CORS a origem do frontend (`http://localhost:3000` no Preview deste projeto ou `http://localhost:5173` quando executado no Vite com outra configuração de porta). Configure CORS no backend existente; este frontend não adiciona proxy ou endpoints.

## Instalação e execução

```bash
npm install
cp .env.example .env.local
npm run dev
```

`npm run dev` inicia o frontend local em `http://localhost:5173`, conforme o fluxo de desenvolvimento do projeto. O script `npm run dev:preview` reserva a porta 3000 para o Preview gerenciado do Manus.

## Variáveis de ambiente

- `VITE_API_BASE_URL`: URL base da API Flask. Padrão: `http://localhost:8080`.
- `VITE_API_KEY`: opcional; enviado no header `X-API-Key` para desenvolvimento local se o Flask exigir.
- `VITE_APP_VERSION`: versão apresentada na tela Configurações.

Atenção: variáveis `VITE_*` são compiladas para código acessível no navegador. `VITE_API_KEY` não é um segredo seguro e não deve ser usada como autenticação de produção. Não coloque credenciais de produção no arquivo `.env` do frontend.

## Build local

```bash
npm run build
npm run preview
```

O artefato estático é criado em `dist/`. O frontend pode ser copiado para `/frontend` do repositório existente sem substituir o Flask; publique `dist/` por qualquer servidor de arquivos estáticos configurado pelo projeto anfitrião.

## Integração da API

Todas as operações HTTP estão centralizadas em `src/api/client.ts` e usam os endpoints informados do serviço Flask, incluindo importação multipart com campo `file`, execução de análise, consultas de achados com filtros server-side e leitura de `X-Total-Count`, saúde, catálogo de regras e exportação JSON/CSV.

Se a aplicação web e Flask estiverem em origens diferentes, ajuste CORS no backend para a origem real do navegador. A API key opcional é enviada em `X-API-Key`; use-a somente para ambiente de desenvolvimento sob as políticas do projeto.

O frontend não contém dados de demonstração ativados por padrão. Se a API estiver indisponível, a interface informa o problema; se não houver registros, apresenta estados vazios. Campos ausentes no contrato são representados por “—”/“Não informado”, e métricas ou tendências não são inventadas.

## Rotas

- `/dashboard`
- `/datasets`
- `/analyses/new`
- `/analyses` e `/analyses/:id`
- `/findings` e `/findings/:id`
- `/governance/access`
- `/governance/data`
- `/governance/ai`
- `/reports`
- `/settings`
