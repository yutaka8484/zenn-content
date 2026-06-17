#!/usr/bin/env bash
# Zenn記事を git push して公開（下書き含む）。Hermes/手動どちらからも使う。
# 使い方: publish.sh "<コミットメッセージ>"
set -euo pipefail
cd /srv/workspace/zenn-content
export PATH="/usr/bin:/usr/local/bin:$PATH"
MSG="${1:-blog: update articles $(date +%F)}"

# --- pre-flightバリデーション(2026-06-17追加) ---
# Zennは1記事でも不正(slug長/title長/topics数等)があるとデプロイ全体を中断する。
# push前に検査し、違反があればここで止めて巻き添え停止を防ぐ。
PY="$(command -v python3 || true)"
if [ -n "$PY" ] && [ -f /srv/workspace/zenn-content/validate_articles.py ]; then
  if ! "$PY" /srv/workspace/zenn-content/validate_articles.py; then
    echo "‼ 記事バリデーションに失敗したため push を中止しました。上記の問題を修正してください。" >&2
    exit 1
  fi
else
  echo "⚠ validate_articles.py または python3 が無いためバリデーションをスキップ" >&2
fi

git add -A
if git diff --cached --quiet; then echo "no changes"; exit 0; fi
git commit -q -m "$MSG"
git push origin main 2>&1 | tail -2
echo "pushed: $MSG"
