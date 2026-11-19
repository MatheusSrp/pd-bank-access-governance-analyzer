# Decisões de projeto

1. **Desconhecido ≠ violação ≠ conforme.** Valores irreconhecíveis geram `insufficient_information` (revisão humana), nunca aprovação nem alerta presumido.
2. **Rastreabilidade.** Cada achado cita aba/linha de origem; cada análise guarda `reference_date` e `coverage` por regra.
3. **Aliases de campo centralizados** em `pdbank/schema.py` e não confirmados com o dataset oficial; `get()` só expande o grupo pedido.
4. **Regras puras** (`rules.py` não conhece banco/HTTP); persistência atrás de `Repository`, com o mesmo teste de contrato para memória e SQL.
5. **Exceções:** aprovação explícita + vigência válida + objeto/regra idênticos; sem curingas; o achado é mantido como risco aceito (`valid_exception`).
6. **Importação defensiva:** nada é extraído em disco; limites de tamanho real, entradas, linhas, colunas; rejeição de caminhos inseguros, criptografia, symlink e zip bomb.
7. **Datasets/análises imutáveis**; reanálise cria novo registro (histórico).
8. **Sem IA paga**, sem autenticação padrão (acadêmico); `API_KEY` e `CORS_ORIGINS` opcionais para integração.
9. Migração de banco aditiva (colunas novas anuláveis), sem Alembic nesta versão.
