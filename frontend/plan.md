# Plano de implementação — PD Bank

## Abordagem e escopo

Construir em `/home/ubuntu/pdbank` um frontend exportável em React + TypeScript + Vite, com Tailwind CSS, React Router, Recharts e Lucide React, para ser colocado na pasta `/frontend` do repositório Flask existente. A aplicação não criará backend, banco de dados, autenticação fictícia ou endpoints novos. Todas as chamadas serão feitas por um cliente centralizado à API Flask configurada em `VITE_API_BASE_URL` (padrão local `http://localhost:8080`), com `VITE_API_KEY` opcional apenas para desenvolvimento local, explicitamente documentada como não segura no navegador.

Implementarei shell responsivo com sidebar recolhível, cabeçalho, status da API e tema escuro/claro; painel executivo; datasets e upload multipart no campo `file`; execução real de análise; histórico e detalhe da análise; busca/filtragem/paginação server-side de achados com leitura de `X-Total-Count`; detalhe de achado; páginas de governança; relatórios com exportações JSON/CSV suportadas; e configurações. As rotas e endpoints serão limitados aos informados no briefing. Sem contrato `docs/API.md` ou backend disponível, os tipos e adaptadores serão conservadores, tratarão respostas e campos opcionais com segurança e mostrarão indisponibilidade/ausência de dados, sem criar métricas, tendências, achados ou progresso artificiais. Os domínios serão obtidos do catálogo/respostas reais da API, não presumidos por mapeamento inventado.

A estrutura separará `src/api` (cliente, tipos e módulos por recurso), `src/components` (layout, gráficos, tabelas, feedback e UI), `src/pages`, `src/hooks`, `src/contexts`, `src/lib` e `src/styles`. Entrega incluirá `.env.example`, `README.md`, configuração Vite/Tailwind, manifesto de rotas em `public/manus-routes.json` e aplicação pronta para `npm install`, `npm run dev` e `npm run build`.

## Design

Estilos candidatos (probabilidades baixas, conforme decisão autônoma): terminal editorial de risco **0,06**; minimalismo de laboratório de dados **0,04**; fintech glassmorphism **0,03**. Escolha: **terminal editorial de risco**, reinterpretado para uma plataforma comercial acessível, sem estética de terminal literal.

- **Movimento de design:** enterprise SaaS de inteligência de risco, com influência editorial suíça e painéis de operações de cibersegurança.
- **Princípios:** hierarquia e densidade controlada; dados reais em primeiro plano; consistência semântica para severidades/status; acessibilidade e legibilidade antes de efeitos.
- **Filosofia de cor:** marinho profundo para foco e confiança, superfícies azul-ardósia em camadas, azul elétrico para ações, ciano para sinalização informativa, violeta reservado a ênfases e cores semânticas somente para estados.
- **Paradigma de layout:** navegação lateral persistente e área de trabalho ampla, com cabeçalho contextual e composição editorial em faixas; KPIs e gráficos condensam o panorama sem visualizações decorativas.
- **Elementos assinatura:** trilho vertical de navegação com indicador luminoso contido; pequenas marcas de “telemetria” nas etiquetas de sistema; cartões com bordas finas e cabeçalhos tipográficos compactos.
- **Interação:** respostas imediatas a filtros e navegação, ações claramente nomeadas, foco por teclado visível, skeletons apenas durante requisições reais, feedback de sucesso/erro e confirmação para ações destrutivas (nenhuma ação de backend não suportada será exposta).
- **Animação:** transições curtas e discretas para navegação, tema e abertura da sidebar; respeitar `prefers-reduced-motion`; sem gráficos animados que sugiram tendências inexistentes.
- **Tipografia:** Inter para interface e dados; escala compacta e consistente, títulos de página destacados sem gigantismo e números tabulares para métricas.
- **Essência da marca:** inteligência operacional de governança para equipes de risco e segurança financeira; precisa, sóbria e confiável.
- **Voz:** direta, objetiva e acolhedora. Exemplos: “Nenhuma análise realizada” e “Importar primeiro dataset”.
- **Logotipo:** monograma “PD” construído em dois traços de escudo/colunas, acompanhado do nome PD Bank e do subtítulo de produto.
- **Cor proprietária:** azul elétrico `#557CFF`, suavizado para estados e contraste acessíveis.

## Estrutura principal

```text
public/manus-routes.json
src/api/{client,types,datasets,analyses,findings,indicators}.ts
src/components/{layout,dashboard,charts,tables,feedback,ui}/
src/contexts/ThemeContext.tsx
src/hooks/
src/lib/
src/pages/
src/styles/
src/App.tsx
src/main.tsx
```

Frontend Vite servirá na porta de Preview declarada pelo projeto; para uso local, README documentará a API Flask em `localhost:8080`, CORS necessário no backend existente, variáveis de ambiente e build estático. Nenhum serviço gerenciado será usado.
