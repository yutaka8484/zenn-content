#!/usr/bin/env bash
# Zenn記事を git push して公開（下書き含む）。Hermes/手動どちらからも使う。
# 使い方: publish.sh "<コミットメッセージ>"
set -euo pipefail
cd /srv/workspace/zenn-content
export PATH="/usr/bin:/usr/local/bin:$PATH"
MSG="${1:-blog: update articles $(date +%F)}"
git add -A
if git diff --cached --quiet; then echo "no changes"; exit 0; fi
git commit -q -m "$MSG"
git push origin main 2>&1 | tail -2
echo "pushed: $MSG"
