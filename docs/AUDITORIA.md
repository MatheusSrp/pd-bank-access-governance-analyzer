# Auditoria e correções — v0.2.0 → v0.3.0

## 1. Limites desta auditoria (leia primeiro)

* **Excel oficial NÃO anexado.** Só o ZIP do backend foi recebido. Nenhum cabeçalho, chave ou relacionamento real foi verificado e os 15 casos públicos não foram executados. **Não se declara compatibilidade oficial.**
* **Sem SQLAlchemy/pytest/Docker/rede no ambiente.** Por isso: (a) a suíte *original* (13 testes) não pôde ser executada para baseline; (b) `pdbank/sql_repository.py`, o Dockerfile e o `docker-compose.yml` foram escritos mas **não executados**; (c) os testes foram escritos em `unittest` (coletáveis pelo pytest) e executados com `python -m unittest`, não com `pytest`.

## 2. Resultado dos testes (executados no ambiente da auditoria)

`python -m unittest discover -s tests -t .` → **104 testes: 91 executados e aprovados, 13 pulados** (os 13 são os testes de SQLite/PostgreSQL, que exigem SQLAlchemy). Smoke test HTTP real (servidor Flask + `curl`, repositório em memória): health, import ZIP com CSV `;`, análise, filtro com `X-Total-Count`, export CSV e erro 400 — OK.

| Arquivo | Cobre |
|---|---|
| `test_values_schema.py` | parse de bool/número/data, normalização, unicidade de aliases, 20 abas oficiais distintas, regressão de contaminação de campos |
| `test_importer.py` | CSV (`;`, cp1252, BOM, binário, vazio, duplicados), XLSX (válido, falso, truncado, datas, nº de linha), ZIP (traversal, bomb, limites, corrompido, duplicatas, criptografia/symlink) |
| `test_rules.py` | R01–R09 positivos/negativos, falsos positivos corrigidos, exceções (válida/vencida/futura/curinga/malformada), cobertura, determinismo |
| `test_validation.py` | abas reconhecidas/desconhecidas, linhas inválidas, avisos de cobertura |
| `test_api.py` | todos os endpoints, filtros/paginação, entradas inválidas, 413, 422, export + injeção de fórmula, API key, CORS, erro 500 em JSON |
| `contract.py` + `test_repository_memory.py` | contrato de persistência (passa em memória) |
| `test_sql_repository.py` | **o mesmo contrato** em SQLite (+ PostgreSQL via `TEST_POSTGRES_URL`) e migração de banco v0.2 — **não executado aqui** |

## 3. Falhas reais encontradas e corrigidas

| # | Problema (v0.2.0) | Impacto | Correção |
|---|---|---|---|
| 1 | `schema.field()`: alias `user_id` pertencia a 2 grupos; lookup de `user_id` podia devolver `asset_id`/`use_case_id` | achados com objeto/usuário errado | grupos únicos (validado no import e por teste); `get()` nunca mistura grupos |
| 2 | `atribuicoes_papeis` mapeada em 2 chaves; `table()` devolvia só o 1º alias | role_assignments nunca reconhecida; abas ignoradas | chaves separadas; todas as abas-alias são lidas |
| 3 | `truth()` tratava "Aprovado", `1.0`, "Parcial", "N/A" como **falso** | falsos positivos em R04/R05/R07 | parse tri-state; desconhecido → `insufficient_information` |
| 4 | **R08 só rodava se o usuário existisse em `usuarios`** (aninhado após `continue`) | falso negativo | R08 independente |
| 5 | Data só ISO; inválida virava "não vencido" em silêncio; `DD/MM/AAAA` ignorada | R08/exceções ineficazes | parse ISO + pt-BR; ilegível → informação insuficiente; "hoje" no fuso de Brasília; `reference_date` explícita |
| 6 | CSV sem normalizar cabeçalhos; só `,`; só UTF-8 | CSV pt-BR do Excel (`;`, cp1252, `Usuário ID`) gerava 0 achados em silêncio | normalização, delimitador e encoding detectados |
| 7 | ZIP/XLSX sem limites; `z.read()` integral | zip bomb / esgotamento de memória | limites de entradas, tamanho real, taxa de compressão, linhas, colunas; path traversal, criptografia e symlink rejeitados |
| 8 | Cabeçalhos duplicados sobrescreviam colunas; abas homônimas no ZIP sobrescreviam tabelas | perda silenciosa de dados | renomeio `_2`/`__2` + aviso |
| 9 | CSV exportado sem proteção | injeção de fórmula ao abrir no Excel | prefixo `'` |
| 10 | `dataset_id` não validado (`"1"`, lista, corpo não-objeto) e sem handler 500; erros de Postgres por `object_ref`>255 | HTTP 500 em HTML | validação de entrada, handler JSON, truncamento |
| 11 | Filtros inválidos (`analysis_id=abc`) ignorados; sem paginação; `/indicators` com formato instável | respostas enganosas | 400 com mensagem; `limit/offset/X-Total-Count`; formato estável |
| 12 | Exceção com curinga `*` suprimia tudo; exceção válida **apagava** o achado | risco de supressão indevida; sem rastreabilidade | curinga ignorado; achado mantido como `valid_exception` com referência à exceção |
| 13 | Valores ilegíveis (retenção "30 dias", autonomia não comparável, aprovação desconhecida) ignorados | falso negativo silencioso | `insufficient_information` |
| 14 | R09 comparava status sem normalizar acento ("Em revisão") | falso negativo | normalização; prazo vencido eleva severidade |
| 15 | Sem rastreabilidade ao dado de origem; análise "limpa" quando faltava aba | falsa sensação de conformidade | `source_sheet`/`source_row`; `coverage` por regra com motivo |
| 16 | `Base.metadata.create_all` e SQLite criados **na importação** do módulo; servidor de desenvolvimento no Docker, root, sem healthcheck | acoplamento, testes poluem disco, race com vários workers | `create_app()` + `init()`; gunicorn `--preload`, usuário não-root, `HEALTHCHECK`, porta do banco só em localhost |

## 4. Melhorias de organização

`app.py` monolítico (linhas de ~300 caracteres) → pacote `pdbank/` com responsabilidades separadas; motor de regras **puro** (sem banco); persistência atrás de `Repository` (memória + SQL com o mesmo teste de contrato). Funcionalidades existentes foram preservadas (todos os endpoints e campos antigos continuam; `analysis_id` mantido junto de `id`). Adições: `GET /api/datasets[/{id}]`, `GET /api/rules`, `coverage`, `reference_date`, paginação, CORS/API key opcionais, OpenAPI completo, `docs/API.md`.

**Mudanças de comportamento a conhecer:** exceção válida agora mantém o achado (`status=valid_exception`) em vez de removê-lo; `*` em exceções não vale mais; `GET /api/findings` valida filtros (400) e limita a 200 por padrão; coluna `domain` filtra por igualdade exata; host padrão local é `127.0.0.1`.

## 5. Verificação manual necessária (não executada aqui)

1. `pip install -r requirements.txt && pytest -q` — os 13 testes pulados devem passar (SQLite, migração v0.2).
2. `docker compose up --build`, depois `curl localhost:8080/api/health` e um import real; (opcional) `TEST_POSTGRES_URL=... pytest tests/test_sql_repository.py`.
3. Subir `python app.py` com SQLite e repetir o fluxo import → análise → export.
Envie a saída de (1) se algo falhar; o código SQL é a parte de maior risco por não ter sido executada.

## 6. Pendências (dataset oficial)

Quando o Excel oficial estiver disponível:
- [ ] Conferir os **20 nomes de aba** (`OFFICIAL_SHEETS`) e a aba `dicionario_de_dados`.
- [ ] Substituir/confirmar `FIELD_ALIASES` em `pdbank/schema.py` pelos cabeçalhos reais; conferir `REQUIRED_FIELDS` (avisos de cobertura de colunas).
- [ ] Mapear chaves/relacionamentos reais: usuário↔papel (`atribuicoes_papeis`), papel↔permissão (`rbac_baseline`), ativo↔evento, caso de IA↔controle/fonte. Hoje os joins assumem `user_id`, `role_id`, `permission_id`, `asset_id`, `use_case_id` (candidatos).
- [ ] Confirmar a taxonomia de classificação (`RESTRICTED_CLASSIFICATIONS`) e os vocabulários de status (`values.py`, `rules.py`: INACTIVE_STATES, PENDING_REVIEW…).
- [ ] Confirmar semântica de exceções (campos de aprovação/vigência) e de R07–R09 (candidatas complementares, não verificadas contra o enunciado).
- [ ] Executar os **15 casos públicos** (`casos_teste_publicos`) e comparar com o esperado; criar teste automatizado por caso. Nenhum resultado foi simulado.
- [ ] Decidir se `campos_dados` (nível de campo) entra em R03/R04; hoje a aba é só preservada.

## 7. Limitações conhecidas

Sem autenticação por padrão; sem paginação em `/api/analyses` e `/api/datasets`; dataset inteiro guardado como JSON texto (adequado ao porte acadêmico); `reviewer` sempre nulo; XLSX lido com `data_only=True` (fórmulas sem valor em cache viram vazio); Swagger UI depende de CDN; análise é síncrona.
