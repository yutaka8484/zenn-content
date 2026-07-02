---
title: "PaseoでClaude CodeもCodexも1CLIにまとめて管理する方法"
emoji: "🤖"
type: "tech"
topics: ["ai", "claude", "agent", "docker"]
published: true
---

# PaseoでClaude CodeもCodexも1CLIにまとめて管理する方法

## 導入：AIエージェントツールの乱立による管理コストの増大

Claude Code、OpenAI Codex、GitHub Copilot、Cursor……2025年以降、開発を支援するAIエージェントが急速に増えました。便利な半面、**ツールごとの認証切り替え、ワークツリーの衝突、ポートの重複** など、小規模チームや個人開発者の運用は意外と手間です。

当社（株式会社コバヤシ）でも、Docker + OllamaのローカルLLM環境を自社サーバーで運用しつつ、Claude CodeとHermesエージェントを日々の業務に活用しています。複数のエージェントを行き来していると「**1つのコマンドで、どのエージェントも同じ土俵で動かせないか**」と感じる場面があります。

その解決策の候補として、本稿では **Paseo** を調べて整理しました。※当社ではまだ導入しておらず、公開情報に基づく検討記事です。Claude Code、Codex、Copilot、OpenCode、Piなどを単一インターフェースから起動・管理できるオープンソースプラットフォームで、ローカル・VM・開発サーバーのどこでもエージェントを実行できます。

---

## Paseoとは

Paseoは、開発者が複数のコード生成エージェントを**分散インフラ上でポータブルに運用する**ためのオープンソースプロジェクトです。

- **プロバイダー非依存**: Claude Code、Codex、Cursor、OpenCode、Piをネイティブハーネスで実行するため、サブスクリプションや設定は各プロバイダー側がそのまま機能
- **どこでも実行**: ノートPC・VM・開発サーバーでエージェントを起動し、CLI・Web・モバイルから接続
- **E2E暗号化リレー**: ネットワーク越しに接続する場合もエンドツーエンド暗号化で転送
- **ポート競合の解消**: ブランチ名ベースのURLを自動生成するため、複数エージェントの並行実行でもポート被りがない
- **完全スクリプト可能**: `paseo run`、`paseo ls`、`paseo attach`、`paseo send` など、CLIから全操作を自動化

### インストールと最小セットアップ

パッケージマネージャーから1コマンドで導入できます。

```bash
npm install -g @getpaseo/cli
paseo init
```

これでデーモンが起動し、同一ネットワーク内のデバイスから操作できるようになります。

### 基本的なCLI操作

```bash
# エージェントを起動してタスクを実行
paseo run "implement user authentication"

# 特定のプロバイダーでworktreeを使って実行
paseo run --provider codex --worktree feature-x "implement feature X"

# 実行中のエージェント一覧
paseo ls

# エージェントの出力をストリームで監視
paseo attach abc123

# 実行中エージェントに追加指示
paseo send abc123 "also add tests"
```

---

## DockerでPaseoを常駐させる

自宅のDocker環境で永続化する場合、コンテナとしてデーモンを常駐させる運用が向いています。以下は最低限の、docker-compose.ymlの例です。

```yaml
version: "3.8"

services:
  paseo:
    image: "ghcr.io/getpaseo/cli:latest"
    container_name: paseo
    restart: unless-stopped
    volumes:
      - ./paseo-data:/home/user/.paseo
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
    ports:
      - "8080:8080"
    command: ["paseo", "daemon"]
    # 必要に応じて NVIDIA runtime 等も追加
```

`npm install -g` せずにコンテナの中だけで完結させたい場合にもビルドの足がかりになります。ただし2026年7月現在、公式Dockerイメージの有無や推奨ラベルは把acquisitionした情報に応じて調整してください。Docker内で実行する場合も、主要な操作はすべてCLIで処理できます。

### Docker Composeで複数エージェントを分離起動

Paseoがサポートするworktree機能と組み合わせると、ブランチごとに別々のコンテキストでエージェントを並列起動できます。

```bash
# feature-x というworktreeでCodexを起動
paseo run --provider codex --worktree feature-x "add billing module"

# feature-y というworktreeでClaude Codeを起動
paseo run --provider claude --worktree feature-y "refactor auth"
```

開発サーバーを並列起動した場合も、Paseoはブランチ名に基づいて自動的にURLを割り当てます。ポートの重複を手動で回避する手間が省けるのは、Docker Composeで複数サービスを立ち上げる場面でも楽になります。

---

## 導入を検討して見えた、メリットと注意点

### メリット1：認証と環境の統一

Claude Codeを普段使いしていると、別途Codexを試したいときに認証の切り替えが面倒です。Paseo経由にするメリットは、**各エージェントのネイティブCLIを同一のワークフローに包める**点にあります。ローカルの設定やMCPサーバーは各プロバイダー側がそのまま引き継がれるため、移行コストも低いです。

### メリット2：自宅サーバーで常駐し、外出先から操作

当社は自社サーバーにDocker環境を構築し、ローカルLLM（Ollama + Open WebUI）を運用しています。この構成にPaseoのデーモンを常駐させれば、外出先からSSHせずにエージェントへタスクを投げ、結果を確認できるはずです。E2E暗号化リレーのおかげで、トークンが平文で外に漏れるリスクも抑えられる設計です。

### 注意点1：コンテナ化時の権限とボリューム

DockerでPaseoを動かす場合、作業ディレクトリの所有権（PUID/PGID）や、ホストのGitリポジトリへのマウント方法に注意してください。特に自宅サーバーで複数のサービスを並べている場合、ボリュームの競合を避けるため、サービスごとにデータディレクトリを分けることをお勧めします。

### 注意点2：プロバイダーの利用規約

Paseo自体はOSSで独立したプロジェクトですが、利用先のClaude CodeやCodexの利用規約は各社が定めるものです。プロバイダーから見れば、Paseo経由の実行も自分でCLIを実行しているのと同等に扱われますが、大規模な商用利用では事前に規約を確認しておくと安心です。

---

## まとめ：エージェントの乗り換えやすさが、DXの速度を決める

Paseoは、** Claude Code・Codex・Copilotをダウンロードし直すことなく、CLIひとつで統合運用する** ためのツールです。ローカルサーバーとDockerを日常的に使う立場から見て、認証の一本化、ポート管理の自動化、外出先からの操作は魅力的な設計です。導入したら、実運用の結果を改めて記事にします。

株式会社コバヤシ（大阪・八尾の木工所）では、製造業の現場でAIエージェントやローカルLLMを自社実践しています。取り組みの記録: https://kobayashi-works.co.jp/digital/

---

_本記事は、2026年6月末時点のPaseo（`getpaseo/cli`）の公開情報に基づく調査・検討記事です。Claude Code / Ollamaのローカル運用は当社の実環境です。_
