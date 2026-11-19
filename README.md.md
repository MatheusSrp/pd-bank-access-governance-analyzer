<div align="center">

# 🛡️ PD Bank

### Access & Governance Analyzer

**Inteligência em governança de acessos, proteção de dados e segurança no uso de inteligência artificial.**

Projeto acadêmico de análise de governança desenvolvido para um cenário bancário fictício. A plataforma transforma datasets estruturados em **achados rastreáveis, indicadores de risco e recomendações para revisão humana**.

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Suportado-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Status:** Em desenvolvimento · **Versão do backend:** v0.4.0 · **Interface:** React + TypeScript

</div>

---

## 📌 Sobre o projeto

O **PD Bank Access & Governance Analyzer** é uma plataforma web de apoio à auditoria e à governança de um banco fictício. O sistema recebe datasets em formatos estruturados, executa regras determinísticas e apresenta resultados para investigação, priorização e tomada de decisão.

O foco não é realizar operações financeiras, mas **identificar possíveis desvios de controle** em três dimensões: identidade e acesso, proteção de dados e governança de IA.

> **Diferencial:** cada achado pode apresentar regra acionada, severidade, evidência, origem na planilha, impacto e recomendação. O resultado auxilia a revisão humana; não revoga permissões nem modifica os dados auditados automaticamente.

## 🎯 Objetivos

- Identificar permissões fora do baseline RBAC e conflitos de segregação de funções (SoD).
- Detectar acessos indevidos, temporários vencidos e revisões pendentes.
- Avaliar classificação, propriedade, compartilhamento e retenção de dados.
- Verificar controles, fontes e níveis de autonomia em casos de uso de IA.
- Oferecer importação de datasets, execução de análises, indicadores e relatórios.
- Manter rastreabilidade dos achados para apoiar investigação e revisão humana.

## 🧩 Módulos do sistema

| Módulo | Responsabilidade |
|---|---|
| **Dashboard executivo** | Indicadores, distribuições e visão geral dos achados |
| **Datasets** | Importação e validação de arquivos XLSX, CSV e ZIP |
| **Análises** | Execução do motor de regras e histórico de resultados |
| **Achados** | Consulta, filtros, severidades, evidências e recomendações |
| **Governança de acessos** | RBAC, SoD, acessos de usuários e revisões |
| **Proteção de dados** | Classificação, responsáveis, compartilhamento e retenção |
| **Governança de IA** | Guardrails, aprovação, fontes de dados e autonomia |
| **Relatórios** | Exportação dos resultados em JSON e CSV |

## 🔍 Motor de regras

| Regra | Análise |
|---|---|
| **R01** | Permissões acima do baseline RBAC |
| **R02** | Conflitos de segregação de funções (SoD) |
| **R03** | Ativos sem classificação ou responsável |
| **R04** | Compartilhamento ou retenção inadequados |
| **R05** | Controles e guardrails insuficientes em IA |
| **R06** | Autonomia excessiva em casos de uso de IA |
| **R07** | Usuários inativos ou desligados com acesso remanescente |
| **R08** | Acessos temporários vencidos |
| **R09** | Revisões de acesso pendentes, vencidas ou reprovadas |

O motor considera exceções válidas, situações de informação insuficiente e cobertura de avaliação por regra. Os resultados **não substituem uma auditoria humana**.

## 🏗️ Arquitetura

```text
┌───────────────────────────────────────────────────┐
│              FRONTEND — React + Vite              │
│ Dashboard · Datasets · Análises · Achados         │
│           http://localhost:5173                   │
└─────────────────────────┬─────────────────────────┘
                          │ HTTP / JSON
                          ▼
┌───────────────────────────────────────────────────┐
│                BACKEND — Flask API                │
│ Importação · Validação · Regras R01–R09           │
│           http://localhost:8080                   │
└─────────────────────────┬─────────────────────────┘
                          │ SQLAlchemy
                          ▼
┌───────────────────────────────────────────────────┐
│             SQLite (local) / PostgreSQL           │
└───────────────────────────────────────────────────┘
```

O frontend e o backend são executados separadamente e se comunicam pela API REST. A interface não implementa regras de negócio nem cria endpoints próprios.

## 🛠️ Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | React 18, TypeScript 5.7, Vite 6 |
| Estilização e UI | Tailwind CSS, Lucide React |
| Gráficos | Recharts |
| Navegação | React Router |
| Backend | Python 3.10+, Flask |
| Persistência | SQLAlchemy, SQLite, PostgreSQL |
| Testes | Pytest / unittest |
| Infraestrutura | Docker, Docker Compose |
| Versionamento | Git e GitHub |

## 🚀 Como executar localmente

### Pré-requisitos

- Python 3.10 ou superior.
- Node.js e npm compatíveis com as dependências do frontend.
- Git.
- Docker Desktop **opcional** para executar com PostgreSQL.

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/pd-bank-access-governance-analyzer.git
cd pd-bank-access-governance-analyzer
```

Substitua `SEU-USUARIO` pelo proprietário real do repositório.

### 2. Backend — terminal 1 (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:CORS_ORIGINS = "http://localhost:5173"
python app.py
```

- **API:** http://localhost:8080
- **Saúde:** http://localhost:8080/api/health
- **Documentação Swagger:** http://localhost:8080/docs

O banco padrão de desenvolvimento é SQLite. Não é necessário instalar PostgreSQL para a primeira execução local.

### 3. Frontend — terminal 2

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

- **Interface web:** http://localhost:5173

Confirme no arquivo `frontend/.env` que `VITE_API_BASE_URL` aponta para `http://localhost:8080`.

### 4. Fluxo de demonstração

1. Acesse a interface no navegador.
2. Importe um dataset compatível.
3. Execute uma nova análise.
4. Consulte os indicadores e os achados.
5. Abra um achado para visualizar suas evidências.
6. Exporte os resultados em JSON ou CSV.

### Alternativa: Docker + PostgreSQL

```bash
docker compose up --build
```

Antes de usar Docker, copie `.env.example` para `.env` e configure as variáveis necessárias, especialmente a senha do PostgreSQL. O frontend continua sendo executado separadamente em desenvolvimento.

## 🧪 Testes e verificações

Na raiz do projeto:

```bash
python -m pytest -q
```

No diretório `frontend/`:

```bash
npm run build
```

Os comandos acima devem ser executados pelos colaboradores antes de abrir um Pull Request. **Não presumimos que testes e build passaram em todas as máquinas:** consulte os resultados da execução mais recente.

O backend inclui documentação adicional em [`docs/API.md`](docs/API.md) e um relatório de validação em [`docs/v0.4.0-relatorio.md`](docs/v0.4.0-relatorio.md).

## 📂 Estrutura do repositório

```text
pd-bank-access-governance-analyzer/
├── frontend/               # Aplicação React + TypeScript
│   ├── src/api/            # Cliente HTTP e adaptadores
│   ├── src/components/     # Componentes visuais reutilizáveis
│   ├── src/pages/          # Páginas da aplicação
│   └── package.json
├── pdbank/                 # Regras, importação, API e persistência
├── tests/                  # Testes do backend
├── scripts/                # Ferramentas de validação
├── docs/                   # Contratos, relatórios e decisões técnicas
├── app.py                  # Entrada da aplicação Flask
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

## 👥 Equipe

| Integrante | Papel no projeto | GitHub |
|---|---|---|
| Abrão Filipi dos Santos | A definir | A adicionar |
| Caio Cesar Leandro Amorim | A definir | A adicionar |
| Danilo Gabriel Diniz e Silva | A definir | A adicionar |
| Boniek Araújo dos Santos Júnior | A definir | A adicionar |
| João Rafael Morato Uchoa Cavalcanti | A definir | A adicionar |
| Alisson da Silva Santana | A definir | A adicionar |
| Alice Maria Sena Pereira | A definir | A adicionar |
| Mateus Valerino Barros de Santana | A definir | A adicionar |
| Matheus do Nascimento Gomes Vaz | A definir | A adicionar |
| Maria Larysse Yasmin Lira Pereira | A definir | A adicionar |
| Letícia Gomes da Silva | A definir | A adicionar |
| Marcio Aureliano Pedro da Silva | A definir | A adicionar |

> Os papéis e perfis do GitHub serão preenchidos após a divisão das atividades, evitando atribuições não confirmadas.

## 🤝 Colaboração e fluxo de trabalho

1. Crie uma issue para a tarefa ou escolha uma já existente.
2. Abra uma branch a partir de `main`, por exemplo `feat/dashboard-indicadores` ou `fix/importacao-xlsx`.
3. Faça commits pequenos e descritivos.
4. Execute os testes relacionados à alteração.
5. Abra um Pull Request explicando o que mudou e como validar.
6. Aguarde a revisão antes de mesclar na `main`.

**Sugestões de labels:** `frontend`, `backend`, `bug`, `testes`, `documentacao`, `integracao`, `prioridade-alta`, `good-first-issue`.

## 🔐 Segurança e limitações

- O projeto utiliza **dados fictícios** para fins acadêmicos.
- Não envie `.env`, credenciais, tokens ou bancos locais ao GitHub.
- O backend pode executar sem autenticação em desenvolvimento; **não o exponha publicamente dessa forma**.
- A análise é baseada em regras e recomendações; não executa alterações automáticas em permissões ou dados.
- A compatibilidade e o funcionamento completo devem ser revalidados após cada integração relevante.

## 📄 Licenciamento e créditos

Projeto acadêmico em desenvolvimento. A licença de distribuição será definida após confirmar a autoria e as permissões de reutilização dos componentes incorporados. Contribuições e materiais de terceiros devem manter os créditos e avisos de licença aplicáveis.

---

<div align="center">

### 🛡️ PD Bank — Access & Governance Analyzer

**Da evidência à decisão: governança mais clara, riscos mais visíveis.**

</div>
