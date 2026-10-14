#!/usr/bin/env bash
# Secret scan: looks for known key shapes in the files git tracks and refuses secret files.
# Pattern-based, so it does not find everything: read `git diff --staged` before every commit.
# Runs in CI and locally:
#
#   bash scripts/check-secrets.sh
#
# Copied from avoq/scripts/check-secrets.sh (same scan as HomeTeam, adr.ht.014).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

error=0

forbidden=$(git ls-files | grep -E '(^|/)(\.dev\.vars|\.env)(\.|$)' | grep -vE '\.example$' || true)
if [ -n "$forbidden" ]; then
  echo "Secret file in git:"; echo "$forbidden"; error=1
fi

patterns=(
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  're_[A-Za-z0-9]{8,}_[A-Za-z0-9]{16,}'
  '(sk|rk)_live_[A-Za-z0-9]{16,}'
  'sk-[A-Za-z0-9_-]{20,}'
  'whsec_[A-Za-z0-9]{24,}'
  'gh[pousr]_[A-Za-z0-9]{36}'
  'github_pat_[A-Za-z0-9_]{50,}'
  'AKIA[0-9A-Z]{16}'
  'xox[abprs]-[A-Za-z0-9-]{10,}'
  '(api[_-]?key|api[_-]?token|secret|password|passwd)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9_./+=-]{20,}["'"'"']'
  'TOKENFACTORY_API_KEY=[^[:space:]]+'
)
for p in "${patterns[@]}"; do
  hits=$(git grep -nIiE -e "$p" -- ':!uv.lock' ':!scripts/check-secrets.sh' || true)
  if [ -n "$hits" ]; then
    echo "Possible secret (pattern: $p):"; echo "$hits" | cut -c1-200; error=1
  fi
done

if [ "$error" -ne 0 ]; then
  echo "Secret scan: FINDINGS. Remove the secret and revoke it at the service."; exit 1
fi
echo "Secret scan: no findings."
