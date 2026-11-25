# Relatório de Validação — PD Bank Access & Governance Analyzer (v0.4.0)

* **Responsáveis:** Matheus do Nascimento Gomes Vaz e Mateus Valerino Barros de Santana
* **Versão Validada:** v0.4.0
* **Base de Evidências:** Suíte automatizada (`pytest` / `unittest`), script oficial `scripts/analyze_official_dataset.py` e auditoria de qualidade de dados (`scripts/check_data_quality.py`).

---

## 1. Resumo Executivo da Validação

A validação funcional e de contrato da versão `v0.4.0` confirma que o motor determinístico processa integralmente as **20 abas** e **1.890 registros** do dataset oficial sem erros de importação, produzindo **431 achados rastreáveis** (`source_sheet` e `source_row`) e exportação CSV/JSON íntegra.

Nos **8 casos de teste formais** (`T1`–`T8`), todos os cenários planejados foram executados com sucesso (`7 Verdadeiros Positivos` e `1 Verdadeiro Negativo` composto por 2 cenários negativos distintos, totalizando **0 Falsos Positivos** e **0 Falsos Negativos** no escopo validado).

---

## 2. Tabela Comparativa dos 15 Casos Públicos (`casos_teste_publicos`)

| Caso | Cenário | Esperado (Categoria / Prioridade / Decisão) | Obtido pelo Motor (v0.4.0) | Veredito Técnico | Classificação / Tratamento |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC01** | `U003/RES03` Admin fora da baseline | `Excesso_de_Privilegio` / Crítico / Revisão | `Excesso_de_Privilegio` / `critical` / **Atenção** (`valid_exception` via `EX001`) | `divergent` | **Divergência documentada:** motor detecta o achado crítico (VP), mas rebaixa a decisão para `Atenção` porque `EX001` está vigente até `2026-12-01`. `[PENDENTE: decisão final do Abraão entre manter Atenção ou exigir Revisão para críticos]` |
| **TC02** | `U037` desligado com permissão | `Conta_Desligada` / Crítico / Revisão | `Conta_Desligada` / `critical` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC03** | `U099` solicitante e aprovador | `Conflito_SoD` / Crítico / Revisão | `Conflito_SoD` / `critical` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC04** | `U010` acesso temporário expirado | `Acesso_Expirado` / Alto / Revisão | `Acesso_Expirado` / `high` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC05** | `U001/RES01` compatível com papel | `sem_achado` / Baixo / Conforme | Nenhum achado / Conforme | `match` | **Verdadeiro Negativo (VN)** |
| **TC06** | `DA18` sem proprietário | `Proprietario_Ausente` / Alto / Revisão | `Proprietario_Ausente` / `high` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC07** | `DA20` sem classificação | `Classificacao_Ausente` / Alto / Revisão | `Classificacao_Ausente` / `high` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC08** | `DA02` política completa | `sem_achado` / Baixo / Conforme | Nenhum achado / Conforme | `match` | **Verdadeiro Negativo (VN)** |
| **TC09** | `SH005` (`DA06`) destino x aprovação | `Calcular` / Variável / Calcular | Nenhum achado / **Conforme** (calculado) | `computed` | **Calculado (VN):** destino aprovado, minimizado e protegido; motor calcula conformidade sem forçar alerta. `[PENDENTE: formalização do Abraão]` |
| **TC10** | `DA23` retenção incompleta | `Retencao_Ausente` / Alto / Revisão | `Retencao_Ausente` / `high` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC11** | `AI06` ação crítica com execução | `Agencia_Excessiva` / Crítico / Revisão | `Agencia_Excessiva` / `critical` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC12** | `AI12` baixo impacto conforme | `sem_achado` / Baixo / Conforme | Nenhum achado / Conforme | `match` | **Verdadeiro Negativo (VN)** |
| **TC13** | `AI02` sem proteção de prompt | `Guardrail_Ausente` / Alto / Revisão | `Guardrail_Ausente` / `high` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC14** | `AI14/DA03` risco integrado | `Risco_Integrado` / Crítico / Revisão | `Risco_Integrado` / `critical` / Revisão | `match` | **Verdadeiro Positivo (VP)** |
| **TC15** | `AI03/DA12` piloto com exceção (`EX004`) | `excecao_valida` / Médio / Atenção | Nenhum achado (`EX004` sem achado associado) | `unmatched` | **Não casado (limitação registrada):** `AI03` possui controles completos e nenhuma regra dispara violação; o motor não inventa achado para casar com `EX004`. `[PENDENTE: decisão final do Abraão]` |

---

## 3. Tratamento Explícito de Falsos Positivos, Falsos Negativos e Limitações

1. **Prevenção de Falsos Positivos (FP):**
   * **Usuários em Licença (`R07`):** Usuários com status `Licenca` (`U052`, `U105`) são intencionalmente isolados de `INACTIVE_STATES`, evitando falso positivo de conta desligada (embora permissões fora do baseline continuem sinalizadas em `R01`).
   * **Dados Ausentes ou Deslocados (`AI07`):** Em vez de presumir violação, o motor emite `status = insufficient_information` (`Dado_Inconsistente`), exigindo revisão humana. No experimento controlado do dataset corrigido (`PD_Bank_Dataset_AI07_Corrigido_TESTE.xlsx`), a correção da linha `AI07` converte `Dado_Inconsistente` (`R06 -1`) em `Guardrail_Ausente` (`R05 +1`), mantendo o total de 431 achados.
   * **Recertificações Vencidas (`R09`):** As 124 ocorrências de `Recertificacao_Vencida` são classificadas como `low` para evitar ruído operacional sobre achados críticos, permanecendo visíveis para governança.
2. **Riscos Conhecidos de Falso Negativo / Cobertura Parcial (FN):**
   * **Principals do tipo `Aplicacao` (`R01`):** 29 permissões vinculadas a aplicações não são comparadas ao `rbac_baseline` porque o baseline atual modela apenas papéis de usuários humanos.
   * **Aba `campos_dados` (`R03`/`R04`):** Os 135 registros de campos são importados e preservados, mas ainda não possuem regra de cruzamento semântico implementada no motor.
   * **Exceções Órfãs (`EX003` e `EX004`):** Permanecem vigentes sem achado correspondente no dataset oficial e são reportadas explicitamente em `coverage["EXCEPTIONS"]["notes"]`.

---

## 4. Contrato de Integração HTTP, Build e Regressão

* **Contrato Multipart e Persistência:** Validado via `tests/test_frontend_integration.py` — `POST /api/datasets/validate` processa o arquivo em memória (`200 OK`) sem gravar registros indevidos no repositório.
* **CORS e Paginação (`X-Total-Count`):** Validado que `Access-Control-Allow-Origin` respeita `CORS_ORIGINS` (`http://localhost:5173`) e que `/api/findings` expõe `X-Total-Count` em `Access-Control-Expose-Headers`.
* **Exportação CSV/JSON:** Validado que `GET /api/analyses/<id>/export?format=csv` inclui todas as colunas obrigatórias de rastreabilidade (`finding_type`, `subject_id`, `related_id`, `source_sheet`, `source_row`).
* **Suíte de Regressão e Build:** Confirmada a execução limpa da suíte (`138 testes` validados na entrega de execução técnica + `14 testes` de qualidade de dados + build `npm run build` concluído sem erros). *Nota operacional em ambiente Windows:* execuções paralelas/repetidas de `tests/test_sql_repository.py` podem apresentar `WinError 32` na limpeza de arquivo SQLite temporário por bloqueio de handle do sistema operacional, sem impacto na lógica de negócio.
