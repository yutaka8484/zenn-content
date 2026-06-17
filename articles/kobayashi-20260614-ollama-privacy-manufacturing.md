---
title: "工場のデータを出さずにAIを動かす：Ollamaと自宅サーバーだけで作るローカルLLM環境"
emoji: "🏭"
type: "tech"
topics: ["ollama", "llm", "privacy", "manufacturing", "ai"]
published: true
---

# 工場のデータを出さずにAIを動かす：Ollamaと自宅サーバーだけで作るローカルLLM環境

製造業の現場では **顧客情報・受注データ・生産指示** を一度も外に出したくないケースが多い。

私は木工所の事業承継を通して「クラウドAIは便利だが、この現場のデータは出せない」と実感した。  
そこで **Ollama + 自宅サーバー x1lite + Docker** だけで、業務に潜む問い合わせをAIで処理する最小の環境を作った。

この記事ではその構成と効果、それに失敗した点を公開する。

## 1. なぜローカルLLMか？

現場の相談例：

- 「 Lloyd's register のような検査記録を、担当者に説明してほしい」
- 「受注データから、来月の生産計画の材料数を算出してほしい」
- 「クレーム内容をもとに、改善点をリストアップしてほしい」

ここに共通するのは **「外部に出すとまずいデータを相手にすること」** だ。

上位のクラウドLLMもあるが、ここは **x1lite のローカル GPU/CPU でも動作する Ollama** を選んだ。

### メリット
- データが社内から出ない
- 回線がない環境でも動作する
- モデル選びとプロンプト設計だけで導入できる

## 2. 自宅サーバーで Ollama を動かす最小構成

```
x1lite (Beelink EliteMini / Ubuntu 24.04)
 └─ Docker Compose
     ├─ ollama (llama3 + 追加モデル)
     └─ frontend (最小React: テキスト入力 + streaming)
```

### docker-compose の要点
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./models:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"

  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3000:3000"
```

**プライバシー面のポイント**

- ollama のポートを `127.0.0.1:11434` にバインド → 外部からアクセス不可
- Tailscale 内だけに公開 → 現場PCでブラウザから使える

## 3. 業務に合わせたプロンプト設計

 todavía、現場の業務データは Obsidian にメモされていたり、
docxファイルに保存されていたりする。

それらを **RAG的に使う** 設計にした：

1. 関係するファイルを `obsidian` のwikiフォルダから抽出
2. チャンク化してOllamaのプロンプトに埋め込む
3. AIの回答を保存し、後で「使えた/使えなかった」を評価

評価フローをCLIで回している：

```python
import subprocess
import json
from pathlib import Path

MODEL = "llama3"
PROMPT_FILE = Path("prompt.txt")
RESPONSE_FILE = Path("response.json")

def ask(prompt: str) -> dict:
    completed = subprocess.run(
        ["curl", "-s", "http://127.0.0.1:11434/api/generate",
         "-d", json.dumps({"model": MODEL, "prompt": prompt})],
        capture_output=True, text=True, check=True
    )
    return json.loads(completed.stdout)

if __name__ == "__main__":
    prompt = PROMPT_FILE.read_text()
    result = ask(prompt)
    # 保存: 回答全文 + timestamp
```

**実際に製造業で使ってみた結果**

| 利用シーン | 使えた率 | 課題 |
|---|---|---|
| 検査記録の要約 | 8割 | 専門用語の追加学習が必要 |
| 生産計画の試算 | 6割 | 数量の丸め誤差が大きい |
| クレーム改善案出し | 5割 | 根拠が曖昧になることが多い |

つまり **「判断の下支え」として十分使え、単体で確定させるのは難しい** という現実がある。でも現場では **「材料を出してくれるだけでも助かる」** という声が大きい。

## 4. 失敗したこと

- **GPU なしで llama3 をフルで動かした** → 1回答あたり30秒以上かかった
  - → Qwen2.5-7b + GGUF少量量子化に変更
- **Obsidianの内容を丸ごとに投げた** → トークン Limit オーバー
  - → パスを `/srv/common/obsidian/wiki/` から自動フィルタする仕組みにした
- **モデルを1つに絞りすぎた** → 現場ごとに適したプロンプト/タスクが異なる
  - → 用途ごとに軽いファインチューニングプロンプトを分ける運用に

## 5. 事業承継とAI活用の未来

事業を引き継ぐ立場で考えると、

- 「顧客と担当者の橋渡しをする窓口」をシステム化したい
- 「長年の業務知識」をAIで整理し、次の担当者に渡す

という2点が自然と求められる。

**Ollama ローカルLLM は、ちょうどその両方を叶える置き場所**として、今後も強化する予定だ。まずは「聞き方」を整え、現場の言葉をプロンプトに落とすところから。

## 6. 相談してみませんか？

コバヤシWEBシステムでは、製造業の現場に合わせた AI 環境構築・Docker 運用を支援しています。

- **「まずは1モデルだけ、社内で動かしてみたい」** という段階から伴走する。
- データを出さないまま、AIで業務を楽にするための仕組みを、一緒に考えたい。

まずは https://x1lite.tail602503.ts.net/ からお問い合わせを。  
LinkedIn でも相談受け付け中。
