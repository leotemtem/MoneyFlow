# Security Policy

## Supported versions

MoneyFlow is an early-stage (alpha) project. Security fixes are applied to the
latest `main` and the most recent release only.

| Version | Supported |
| --- | --- |
| latest `main` / newest release | ✅ |
| older releases | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Instead, report privately using GitHub's **"Report a vulnerability"** feature
(Security → Advisories) on this repository, or contact the maintainer through the
repository's GitHub profile.

> Replace this line with a dedicated security contact address if you set one up:
> `SECURITY CONTACT: <your-email-here>`.

Please include:
- a description of the issue and its impact,
- steps to reproduce **using synthetic data only**,
- affected version/commit.

We aim to acknowledge reports within a reasonable time and will coordinate a fix
and disclosure timeline with you.

## Handling secrets

- Never commit `.env`, API keys, database passwords, or tokens.
- Configuration is environment-driven; keep secrets in a local `.env` (git-ignored)
  or your platform's secret manager.
- `scripts/scan_secrets.sh` runs in CI and pre-commit as a best-effort screen —
  it is not a substitute for care.

## Financial-data privacy

- Do not include real transaction data, statements, or account details in bug
  reports, issues, pull requests, or test fixtures. Use synthetic data.
- The default configuration keeps data local (SQLite, AI disabled). Enabling a
  **remote** AI endpoint sends a summary of your financial figures to that
  endpoint — review your provider's policies first, or use a local endpoint.

## Known security caveats

- Passwords are hashed with **Argon2id** (salted, via `argon2-cffi`). This is
  still an educational project, so review the authentication flow before relying
  on it for real multi-user deployments.

## Dependencies

- Keep dependencies reasonably current. Report vulnerable transitive dependencies
  via the process above. CI is a good place to add automated dependency scanning
  (e.g. `pip-audit`) for deployments.
