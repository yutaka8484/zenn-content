#!/usr/bin/env python3
"""Zenn記事のpre-flightバリデーション。
Zennは1記事でも不正があるとデプロイ全体を中断する(2026-06-17障害の真因)。
push前に articles/*.md を検査し、違反があれば該当ファイルと理由を表示して exit 1。

検査ルール(Zenn公式準拠):
- slug(ファイル名・拡張子除く): 半角 a-z0-9 と - _ のみ / 12〜50文字
- frontmatter必須キー: title, emoji, type, topics, published
- title: 1〜70文字
- type: "tech" または "idea"
- topics: 1〜5個・各文字列
- published: true/false (bool)
- emoji: 1文字以上(絵文字想定)
"""
import os, re, sys, glob

try:
    import yaml  # PyYAML
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False

ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles")
SLUG_RE = re.compile(r"^[a-z0-9_-]{12,50}$")
errors = []

# 公開記事に載せてはいけない「一般読者が到達できない内部URL/ホスト」(2026-06-17追加)。
# Tailscale限定URLを問い合わせ導線に書いてしまう事故の再発防止。
# 例: https://x1lite.tail602503.ts.net/ はTailscale参加端末しか開けない。
# ※localhost/プライベートIPはコード例で正当に使われるため、ここでは「Tailscale/内部ホスト名」に限定して誤検知を避ける。
# 検出するのは「一般読者が絶対に到達できない＝著者の私的インフラ(Tailscale/自宅サーバx1lite)」だけ。
# localhost/127.0.0.1/プライベートIPはコード例で正当に使われる(読者が自環境で動かす)ため弾かない=誤検知回避。
# 文章中の単なる語「自宅サーバーx1lite」も正当なので弾かない。URL/FQDNとして使われた時だけ検出。
FORBIDDEN_HOST_RE = re.compile(
    r"\b[A-Za-z0-9._-]*\.ts\.net\b"                       # Tailscale MagicDNS/serve (*.ts.net) ※常に到達不可
    r"|https?://[A-Za-z0-9._:-]*x1lite[A-Za-z0-9._:-]*"   # x1liteを含むURL
    r"|\bx1lite\.[A-Za-z0-9.-]+",                         # x1lite.<fqdn> 形
    re.IGNORECASE,
)

def parse_frontmatter(text):
    """先頭の --- ... --- ブロックを返す(dict)。YAMLが無ければ簡易パース。"""
    if not text.startswith("---"):
        return None, "frontmatterが --- で始まっていない"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatterの閉じ --- が無い"
    block = text[3:end].strip("\n")
    if HAVE_YAML:
        try:
            return yaml.safe_load(block) or {}, None
        except Exception as e:
            return None, f"frontmatterのYAMLパース失敗: {e}"
    # 簡易フォールバック(YAML未導入時)
    fm = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip(); v = v.strip()
        if k == "topics":
            fm[k] = re.findall(r'"([^"]+)"|\'([^\']+)\'', v)
            fm[k] = [a or b for a, b in fm[k]]
        elif k == "published":
            fm[k] = v.lower() == "true"
        else:
            fm[k] = v.strip('"').strip("'")
    return fm, None

def check(path):
    name = os.path.basename(path)
    slug = name[:-3] if name.endswith(".md") else name
    errs = []
    # slug
    if not SLUG_RE.match(slug):
        errs.append(f"slug不正(半角a-z0-9-_の12〜50字): '{slug}' ({len(slug)}字)")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, perr = parse_frontmatter(text)
    if perr:
        errs.append(perr); return errs
    for key in ("title", "emoji", "type", "topics", "published"):
        if key not in fm or fm[key] in ("", None):
            errs.append(f"frontmatter必須キー欠落/空: {key}")
    title = fm.get("title", "")
    if isinstance(title, str) and not (1 <= len(title) <= 70):
        errs.append(f"title長が範囲外(1〜70字): {len(title)}字")
    typ = fm.get("type")
    if typ not in ("tech", "idea"):
        errs.append(f'typeは"tech"か"idea": 現在 {typ!r}')
    topics = fm.get("topics")
    if isinstance(topics, list):
        if not (1 <= len(topics) <= 5):
            errs.append(f"topicsは1〜5個: 現在 {len(topics)}個")
    else:
        errs.append(f"topicsが配列でない: {topics!r}")
    if not isinstance(fm.get("published"), bool):
        errs.append(f"publishedはbool(true/false): 現在 {fm.get('published')!r}")
    emoji = fm.get("emoji", "")
    if isinstance(emoji, str) and len(emoji) < 1:
        errs.append("emojiが空")
    # 内部URL/ホスト検出(本文全体)。一般読者が到達できないリンクは公開記事に載せない。
    for i, line in enumerate(text.splitlines(), 1):
        m = FORBIDDEN_HOST_RE.search(line)
        if m:
            errs.append(f"内部URL/ホスト検出(一般読者が到達不可・公開記事に載せない): "
                        f"L{i} '{m.group(0)}' → 公開URL(例 https://zenn.dev/yutaka8484)に置換")
    return errs

def main():
    files = sorted(glob.glob(os.path.join(ART_DIR, "*.md")))
    if not files:
        print("⚠ articles/*.md が見つからない"); return 0
    bad = 0
    for p in files:
        e = check(p)
        if e:
            bad += 1
            print(f"\n❌ {os.path.basename(p)}")
            for msg in e:
                print(f"   - {msg}")
    if bad:
        print(f"\n=== バリデーション失敗: {bad}/{len(files)} 件に問題。push中止(Zennデプロイ全体停止を未然回避) ===")
        if not HAVE_YAML:
            print("   (注: PyYAML未導入のため簡易パース。正確性のため `pip install pyyaml` 推奨)")
        return 1
    print(f"✓ バリデーションOK: {len(files)}件すべて適合")
    return 0

if __name__ == "__main__":
    sys.exit(main())
