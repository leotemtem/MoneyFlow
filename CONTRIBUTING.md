# Contributing to MoneyFlow

Thanks for your interest in improving MoneyFlow! This is a small open-source
project and contributions of all sizes are welcome.

## Ground rules (please read)

1. **Never commit real financial data.** No real bank statements, account
   numbers, or transaction exports — in code, tests, fixtures, sample data, or
   screenshots. Test data must be synthetic.
2. **Never add personal or identifying information** about the project's original
   university team (names, usernames, emails, student IDs, module codes, private
   repository links, etc.). This edition is deliberately sanitised.
3. **Never commit secrets** — API keys, database passwords, tokens, `.env` files.
   Use `.env` locally (it is git-ignored).

## Environment setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install        # optional but recommended
```

## Development workflow

- Branch off `main`: `git checkout -b feat/short-description` (or `fix/…`, `docs/…`).
- Keep changes focused; avoid unrelated refactors in the same PR.
- Follow the existing structure: UI in `ui/`, orchestration in `services/`,
  deterministic logic in `analytics/`/`parsing/`, data access in `database/`,
  optional AI behind `ai/`.
- Validate input at boundaries (forms, CSV upload, DB, external endpoints).

## Code style

- Formatting and linting via **Ruff**:
  ```bash
  ruff format .
  ruff check . --fix
  ```
- Prefer type hints and small, focused functions.
- Keep the deterministic core independent of the optional AI layer.

## Tests

- Add or update tests for any behaviour change:
  ```bash
  pytest -m "not integration"
  pytest -m "integration"
  ```
- Use synthetic fixtures (see `tests/conftest.py`).
- Don't write superficial tests purely to raise coverage.

## Pull requests

- Describe the change and the reasoning; link any related issue.
- Ensure `ruff check .`, `ruff format --check .`, and the test suite pass.
- Update `README.md` / `docs/` and `CHANGELOG.md` (Unreleased section) when
  relevant.

## Reporting issues

- Use GitHub Issues for bugs and feature requests.
- **Do not** paste real transaction data or secrets into an issue. Reduce bugs to
  a synthetic, minimal reproduction.
- For security vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of
  opening a public issue.
