# Architecture

MoneyFlow is a Streamlit application organised as an installable package under
`src/moneyflow/`. The guiding principle is that the **deterministic core**
(parsing, analytics, persistence, auth) is fully independent of the **optional AI
layer**.

## Layers

```
UI (Streamlit)          ui/                 pages, components, theme
  │  calls
Services                services/           file_processor, subscription_service, llm_service
  │  orchestrates
Domain                  analytics/          analyzer, subscriptions, unusual_rules
                        parsing/            csv_parser
                        auth/               handler, validators
  │  reads/writes
Data access             database/           models (ORM), handler (DAO)
Configuration           config/             settings (env-driven)
Optional AI             ai/                  base, prompt_builder, providers, factory
```

- **`config/settings.py`** — single source of truth for configuration, read from
  environment variables with safe defaults (local SQLite, AI disabled). Cached via
  `lru_cache`; `reset_settings_cache()` supports tests.
- **`parsing/`** — turns an uploaded CSV into a standardised DataFrame
  (`Date, Description, Amount, Type[, Balance]`), including CSV-injection
  sanitisation and Debit/Credit handling.
- **`analytics/`** — pure, deterministic computation over the DataFrame: summary
  stats, categorisation, recurring/subscription detection, unusual-transaction
  rules, budget recommendations. No I/O, no AI.
- **`auth/`** — registration/login/password change and input validation.
- **`database/`** — SQLAlchemy `models` and a `DatabaseHandler` data-access object.
  Portable across SQLite (local/tests) and PostgreSQL (production).
- **`ai/`** — the only place that talks to a language model:
  - `base.py` — `AIProvider` interface + typed errors.
  - `prompt_builder.py` — formats the deterministic summary into prompts/messages.
  - `local_mistral.py` — in-process model (lazy heavy imports).
  - `openai_compatible.py` — HTTP client for any OpenAI-compatible endpoint.
  - `factory.py` — returns the configured provider, or `None` when AI is disabled.
- **`services/`** — thin Streamlit-facing orchestration that wires the domain,
  database, and AI together and manages session state.
- **`ui/`** — page routing (`app.py`), theme (`theme.py`), reusable components,
  and per-tab page modules.

## AI is optional by construction

- The factory returns `None` when `MONEYFLOW_AI_PROVIDER=none` (the default).
- Session state stores the provider (or `None`); the sidebar only offers to enable
  AI when a provider is configured, and loading happens on demand.
- Providers raise typed errors (`AIUnavailableError`, `AIConfigurationError`,
  `AIProviderError`); the UI catches these so a failed/timed-out model never
  breaks the rest of the app.
- The heavy ML stack is imported only inside the local provider's `load()`, so
  importing the package (or running tests) never requires `torch`/`transformers`.

## Data flow (happy path)

1. User uploads CSV → `services.file_processor.process_uploaded_file`
2. `parsing.csv_parser` standardises it → DataFrame in session state
3. `analytics.*` compute the financial summary (`build_financial_data`)
4. `ui.pages.*` render dashboards from that summary
5. *(optional)* `ai` formats the summary into a prompt and calls the provider
6. *(optional)* `database.handler` persists transactions/subscriptions on request
