# zenn-content
コバヤシWEBシステム（個人事業）の技術ブログ。Zenn(https://zenn.dev)とGitHub連携で自動公開。
記事は `articles/*.md`。Hermes Agentが第2の脳(Obsidian)とyutakaの経歴から下書き生成→人間レビュー後に published:true でpush。

## 公開ペースの制約（2026-08-03 実測）
Zennは**1日に1本しか公開されない**（当アカウントの全履歴で1日2本以上になったことがない）。
pushを1日に複数回しても、公開されるのは最初の1回分のみで、残りは翌日以降に順次繰り越される。
そのため記事の生成ペースも1日1本に合わせる（`/srv/ops/hermes-jobs/zenn_daily.py` の `POSTS_PER_DAY`）。
