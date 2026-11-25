# Resultados Obtidos — Execução v0.4.0

* **Responsáveis:** Matheus do Nascimento Gomes Vaz e Mateus Valerino Barros de Santana
* **Snapshot Oficial Analisado:** `PD_Bank_Analyzer_Dataset_Completo_Alunos_1.xlsx` (SHA-256 `70e7e759...c2299e76`, referência `2026-11-05`)
* **Totais Gerais Obtidos:** 20/20 abas reconhecidas (0 avisos), 1.890 registros processados, **431 achados** (`44 critical`, `119 high`, `142 medium`, `126 low`), todas as 9 regras (`R01`–`R09`) efetivamente avaliadas.

---

## 1. Resultados Obtidos nos 8 Casos Formais

| ID | Resultado Obtido pelo Sistema | Classificação | Status | Evidência de Comprovação |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | Motor gerou 5 ocorrências de `Conta_Desligada` em `R07` (`U037`, `U074`, `U111`, `U148`, `U150`), incluindo `U037/RES04` com severidade `critical` e `status = non_compliant`. Usuários em licença (`U052`, `U105`) não foram marcados indevidamente em `R07`. | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py::test_r07_only_dismissed_users_not_those_on_leave` |
| **T2** | Motor gerou `Proprietario_Ausente` (`high`) para `DA18` e `Classificacao_Ausente` (`high`) para `DA20` na regra `R03` (total de 7 achados em `R03`). | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py::test_r03_r04_r08_planted_cases` |
| **T3** | Motor gerou `Guardrail_Ausente` (`high`) para `AI02` apontando falta de proteção contra *prompt injection* na regra `R05`. | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py::test_ai_findings_use_controles_ia_values` |
| **T4** | Nenhum achado gerado para `(U001, RES01)` em `R01` (dentro dos 507 registros de usuários avaliados, apenas 11 pares geraram `Excesso_de_Privilegio` e 5 geraram `Modo_de_Acesso_Divergente`). | **Verdadeiro Negativo (VN)** | **Aprovado** | `tests/test_official_dataset.py::test_r01_outside_baseline_exactly_the_eleven_anomalies` |
| **T5** | Zero achados gerados para `AI12` em `R05`/`R06` e zero achados gerados para `DA02` em `R04`. | **Verdadeiro Negativo (VN)** | **Aprovado** | `tests/test_official_dataset.py::test_ai_findings_use_controles_ia_values` e `test_public_cases_comparison_is_honest` |
| **T6** | 1) `R08` gerou 4 achados de `Acesso_Expirado` (`high`), incluindo `(U010, RES01)`;<br>2) Na data `2026-11-05`, as 4 exceções foram validadas (`valid: 4`), convertendo `(U003, RES03, R01)` via `EX001` e `(U057, RES06, R01)` via `EX002` para `status = valid_exception`. | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py::test_exception_association_and_validity` |
| **T7** | 1) Para `AI07`, o motor gerou `Dado_Inconsistente` (`status = insufficient_information`, `low`) em `R06` devido ao deslocamento de colunas na origem, sem interromper o disparo de `Fonte_Nao_Aprovada` (`DA09`) em `R05`;<br>2) `POST /api/datasets/validate` retornou `200`, header `Access-Control-Allow-Origin: http://localhost:5173` e `GET /api/datasets` permaneceu vazio (`[]`). | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py` e `tests/test_frontend_integration.py::test_frontend_multipart_validation_does_not_persist` |
| **T8** | 1) Para `AI14/DA03`, o motor gerou `Risco_Integrado` (`critical`), `Agencia_Excessiva` (`critical`) e `Acesso_Excessivo` (`critical`);<br>2) `GET /api/findings` retornou `200` com `X-Total-Count` presente em `Access-Control-Expose-Headers`. | **Verdadeiro Positivo (VP)** | **Aprovado** | `tests/test_official_dataset.py` e `tests/test_frontend_integration.py::test_frontend_cors_exposes_total_count` |

---

## 2. Distribuição de Achados Obtidos por Regra (Snapshot Oficial)

| Regra | Título no Motor | Registros Verificados | Achados Gerados | Observação Técnica |
| :--- | :--- | :---: | :---: | :--- |
| **R01** | Acesso fora do baseline RBAC | 507 | **16** | 11 `Excesso_de_Privilegio` + 5 `Modo_de_Acesso_Divergente`; 29 permissões de `Aplicacao` não comparadas. |
| **R02** | Conflito de segregação de funções (SoD) | 8 | **5** | Usuários `U021`, `U035`, `U043`, `U099`, `U141` (via papel ou permissão efetiva — premissa `A4`). |
| **R03** | Ativo sem classificação/proprietário | 30 | **7** | `DA18` (sem proprietário), `DA20` (sem classificação) + 5 classificações divergentes. |
| **R04** | Compartilhamento/retenção fora da política | 130 | **65** | 46 destinos não aprovados + 16 proteções insuficientes + 3 retenções ausentes (`DA18`, `DA20`, `DA23`). |
| **R05** | Caso de IA sem controles/fontes aprovadas | 64 | **25** | 6 `Guardrail_Ausente`, 2 `Acesso_Excessivo`, 4 `Fonte_Nao_Aprovada`, 12 `Fonte_Sem_Minimizacao`, 1 `Risco_Integrado`. |
| **R06** | Autonomia de IA acima do limite | 15 | **3** | 2 `Agencia_Excessiva` (`AI06`, `AI14`) + 1 `Dado_Inconsistente` (`AI07`). |
| **R07** | Acesso remanescente de usuário desligado | 536+ | **19** | 5 usuários desligados (`U037`, `U074`, `U111`, `U148`, `U150`); usuários em licença (`U052`, `U105`) excluídos. |
| **R08** | Acesso temporário vencido | 536 | **4** | Usuários `U010`, `U018`, `U046`, `U088`. |
| **R09** | Revisão de acesso pendente/vencida | 420 | **287** | 155 revisões vencidas + 8 remoções não executadas + 124 recertificações vencidas (`low`). |
| **Total** | — | — | **431** | `44 critical`, `119 high`, `142 medium`, `126 low`. |
