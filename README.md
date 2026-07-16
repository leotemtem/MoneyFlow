# MoneyFlow

[![CI](https://github.com/leotemtem/MoneyFlow/actions/workflows/ci.yml/badge.svg)](https://github.com/leotemtem/MoneyFlow/actions/workflows/ci.yml)
[![CodeQL](https://github.com/leotemtem/MoneyFlow/actions/workflows/codeql.yml/badge.svg)](https://github.com/leotemtem/MoneyFlow/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/leotemtem/MoneyFlow/branch/main/graph/badge.svg)](https://codecov.io/gh/leotemtem/MoneyFlow)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**A local-first personal finance analysis app.** Upload a bank-statement CSV and
MoneyFlow parses it, categorises transactions, detects subscriptions and unusual
spending, and presents dashboards — all computed locally. Natural-language "AI
insights" are an **optional** add-on that you can point at a local model or any
OpenAI-compatible endpoint.

Built with Streamlit, pandas, and SQLAlchemy.

**📽️ Demo:** [Watch the demo video](https://drive.google.com/file/d/1tx3pEMpf8RdRSLAOspVtkAQVKpekROek/view?usp=drive_link)

> MoneyFlow began as a collaborative university software project. This repository
> is a separately maintained, privacy-sanitised open-source edition, maintained
> here independently. It is not affiliated with any university.

---

## ⚠️ Financial disclaimer

MoneyFlow is an **educational and personal finance management tool**. It does
**not** provide financial, tax, legal, investment, or accounting advice, and it
is not a regulated financial service. Automatically generated figures and any
AI-generated text are **informational only and may be inaccurate**. Always verify
important financial decisions independently. See [Privacy & data handling](#privacy--data-handling).

---

## Project status

**Alpha / early open-source release (v0.1.0).** The deterministic core (parsing,
analytics, dashboards, persistence, auth) is functional and covered by tests. The
AI layer is optional and experimental. This is a personal/educational project, not
a production-hardened financial product.

## Screenshots

_Screenshots are not yet included in this edition._

| View | Placeholder |
| --- | --- |
| Landing page | _add `docs/img/landing.png`_ |
| Overview dashboard | _add `docs/img/overview.png`_ |
| Transactions | _add `docs/img/transactions.png`_ |

When adding screenshots, ensure they contain **no** real names, account numbers,
transaction data, file paths, or browser-profile details.

## Features

**Working today (deterministic, tested):**
- CSV upload with automatic column detection (single `Amount`, or split `Debit`/`Credit`)
- CSV-injection sanitisation and malformed-row handling
- Transaction categorisation by merchant keywords
- Financial overview: income, expenses, net cashflow, averages
- Interactive charts (category breakdown, monthly trends, spending heatmap, running balance)
- Recurring-payment and subscription detection (with a known-service catalogue)
- Unusual-transaction detection with user-configurable rules
- Budget recommendations (50/30/20-style heuristics)
- Budget planner and savings-goal tabs
- User accounts and per-user transaction storage (SQLAlchemy; SQLite or PostgreSQL)
- Per-user daily upload rate limiting

**Experimental (optional):**
- AI insights via a **local** instruction-tuned model (e.g. Mistral 7B) or an
  **OpenAI-compatible** HTTP endpoint. Disabled by default; the app is fully
  usable without it.

**Planned / not yet implemented:**
- Analysis-history UI, transaction de-duplication, multi-file/Excel/PDF import,
  password recovery, stronger password hashing (see [Known limitations](#known-limitations)).

## Architecture overview

```
src/moneyflow/
├── config/       # centralised, environment-driven settings
├── parsing/      # CSV parsing & standardisation
├── analytics/    # analyzer, subscriptions, unusual-rule engine (deterministic)
├── auth/         # authentication + input validation
├── database/     # SQLAlchemy models + data-access handler
├── ai/           # optional AI: base interface, prompt builder, providers, factory
├── services/     # Streamlit-facing orchestration (file processing, AI enable)
├── state/        # Streamlit session-state setup
└── ui/           # theme, components, and page modules
```

Layering: **UI → services → domain (analytics/parsing/auth) → database**. AI is an
isolated, optional module behind a provider interface, so the deterministic core
never depends on it. All financial figures are computed deterministically; the AI
layer only formats those figures into prompts.

See [`docs/architecture.md`](docs/architecture.md) for detail.

## Technology stack

- **Python** ≥ 3.10
- **Streamlit** — UI
- **pandas** / **numpy** — transaction processing
- **Plotly** — charts
- **SQLAlchemy 2** — ORM (SQLite locally/in tests, PostgreSQL in production)
- **requests** — OpenAI-compatible AI calls
- Optional **torch** / **transformers** — local model (via the `local-ai` extra)

## Local setup

Requires Python 3.10+.

```bash
git clone https://github.com/leotemtem/MoneyFlow.git
cd MoneyFlow

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"          # core app + dev/test tools
cp .env.example .env             # optional; defaults work out of the box
```

Optional extras:

```bash
pip install -e ".[postgres]"     # PostgreSQL driver
pip install -e ".[local-ai]"     # local model support (large download)
```

## Environment variables

All are optional — MoneyFlow runs with zero configuration (local SQLite, AI off).

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | local SQLite (`data/moneyflow.db`) | SQLAlchemy DB URL |
| `MONEYFLOW_DATA_DIR` | `data` | Directory for the default SQLite DB |
| `MONEYFLOW_DEBUG` | `false` | Verbose/debug mode (off by default) |
| `MONEYFLOW_CURRENCY_SYMBOL` | `£` | Currency symbol for display |
| `MONEYFLOW_DAILY_CSV_LIMIT` | `10` | Per-user CSV analyses per day |
| `MONEYFLOW_AI_PROVIDER` | `none` | `none` \| `local` \| `openai` |
| `MONEYFLOW_AI_MODEL` | `mistralai/Mistral-7B-Instruct-v0.2` | Model id/name |
| `MONEYFLOW_AI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `MONEYFLOW_AI_API_KEY` | _(empty)_ | API key, if the endpoint needs one |
| `MONEYFLOW_AI_TIMEOUT` | `60` | AI request timeout (seconds) |
| `MONEYFLOW_AI_MAX_TOKENS` | `512` | Max tokens per AI response |
| `MONEYFLOW_AI_TEMPERATURE` | `0.7` | Sampling temperature |

Secrets belong only in your local `.env` (git-ignored) — never commit them.

## Database setup

- **SQLite (default):** nothing to do. A file is created at `data/moneyflow.db`
  on first run. Tables are created automatically.
- **PostgreSQL:** `pip install -e ".[postgres]"` and set
  `DATABASE_URL=postgresql://user:password@host:5432/dbname`. Tables and additive
  schema updates are applied automatically at startup.

## Running the application

```bash
streamlit run streamlit_app.py
```

Then open http://localhost:8501, register an account, and upload a CSV (try
[`sample_data/sample_statement.csv`](sample_data/sample_statement.csv)).

## Tests, linting, and type checking

```bash
pytest -m "not integration"      # fast unit tests
pytest -m "integration"          # DB / workflow tests
pytest --cov=moneyflow           # with coverage

ruff check .                     # lint
ruff format .                    # format
```

## CSV format

Columns are auto-detected (case-insensitive). MoneyFlow supports either a single
`Amount` column **or** separate `Debit`/`Credit` columns.

- **Date** — transaction date (most common formats parse)
- **Description** — merchant/description text
- **Amount** — positive = income, negative = expense _(or use Debit/Credit)_
- **Balance** _(optional)_ — running balance (enables the balance chart)

```csv
Date,Description,Amount,Balance
2024-12-01,Salary Deposit,3500.00,3500.00
2024-12-02,Tesco Supermarket,-85.50,3414.50
2024-12-06,Netflix Subscription,-15.99,3398.51
```

Full details and the Debit/Credit variant: [`docs/csv-format.md`](docs/csv-format.md).

## Synthetic sample data

`sample_data/` contains only synthetic files. Generate a larger one:

```bash
python scripts/generate_sample_data.py --months 6 --out sample_data/generated.csv
```

## AI provider configuration

AI is **off by default** and never required. To enable it:

- **OpenAI-compatible endpoint** (recommended; works with Ollama, LM Studio,
  llama.cpp, vLLM, or hosted services):
  ```bash
  MONEYFLOW_AI_PROVIDER=openai
  MONEYFLOW_AI_BASE_URL=http://localhost:11434/v1
  MONEYFLOW_AI_MODEL=llama3.1
  # MONEYFLOW_AI_API_KEY=...   # if your endpoint requires one
  ```
- **Local model** (in-process, large download):
  ```bash
  pip install -e ".[local-ai]"
  MONEYFLOW_AI_PROVIDER=local
  MONEYFLOW_AI_MODEL=mistralai/Mistral-7B-Instruct-v0.2
  ```

Then click **Enable AI insights** in the sidebar. AI output is clearly labelled
and separated from deterministic figures. If the model is unavailable or times
out, the rest of the app keeps working.

## Privacy & data handling

- **Local-first:** parsing and analytics run on your machine. Uploaded CSVs are
  held in the Streamlit session and only persisted to your database when you
  click **Save to Database**.
- **Where data lives:** the local SQLite file under `data/` (git-ignored) or your
  configured PostgreSQL server.
- **AI and your data:** if you enable the `openai` provider with a **remote**
  endpoint, a summary of your financial figures is sent to that endpoint. Use a
  local endpoint (Ollama/LM Studio) or the `local` provider to keep everything on
  your machine. AI is opt-in.
- **No telemetry:** MoneyFlow adds no analytics or tracking. Streamlit usage stats
  are disabled in `.streamlit/config.toml`.
- **Logs:** application logs avoid printing full transaction records; debug mode
  is off by default.
- `.env`, databases, uploads, logs, and model files are git-ignored.

## Known limitations

- Passwords are hashed with **Argon2id** (salted, via `argon2-cffi`). Still, this
  is an educational project — review the auth flow before any real multi-user use.
- No transaction de-duplication (re-uploading a CSV can duplicate rows).
- Categorisation and subscription detection are keyword/heuristic based.
- AI insight quality depends entirely on the model you configure.
- Not audited for production/regulated use.

## Roadmap

- Transaction de-duplication on save
- Analysis-history UI
- Additional import formats (Excel, OFX, PDF)
- Screenshots and a hosted demo

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Please **never**
commit real financial data or personal information, and report security issues
privately per [SECURITY.md](SECURITY.md).

## Licence

Released under the [MIT Licence](LICENSE). © 2026 Leo Teme Teme.

Third-party runtime attributions: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Acknowledgements

MoneyFlow began as a collaborative university software project. Thanks to the
original group members who contributed to that earlier work:

- Muhammad Iqbal
- Prabhashini Rajapakse Kankanamalage

## Project origin

> MoneyFlow began as a collaborative university software project. This repository
> is a separately maintained, privacy-sanitised open-source edition, maintained
> here independently by the current maintainer.
