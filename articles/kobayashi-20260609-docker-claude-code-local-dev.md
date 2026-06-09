---
title: 'Dockerで動かすClaude Code：自宅サーバーで試した堅牢なローカル開発環境の作り方'
emoji: '🛠️'
type: 'tech'
topics: ['docker', 'claude', 'ai', 'python', 'linux']
published: true
---

# Dockerで動かすClaude Code：自宅サーバーで試した堅牢なローカル開発環境の作り方

## この記事の目標
社内情シス／製造業の現場で「LLM を開発に取り入れたいが、社内ポリシーや機密の壁で手が出ない」というケースに、**自宅サーバー x Docker x Claude Code** で作った現実的な構成を解説します。

## 課題：クラウド AI をそのまま業務に使えない訳
中小企業や製造業の現場で、来年度の DX で生成 AI の導入を検討する動きが増えています。しかしすぐに実運用できない理由は、たいてい次の 3 点に集約されます。

- 機密情報を社外へ出したくない（契約図面、顧客リスト、品質記録……）
- 開発環境の依存地獄（ライブラリの衝突、OS 差分、Python 2/3 混在）
- 「誰かが動かした時だけ動く」状態が続いて技術的負債になる

私も 2025 年から始めた個人事業で、Docker と Anthropic の Claude Code を組み合わせて、**自宅の x1lite サーバー上にローカルの AI 開発環境**を作り、業務システムのオペレーションを支援してきました。今回はその実装と注意点を共有します。

## 構築の全体像
設計は「最小のリスク」を基準に 3 つの領域に切りました。

- **ホスト**: Ubuntu 24.04 が動く Beelink EliteMini（旧称 x1lite）
- **基盤**: Docker Compose + s6 overlay によるサービスの再起動自動化
- **アプリケーション**: ClawLess の WebContainers ランタイムを参考に、ブラウザ上で Claude Code を動作させる構成

セキュリティ面は、Docker ネットワークを `bridge` で分離し、ホスト側のポート 80/443 からのみ外部公開。LLM 関連コンテナは PR ビルド時のみ起動することで、常駐コストを抑えています。

## 実装：3 つの Dockerfile で環境を固定する
ハンズオンの再現性を高めるため、私は 3 つの Dockerfile を分けました。ファイルは `/srv/common/obsidian/wiki/Docker.md` メモで管理しつつ、実際の構成も git で追跡しています。

```dockerfile
# base image: CPU アーキテクチャに合わせて slim 系を使う
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 非 root で実行
RUN useradd -m appuser
USER appuser
CMD ["python", "main.py"]
```

```dockerfile
# claude-python: Claude API 呼び出し例
FROM python:3.13-slim

RUN pip install anthropic==0.39.0

COPY claude_client.py .
ENV ANTHROPIC_API_KEY=""

# API キーは run 時に docker run -e で注入
CMD ["python", "claude_client.py"]
```

```python
# claude_client.py（最小限の動作例）
import os
from anthropic import Anthropic

client = Anthropic()

def ask(message: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}],
    )
    return response.content[0].text

if __name__ == "__main__":
    result = ask("Docker の主要メリットを 3 つ、日本語で簡潔に")
    print(result)
```

ポイントは、**ホスト OS のライブラリ差分を Dockerfile で封じ込める**ことです。後日、C 拡張のあるライブラリを追加する場合も apt レイヤー固定で再現できます。

## docker compose で全体を起動する
`docker-compose.yml` は次のようにサービスを分けました。ClawLess の WebContainers ランタイムの仕組みを参考に、ブラウザ上から Claude Code を操作できるポータルも用意しています。

```yaml
version: '3.9'
services:
  llm-api:
    build: ./claude-python
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./src:/app/src:ro
    restart: unless-stopped

  web-portal:
    image: nginx:alpine
    ports:
      - "127.0.0.1:3000:80"
    volumes:
      - ./portal:/usr/share/nginx/html
    depends_on:
      - llm-api
    restart: unless-stopped
```

注意として、API キーは `.env` に記載し、git には含めません。Anthropic のダッシュボードで発行したキーを、ランタイム側にまるごと渡すのではなく、`docker compose run --rm -e ANTHROPIC_API_KEY ...` の形で都度注入する運用を推奨します。

## 自宅サーバーで得られた効果
実際にこの環境を使い始めてからのメリットを 3 つ挙げます。

### 1. 再利用性
Claude との会話ログや補助スクリプトをすべて Obsidian の Vault に保存。同じ構成を別案件にも 10 分で再利用できました。Docker イメージのレイヤーをタグ付けせずに固定することで、半年後の再現性も確保しています。

### 2. コスト構造が見える
x1lite は消費電力が小さく、1 日の Docker 起動時間あたりの電気代は数円程度です。部署単位でクラウド AI を契約する場合の 1/10 以下で済むケースも多く、小規模事業所の導入障壁を下げられます。

### 3. アップデートの恐怖が消える
`docker compose pull` で最新のバグ修正を取得しつつ、`docker compose up -d` で新しいコンテナを起動。旧イメージは `docker images` で管理し、障害時は `docker compose down` で旧バージョンに戻せます。製造業の保守運用感覚と非常に相性が良い点も、継続率が高い理由だと考えています。

## 課題と現時点の対応
構築を進める中で、次に示す点は現在進行系で改善中です。

- **Windows / Mac での再現**: ホスト OS のファイルシステム権限（Docker Desktop では rootless 挙動が異なる）で落ちやすい。`docker compose exec` でホームディレクトリを明示的にマウントします。
- **キー管理**: 本番案件では HashiCorp Vault 等と併用し、Docker Compose 自体に secrets を渡さない設計に移行予定です。
- **長期実行テスト**: 2 年単位での Dependabot 更新と、`docker compose run --rm` の end-to-end テストを CI で回すことで、破壊的変更を早期検知しています。

## まとめ
**Claude Code + Docker のローカル開発環境は、機密保持と再利用性を両立する現実的な選択肢**です。クラウド上の案件と並行して、小規模な自動化スクリプトから運用を始めることで、組織の AI リテラシーを高められます。

自宅サーバーでも、製造業の基幹システム連携でも、まずは「1 つの Docker Compose」から始めるのが最短です。私は個人事業の形で、中小企業の DX 推進・サーバー構築・業務システムの内製支援を手掛けています。機密保持の要件がある案件でも、相談内容に応じて最適な構成をご提案できます。

---

## 参考資料
- Obsidian メモ: `/srv/common/obsidian/wiki/Docker.md`
- Obsidian メモ: `/srv/common/obsidian/wiki/Claude.md`
- Anthropic Claude Docs: https://docs.anthropic.com/
