# Resultados Esperados — Pacote de Validação (v0.4.0)

* **Responsáveis:** Matheus do Nascimento Gomes Vaz e Mateus Valerino Barros de Santana
* **Data de Referência:** `2026-11-05`

---

## 1. Resultados Esperados dos 8 Casos Formais

| ID | Regra(s) | Achado(s) / Comportamento Esperado | Severidade Esperada | Status / Decisão Esperada |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | `R07` *(e `R01`)* | Geração de achado `Conta_Desligada` para `U037` em `RES04` (e demais contas desligadas com acesso ativo), com rastreabilidade de aba e linha. | `critical` | `non_compliant` / **Revisão** |
| **T2** | `R03` | Geração de `Proprietario_Ausente` para `DA18` e `Classificacao_Ausente` para `DA20`. | `high` (ambos) | `non_compliant` / **Revisão** |
| **T3** | `R05` | Geração de `Guardrail_Ausente` para `AI02` apontando ausência de `proteção contra prompt injection`. | `high` | `non_compliant` / **Revisão** |
| **T4** | `R01` | Nenhum achado de `Excesso_de_Privilegio` ou `Modo_de_Acesso_Divergente` gerado para `(U001, RES01)`. | Nenhuma | Sem achado / **Conforme** |
| **T5** | `R05`, `R04` | Nenhum achado gerado para `AI12` (baixo impacto não exige `logging`) nem para `DA02` (política de retenção completa). | Nenhuma | Sem achado / **Conforme** |
| **T6** | `R08` / Exceções | 1) Geração de `Acesso_Expirado` para `(U010, RES01)` e outros 3 registros expirados;<br>2) Classificação de `EX001` (`U003/RES03`) e `EX002` (`U057/RES06`) como exceções válidas na data `2026-11-05`. | `high` (`R08`) / Mantida com mitigação (exceções) | `non_compliant` (`R08`) e `valid_exception` (`EX001`, `EX002`) |
| **T7** | `R06`, `R05` / API | 1) Geração de `Dado_Inconsistente` para `AI07` sem adivinhar `action_level`/`impact_level`, mantendo o alerta `Fonte_Nao_Aprovada` para `DA09`;<br>2) HTTP `200` em `/api/datasets/validate` com `Access-Control-Allow-Origin` válido e `GET /api/datasets` retornando lista vazia (`[]`). | `low` (`insufficient_information`) e `high`/`critical` (`Fonte_Nao_Aprovada`) | `insufficient_information` (`AI07`) + `non_compliant` (`DA09`) |
| **T8** | `R05`, `R06` / API | 1) Geração simultânea de `Risco_Integrado`, `Agencia_Excessiva` e `Acesso_Excessivo` para `AI14/DA03`;<br>2) HTTP `200` em `/api/findings` expondo `X-Total-Count` em `Access-Control-Expose-Headers`. | `critical` | `non_compliant` / **Revisão** |

---

## 2. Resultados Esperados dos 15 Casos Públicos (`casos_teste_publicos`)

| Caso | Domínio | Sujeito / Relacionado | Cenário | Categoria Esperada | Prioridade Esperada | Decisão Esperada |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC01** | Acesso | `U003` / `RES03` | Admin legado fora do baseline | `Excesso_de_Privilegio` | Crítico | Revisão |
| **TC02** | Acesso | `U037` / `RES04` | Usuário desligado com permissão ativa | `Conta_Desligada` | Crítico | Revisão |
| **TC03** | Acesso | `U099` / `SOD01` | Conflito SoD (solicitante e aprovador) | `Conflito_SoD` | Crítico | Revisão |
| **TC04** | Acesso | `U010` / `RES01` | Acesso temporário expirado | `Acesso_Expirado` | Alto | Revisão |
| **TC05** | Acesso | `U001` / `RES01` | Acesso compatível com o papel | `sem_achado` | Baixo | Conforme |
| **TC06** | Dados | `DA18` | Ativo sem proprietário | `Proprietario_Ausente` | Alto | Revisão |
| **TC07** | Dados | `DA20` | Ativo sem classificação | `Classificacao_Ausente` | Alto | Revisão |
| **TC08** | Dados | `DA02` | Política de retenção completa | `sem_achado` | Baixo | Conforme |
| **TC09** | Compartilhamento | `SH005` / `DA06` | Destino vs. aprovação | `Calcular` | Variável | Calcular |
| **TC10** | Retenção | `DA23` | Política de retenção incompleta | `Retencao_Ausente` | Alto | Revisão |
| **TC11** | IA | `AI06` | Ação crítica com execução automática | `Agencia_Excessiva` | Crítico | Revisão |
| **TC12** | IA | `AI12` | Caso de baixo impacto conforme | `sem_achado` | Baixo | Conforme |
| **TC13** | IA | `AI02` | Sem proteção contra prompt injection | `Guardrail_Ausente` | Alto | Revisão |
| **TC14** | Integrado | `AI14` / `DA03` | IA crítica + credenciais + acesso excessivo | `Risco_Integrado` | Crítico | Revisão |
| **TC15** | IA | `AI03` / `DA12` | Piloto em conformidade com exceção (`EX004`) | `excecao_valida` | Médio | Atenção |
