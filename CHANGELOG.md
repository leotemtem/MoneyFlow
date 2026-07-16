# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

This is the initial standalone open-source edition of MoneyFlow, extracted and
sanitised from a collaborative university project.

### Added
- Standalone `src/moneyflow/` package with clear layering: `config`, `parsing`,
  `analytics`, `auth`, `database`, `ai`, `services`, `state`, `ui`.
- Centralised, environment-driven configuration (`moneyflow.config.settings`).
- Optional AI provider abstraction (`moneyflow.ai`): a common interface with a
  local-model provider and an OpenAI-compatible HTTP provider, selected via a
  factory. **AI is disabled by default and never required.**
- Zero-configuration startup: defaults to a local SQLite database.
- Financial disclaimers and clear separation of AI-generated text from
  deterministic figures.
- MIT `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `THIRD_PARTY_NOTICES.md`, and this changelog.
- `pyproject.toml` packaging with `postgres`, `local-ai`, and `dev` extras.
- Ruff configuration, pre-commit hooks, and a best-effort secret/data scan.
- GitHub Actions CI hardened for a public repository: least-privilege
  `permissions`, concurrency cancellation, pip caching, per-job timeouts,
  lint, tests across Python 3.10–3.12 with a coverage gate and uploaded
  coverage report, an application import **and** Streamlit boot smoke test,
  a package build + `twine` metadata check, `gitleaks` plus the custom
  secret/data scan, and an advisory `pip-audit` dependency audit.
- CodeQL security analysis workflow and Dependabot updates (pip + Actions).
- Synthetic sample data (single-amount and Debit/Credit formats) and a
  synthetic-data generator script.
- Tests for the configuration layer and the AI provider abstraction, including
  AI failure, timeout, misconfiguration, and disabled-by-default behaviour.

### Changed
- Reorganised the previous flat module layout into an installable package and
  rewrote imports accordingly.
- Split the monolithic database module into ORM `models` and a data-access
  `handler`; the handler now falls back to a configured SQLite default.
- Extracted the AI prompt-building logic into a provider-agnostic module.
- Made database logging avoid printing transaction data.
- Extracted Streamlit theming into a dedicated `ui/theme` module.

### Removed
- All university-specific material (assessment PDFs, meeting minutes, project
  outline, GitLab CI, setup/process docs).
- Private/identifying details of the original project team (emails, usernames,
  student IDs, private links). A names-only acknowledgement of group members is
  retained at the maintainer's request.
- Real/local credentials, the local database, stored user records, caches,
  virtual environments, and the oversized binary logo assets.
- Unused dependencies (`scikit-learn`, `langchain`) that were not referenced by
  the code.

### Security
- Replaced SHA-256 password hashing with **Argon2id** (`argon2-cffi`), with
  salted hashes and transparent rehashing on login. Resolves the CodeQL
  "weak cryptographic hashing on sensitive data" findings.
- Fixed additional CodeQL findings: a possibly-uninitialized variable in the
  optional local-model provider and an empty `except` in the sidebar.
- Added CSV upload validation notes and kept CSV-injection sanitisation.
