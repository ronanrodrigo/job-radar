<div align="center">

<!-- ![JobRadar](assets/cover.png) -->

# 📡 JobRadar iOS
### Monitor automatizado de vagas para iOS Developer

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Scraping-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Cron-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Tests](https://img.shields.io/badge/testes-363%20passing-success?style=for-the-badge)
![Status](https://img.shields.io/badge/status-em%20produção-success?style=for-the-badge)

Fork mantido por [Ronan Rodrigo](https://github.com/ronanrodrigo), a partir do projeto de Liliam Kezia Oliveira Souza.

</div>

---

## 💎 Proposta de valor

> O JobRadar iOS monitora fontes de vagas a cada três horas, reconhece títulos iOS com regras explícitas, envia alertas no Telegram e oferece um painel privado para acompanhar candidaturas.

## 📄 Resumo executivo

O radar mantém vagas em um banco Supabase compartilhado entre o coletor e o painel, sem depender de commits de um arquivo SQLite para preservar o histórico.

| Achado | Número |
|---|---|
| 📊 Vagas migradas para produção | **1.350** |
| 🧪 Testes automatizados (CI a cada push) | **363** |
| 🌎 Fontes monitoradas em paralelo | **9** |
| ⏱️ Frequência de checagem | **a cada 3h** |
| 💰 Custo de infraestrutura | **R$ 0** |

A concentração em LinkedIn é um risco medido, não ignorado: o endpoint usado não é oficial e o próprio código documenta a chance de bloqueio — por isso parte do trabalho recente foi medir o rendimento de cada fonte secundária e paginar mais fundo nelas, em vez de só empilhar fonte nova.

---

## 📸 Como chega pra você

<!-- ![Notificação no Telegram](assets/screenshots/notificacao.png) -->

Vaga de alta relevância chega na hora, com motivo da aprovação, nível e link. O resto do dia entra num resumo único, ranqueado — sem virar spam.

---

## 🗂️ Sumário

- [Como funciona (pipeline)](#-como-funciona-pipeline)
- [Arquitetura técnica](#%EF%B8%8F-arquitetura-técnica)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Como rodar](#-como-rodar)
- [Testes](#-testes)

---

## 🧭 Como funciona (pipeline)

| Etapa | O que faz |
|---|---|
| **Busca** | Varre as fontes em paralelo, com rodízio de termos pra controlar custo por ciclo |
| **Filtra** | Cargo (forte / ambíguo + qualificador / ferramenta + cargo), cidade ou mercado remoto, idioma |
| **Pontua** | Score 0–10 por vaga: cargo, ferramenta, senioridade, mercado, idioma — soma de sinais, sem IA |
| **Deduplica** | Por link e por empresa+título, pra pegar a mesma vaga republicada em fonte diferente |
| **Notifica** | Alta relevância na hora; o resto num resumo diário ranqueado, melhor vaga no topo |
| **Aprende** | Botão 👍/👎 em cada notificação — feedback vira dado pra medir precisão por fonte e por semana |

## 🏗️ Arquitetura técnica

- **Filtro em 3 níveis de confiança:** cargo inequívoco passa sozinho; cargo ambíguo (ex: "Business Analyst") só conta com qualificador de dados junto no título; ferramenta (ex: "Power BI") só conta com palavra de cargo junto — nada aprova por palavra-chave solta.
- **Score de relevância sem ML:** 5 sinais conhecidos (cargo, ferramenta, senioridade, mercado, idioma), pesos calibrados contra o histórico real do banco, não chutados.
- **Persistência compartilhada:** GitHub Actions como motor de cron e Supabase Postgres como fonte de verdade; SQLite fica para desenvolvimento e migração local.
- **Resiliente:** nunca marca vaga como "vista" sem confirmar que a notificação saiu; alerta automático se metade das fontes falhar num ciclo; heartbeat diário confirmando que o robô ainda está de pé.
- **363 testes automatizados em CI:** filtros iOS, painel, SQLite e o contrato HTTP do Supabase são verificados a cada push.

## 📁 Estrutura do repositório

obradar/
├── README.md
├── requirements.txt
├── main.py ← motor único: um ciclo de busca por perfil
├── perfis.py ← Brasil vs Internacional (dado, não lógica duplicada)
├── config.py / config_intl.py ← cargos, cidades, termos de busca, pesos
├── job.py ← Job, filtro, score de relevância
├── relatorio_precisao.py ← aprovadas/notificadas por fonte e por semana
├── database/
│ ├── database.py ← fachada de persistência e SQLite local
│ └── supabase.py ← adaptador PostgREST de produção
├── dashboard/ ← painel Flask privado
├── notifier/
│ └── telegram.py ← notificação individual, digest, botão 👍/👎
├── scrapers/ ← um módulo por fonte (LinkedIn, Gupy, Indeed...)
├── utils/
│ └── filtro.py
├── tests/ ← 73 casos, roda em CI a cada push
├── data/
│ └── jobs.db ← banco versionado (histórico de dedup)
└── .github/workflows/
├── jobradar.yml ← cron de produção (a cada 3h)
└── testes.yml ← CI

## 💻 Como rodar

```bash
git clone <repo>
cd jobradar
python -m venv venv && venv\Scripts\activate   # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Criar `.env` na raiz com `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` (via [@BotFather](https://t.me/BotFather)), depois:

```bash
python main.py --perfil ios --once
```

## 🧪 Testes

```bash
pytest tests/ -v
```

Os testes cobrem a camada de filtro, o Telegram, o painel, SQLite e o contrato HTTP do adaptador Supabase.

## Operação em produção

O fluxo de produção é: **GitHub Actions (a cada 3h) → JobRadar → Supabase Postgres ← painel Flask na Vercel**. Assim robô e painel usam a mesma base; SQLite fica reservado ao desenvolvimento local. O painel publicado está em [job-radar-ios.vercel.app](https://job-radar-ios.vercel.app).

1. No projeto Supabase, aplique a migration em `supabase/migrations/`. As tabelas criadas usam o prefixo `job_radar_`, permitindo compartilhá-lo com outros produtos.
2. Importe o histórico com `python scripts/migrar_sqlite_para_supabase.py --dry-run`; revise a contagem e execute sem `--dry-run`.
3. No GitHub, configure `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` como secrets.
4. Importe o repositório na Vercel e configure `JOBRADAR_STORAGE=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DASHBOARD_SECRET_KEY` e `DASHBOARD_PASSWORD`.
5. Faça o deploy. A Vercel detecta `app.py` como a aplicação Flask.

Para abrir o painel localmente, execute `flask --app dashboard.app run --port 5050`.

Nunca exponha `SUPABASE_SERVICE_ROLE_KEY` no navegador, JavaScript ou Git.

---

<div align="center">

*Case de portfólio em automação de dados — Python, Playwright, SQLite, GitHub Actions e engenharia de filtro sem ML.*

</div>
