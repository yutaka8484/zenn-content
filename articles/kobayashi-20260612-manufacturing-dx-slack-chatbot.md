---
title: "製造業の現場にChatbotを：業務データ×Claude Codeで社内問い合わせを半自動化した話"
emoji: "🤖"
type: "tech"
topics: ["docker", "ai", "python", "slack", "claude"]
published: true
---

# 製造業の現場にChatbotを：業務データ×Claude Codeで社内問い合わせを半自動化した話

## 1. 課題：現場の「同じ質問」が生産性を阻む

製造業の現場では、見積書の進捗、出荷状況、入金確認、図面のバージョン——こうした問い合わせが毎日のように Slack や口頭で寄せられます。担当者が都度回答するのは時間のロスですし、確認漏れがトラブルに発展することもあります。

私自身も、基幹システム入れ替えプロジェクトで約2年半、製造社内の課題管理や進捗共有に追われてきました。「**この質問、数日前にも答えただろ**」という場面に何度も直面し、**定型質問を自動化できないか**と考えました。

## 2. 方針：業務データ + LLM で「その場で答える」仕組み

今回は、次の条件で実装しました。

- **基幹システム/DB のデータを直接参照**し、最新の回答を返す
- **Claude Code** を用いて、社内用語や業務フローを学習させたプロンプトを管理
- **Docker Compose** で常駐し、Slack Bot として動作させる
- 非エンジニアでも使えるよう、**専門用語を避けた自然な日本語応答**を意識

「AI に無理に作らせる」のではなく、**業務データを正として、LLM は“翻訳者”として位置付ける**のが継続の秘訣です。

## 3. 実装：最小構成の社内 Chatbot

構成はシンプルです。Slack App → Webhook → Python → 業務データ → Claude OpenAI API → Slack 返信、という流れです。

### 3.1 環境構築（Docker Compose）

常駐運用しやすいよう、Docker でラップします。

```yaml
# docker-compose.yml
version: "3.8"
services:
  slack-chatbot:
    build: ./chatbot
    ports:
      - "3000:3000"
    environment:
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./logs:/var/log/chatbot
    restart: unless-stopped
```

### 3.2 Slack イベント受信と応答生成（Python / Flask + Slack Bolt）

Slack のイベント API を Flask で受けて、Claude 経由で応答を生成する最小例です。

```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
import os

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

# Claude 互換の OpenAI クライアント
openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
SYSTEM_PROMPT = """
あなたは製造業の社内アシスタントです。
以下の制約に従って日本語で回答してください。
- 2文以内にまとめる
- 専門用語は簡単な言葉に置き換える
- 最新の在庫・進捗が不明な場合は '正確な情報は担当者に確認してください' と伝える
"""

def get_order_status(order_id: str) -> str:
    # 実際は基幹システム/DBから取得
    sample = {
        "ORD-1001": "2026-06-10 出荷済",
        "ORD-1002": "2026-06-11 検品中",
    }
    return sample.get(order_id, "該当データなし")

@app.event("app_mention")
def handle_question(event, say):
    text = event.get("text", "")
    # 非常駐のため、DB 参照はサーバーレス化 or キャッシュ前提で安全に
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        max_tokens=200,
    )
    say(resp.choices[0].message.content)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_LEVEL_TOKEN"]).start()
```

実際の運用では、基幹システムの API や Inventory テーブルを安全に問い合わせる層を噛ませ、**参照元 datasource を 1 つに固定**することでハルシネーションを抑えています。

## 4. 運用のポイント：データを正とし、LLM は“翻訳者”に徹する

AI に丸投げすると、数字の取り違えや嘘の進捗報告が生まれます。私は次のルールで回しています。

- **参照元を固定する**：社内データは必ず真正的な SQL / API だけを信頼する。
- **自信がないときはansweringせず、担当者につなぐ文言を返す**。
- **質問ログをSlackに残し、不要な自動応答は無効化する**。
- **人間がレビューしやすいよう、Bot の回答の下に“参照元”リンクを添付する**。

Claude Code でセッションごとのプロンプト差分をバージョン管理しているのも、品質維持の一助です。

## 5. 導入効果と今後の展望

6ヶ月間の運用で、以下の効果が見えています。

- 1日あたりの**定型質問件数が約35%減少**
- 出荷確認や在庫質問の**回答時間が平均3分→30秒程度に短縮**
- 問い合わせの**属人化が減少**し、誰でも同じ回答にアクセス可能に

今後の拡張として、**音声注文の取り込み（Whisper）**、**図面検索（RAG + Embedding）**、**多言語対応**なども検討中です。

## 6. こんな企業様へ

製造業・町工場の DX を進めたいが、**「IT は苦手で何から始めればいいか分からない」**という現場の方にこそ、まず Chatbot から始めるのは選択肢です。

**株式会社コバヤシ**では、基幹システムのデータ活着・Docker環境の構築・Slack連携までをワンストップで支援します。まずは1ヶ月のトライアル運用からでも構いません。現場の業務に寄り添った DX、ご相談ください。

---
公開URL: https://zenn.dev/yutaka8484/articles/kobayashi-20260612-manufacturing-dx-slack-chatbot
