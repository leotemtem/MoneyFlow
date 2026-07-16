#!/usr/bin/env bash
# Lightweight guard against committing secrets or personal financial data.
# Exits non-zero if a tracked file looks like a secret, database, env file, or
# real transaction data. This is a best-effort screen, not a replacement for a
# dedicated scanner such as gitleaks or trufflehog.
set -uo pipefail

fail=0

# Files that must never be tracked.
blocked=$(git ls-files | grep -Ei '(^|/)\.env$|(^|/)\.env\.[^e]|\.db$|\.sqlite3?$|\.dump$|/users\.json$|\.glb$|\.safetensors$|\.gguf$' || true)
if [ -n "$blocked" ]; then
  echo "ERROR: these files should not be tracked (secrets/data/binaries):"
  echo "$blocked"
  fail=1
fi

# Content patterns that look like live credentials.
if git grep -nEI 'postgres(ql)?://[^ ]*:[^ @]+@' -- '*.py' '*.md' '*.toml' '*.yml' '*.yaml' 2>/dev/null \
      | grep -vE 'user:password@|username:password@|\[password\]|user:pw@host'; then
  echo "ERROR: possible hard-coded database credentials found above."
  fail=1
fi

if git grep -nEI '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
      -- . ':(exclude)scripts/scan_secrets.sh' 2>/dev/null; then
  echo "ERROR: possible API key / private key found above."
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "scan_secrets: no tracked secrets or financial data detected."
fi
exit "$fail"
