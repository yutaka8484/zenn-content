---
title: "Python+Claude Codeで議事録を自動整形しObsidian/Google Sheetsへ同期"
emoji: "🗂️"
type: "tech"
topics: ["python", "obsidian", "claude-code", "automation", "dx"]
published: true
---

2026年、中小企業のDX現場で「議事録が残ったまま活用されていない」ケースをよく見かけます。
打ち合わせの記録は膨大にあるのに、次のアクションに結びつかない。
原因の多くは、**「記録する行為」と「案件として管理する行為」が分断されている**点にあります。

私は大阪・八尾の木工所で経営を支えつつ、株式会社コバヤシとして製造業のDXにも取り組んでいます。
自社工場では、基幹システム入れ替えリーダーとして**「受注→請求・生産管理・工程管理」を一元化**した実績があります。

今回はその知見を活かし、**「Obsidianに保存した議事録を、PythonとClaude Codeで案件メモへ自動変換し、Google Sheetsへ同期する」**仕組みをご紹介します。
読者は、中小企業のDX担当者・経営者、そして同様の自動化に取り組むエンジニアを対象としています。

## 1. 課題：Obsidianに埋もれた「生の議事録」たち

私は業務ノートを**Obsidian**で一元管理しています。
タグ付けやノートリンクも活用し、プロジェクトごとにフォルダを分けて管理しています。

一方で、顧客との打ち合わせで議事録をObsidianに保存すると、**「記録はあるが、次のアクションが表に出てこない」**という問題が起きます。

例えば、木工所でのDX案件では次のような課題がありました。

- 打ち合わせ内容が散在し、**「誰が・いつまでに・何を」が分からない**
- 共有Google SheetsとObsidianが二重管理になり、**更新漏れが発生**
- 議事録の整形に手間がかかり、記録する習慣自体が消えかかる

記録は資産ですが、**「すぐに案件化できる形になっていない」**状態では、DXの足かせになります。

## 2. 方針：議事録を「案件メモ」として再構築する

解決の核心は、**「議事録を案件メモへ自動変換すること」**です。
私は次の3点を設計原理としました。

| 設計原理 | 内容 |
|---------|------|
| **ポータブル** | Markdown形式で保存し、ObsidianとCSVの双方で利用可能に |
| **自動整形** | Claude Codeによるプロンプトで、議事録から案件要素を抽出 |
| **シームレス同期** | PythonスクリプトでGoogle Sheetsと双方向同期 |

**技術スタック**は次の通りです。

- Python 3.13
- Obsidian Local REST API（ローカルHTTPサーバー）
- Claude Code via API
- Google Sheets API（`gspread`）

少人数チームの強みは、このような**小さな自動化を素早く回せる点**にあります。
法人の案件でも、スモールスタートで効果を実証し、継続的に改善するスタイルを貫いています。

## 3. Python実装：議事録の整形から同期まで

### 3.1 議事録を案件メモへ整形するプロンプト

Obsidianに保存した議事録は、**次のプロンプトで案件メモへ再構成**されます。

```python
import anthropic

client = anthropic.Anthropic()

PROMPT = """
以下の打ち合わせ議事録を、案件メモ形式に整形してください。

【整形ルール】
- タイトル：案件名を分かりやすく
- 日付：YYYY-MM-DD形式
- 参加者：リスト形式
- 課題：文字列的課題
- アクション：誰が、いつまでに、何をするか
- 優先度：高 / 中 / 低
- タグ：dx, 製造業 など

【議事録】
{minutes}
"""

def format_meeting(minutes: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT.format(minutes=minutes)}],
    )
    return response.content[0].text
```

このプロンプトにより、「課題」と「アクション」が明確に分離され、**Google Sheetsの案件管理シートへそのまま流し込める形**になります。

### 3.2 Obsidian Local REST APIから議事録を取得

Obsidianには、Local REST APIプラグインを導入することで、ローカルHTTP経由でノートを取得できます。

```python
import requests

OBSIDIAN_URL = "http://localhost:27123/meeting-minutes"

def fetch_obsidian_note(note_path: str) -> str:
    resp = requests.get(f"{OBSIDIAN_URL}/{note_path}")
    resp.raise_for_status()
    return resp.json()["content"]
```

この仕組みを使うことで、**Obsidianのノートをファイルシステム経由せずに直接取得**できます。
Dockerコンテナ上で動作するPythonスクリプトからもアクセス可能なため、運用が柔軟です。

### 3.3 Google Sheetsへの同期

整形後の案件メモは、`gspread`でGoogle Sheetsへ書き込みます。

```python
import gspread
from datetime import date

def sync_to_sheets(sheet_name: str, case_data: dict):
    gc = gspread.service_account(filename="service_account.json")
    sheet = gc.open(sheet_name).sheet1
    sheet.append_row([
        case_data["title"],
        case_data["date"],
        case_data["client"],
        case_data["action"],
        case_data["owner"],
        case_data["due_date"],
        case_data["priority"],
        case_data["tags"],
    ])
```

**実際に使ってみて実感した効果**は2つあります。

1. **議事録を作る心理的ハードルが下がった**
   保存さえすれば、あとは自動で整形されるため、「とりあえずObsidianに残す」習慣が定着した。

2. **案件管理表が常に最新に保たれた**
   Google Sheets側で案件進捗を確認する機会が増え、**先回りしたフォローアップが可能**になった。

## 4. 製造業DXでの応用：木工所の事例

私は現在、大阪・八尾の木工所を事業承継し、**株式会社コバヤシ**の社長としても活動しています。

同社工場では、**「記録のデジタル化」と「業務の見える化」**を並行して進めています。
今回の手法は、工場での生産会議や設計打ち合わせでも応用可能です。

具体的には、次のような流れで活用できます。

- 設計変更の議事録 → 案件メモ化 → **図面管理システムへ自動反映**
- 生産会議の議事録 → アクション抽出 → **工程表（Google Sheets）へ自動登録**
- 顧客との仕様打ち合わせ → 課題リスト化 → **次回打ち合わせの事前共有資料を自動作成**

**公認会計士を招聘した経理管理体制**のもと、これらの記録は**会計データと独立して管理**されます。
「議事録自動化」は、財務 governance を損なわずに業務効率を上げられる点で、製造業のDXに適していると考えています。

## 5. まとめ：議事録を「資産」に変える3ステップ

今回の手法を一言でまとめれば、**「Obsidianに書きさえすれば、あとは自動で案件管理につながる」**状態を作ることです。

### 3ステップ

1. **Obsidianに議事録をMarkdownで保存**
2. **Python + Claude Codeで案件メモへ自動整形**
3. **Google Sheetsへ同期し、チームで案件管理**

このサイクルを回すことで、**「記録あるも活用されず」の状態を解消**し、中小企業のDXを着実に前に進めることができます。

---

株式会社コバヤシでは、製造業のDX支援・Web制作・サーバー構築・AI活用を一気通貫でサポートしています。
ObsidianやClaude Codeを使った業務効率化に興味がある方は、お気軽にご相談ください。

🌐 株式会社コバヤシ: ご相談はDMまたはWebサイトから

## 関連記事
- [Dockerで動かすClaude Code：ローカル開発環境の安定運用術](/yutaka8484/articles/kobayashi-20260609-docker-claude-code-local-dev)
- [基幹システムリプレースの現場から学ぶ：製造業DXのリアル](/yutaka8484/articles/kobayashi-20260613-woodworking-dx-paper-to-dashboard)
- [製造業の30日DXロードマップ：現場から経理まで](/yutaka8484/articles/kobayashi-20260615-dx-roadmap-30day-manufacturing)
