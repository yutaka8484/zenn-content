---
title: "製造業の会議ノートをPythonとObsidianで“活かす”自動議事録の作り方"
emoji: "🛠️"
type: "tech"
topics: ["python", "obsidian", "ai", "automation", "dx"]
published: true
---

# 製造業の会議ノートをPythonとObsidianで“活かす”自動議事録の作り方

## 1. 課題：議事録が「書いて終わり」になっていませんか？

製造業の会議では、設計変更・生産調整・品質指摘など決定事項が次々に出ます。  
メモは残っても、後から「あの日何を決めた？」「誰がアクションを持った？」と探すのに時間がかかる現場は多いです。私も木工所のDX支援で基幹システム入れ替えを率いた際、同じ課題に直面しました。

**「書く」こと自体は手間ではありません。「活かす」ところに時間がかかっている**  
それが自動化の出発点です。

## 2. 具体的な解決策：Obsidian + Python + 生成AIの最小フロー

今回ご紹介するのは、たった1本のPythonスクリプトで「会議メモ → 整形された議事録 → Obsidian Vault」まで流す仕組みです。

### フロー図（テキスト版）

```
1. 会議 rawメモ (.md) 
      ↓ Pythonスクリプト
2. LLMで要約・TODO抽出
      ↓
3. Obsidian vault に所定のスラッグで保存
```

### 動作するコード例

以下はOpenAI互換API（ローカルLLMやOpenAI等）を使って、メモを整形する最小のスクリプトです。テスト時に `http://localhost:11434/v1/chat/completions` を指定すれば、ローカル環境でも動作確認できます。

```python
import json
from pathlib import Path
from datetime import datetime

def build_prompt(raw_note: str) -> str:
    return f"""以下の会議ノートを Markdown 形式の議事録に整形してください。
- 決定事項 / アクションアイテム / 次回までの確認事項 をそれぞれセクションに分けてください。
- 参加者・日付が分かる場合は先頭に記載してください。
- 箇条書き中心で読みやすく。

会議ノート:
{raw_note}
"""

def create_minutes(raw_note_path: str, output_dir: str = "./minutes") -> str:
    raw = Path(raw_note_path).read_text(encoding="utf-8")
    prompt = build_prompt(raw)

    # --- ここを OpenAI 互換 API に置き換えて使います ---
    # ローカルの Ollama 等でも、OpenAI 互換のエンドポイントがあれば同じ要領で呼べます。
    from openai import OpenAI

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="dummy")
    completion = client.chat.completions.create(
        model="local-model",  # 例: ollama のモデル名
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    minutes = completion.choices[0].message.content

    # Obsidianに保存（slugは日付＋短縮名）
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = "meeting-minutes"
    slug = f"{today}-{safe_title}"

    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    path = out / f"{slug}.md"
    path.write_text(minutes, encoding="utf-8")
    return str(path)

# 使い方（例）
# minutes_path = create_minutes("./raw_notes/2026-06-18-meeting.md")
# print("保存:", minutes_path)
```

**1行で言えば：**  
「生の会議ノートをLLMで整形して、Obsidianに日付スラッグで保存する」ことを自動化しています。

## 3. 私が実際に使っているコツ

- **参加者・決定事項は必須キーにする**  
  後から検索しやすいよう、frontmatterの `tags` に `meeting/議事録` と `会議のトピック` を必ず入れます。

- **rawメモは残し、議事録は上書きしない**  
  ObsidianのDataviewでraw未整理メモと整形後の議事録を一覧表示すると、メモの粒度を比較できるので便利です。

- **ローカルLLM（Ollama）でテストする**  
  社外秘の情報が含まれる会議メモは、APIにそのまま投げられないケースが多いです。ローカルLLMでプロトタイプを作ってからクラウドAPIと使い分ける運用が現実的です。

## 4. なぜPython＋Obsidianなのか

- **Pythonはパイプライン構築に強い**  
  ファイル操作、API呼び出し、Markdown整形が同じ言語内で完結するので、「途中経過が見える」自動化に向きます。

- **Obsidianは「文章資産」の置き場所として最適**  
  検索・双方向リンク・タグ付けが標準で可能で、議事録を単なるドキュメントでなく“活かす情報”として再利用しやすいです。

- **株式会社コバヤシでは、自社の会議メモ定型化も支援可能です**  
  社内の会議ルールに合わせたテンプレート生成や、工程管理・木工所DXの業務フローに応じた議事録構造のカスタマイズまで対応できます。

## 5. まとめ

事務処理の自動化は“大きな investments”ではなく、小さなスクリプトから始められます。  
会議ノートをObsidianで一元管理し、Pythonで生成AIの力を借りて議事録を自動整形する仕組みは、個人でも小規模チームでも始めやすい起点です。

**製造業DXにおける「小さく始めて大きく育てる」事例**として、株式会社コバヤシへの相談も受け付けています。

- 📩 お問い合わせは公開プロフィールよりどうぞ  
- 🏠 事例：木工所DX・基幹システム入れ替え・自社サーバー運用

---

> コード例は `python` と `openai` パッケージで動作します。ローカルAPIを使う場合は Ollama 等の互換エンドポイントを指定してください。
