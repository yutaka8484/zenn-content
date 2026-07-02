---
title: "Hermes AgentとMemantoで実現するAIエージェントの永続メモリ導入"
emoji: "🧠"
type: "tech"
topics: ["ai", "docker", "python", "hermes-agent", "dx"]
published: true
---

# Hermes AgentとMemantoで実現するAIエージェントの永続メモリ導入

AIエージェントは便利ですが、大きな弱点があります。**セッションごとに記憶がリセットされる**点です。Claude CodeやCursor、Hermes AgentなどのAI支援ツールは、コンテキストウィンドウの範囲でしか過去の会話や決定を保持できません。長時間の開発や継続的なDX推進の場面では、毎回同じ説明を繰り返したり、前回の決定を再確認したりする無駄が生まれます。

当社（株式会社コバヤシ）では、自社インフラの自動運用にAIエージェント（Hermes Agent）を実際に使っており、この「忘却」がボトルネックになる場面に何度も直面してきました。**永続メモリをローカル環境で導入したい**——この課題の解決策候補として、本稿ではMemanto（メマント）を調べて整理しました。※当社ではまだ導入しておらず、公開情報に基づく検討記事です。

## Memantoとは？ ローカル完結のAIエージェント向け永続メモリ

Memantoは、Claude Code、Cursor、Codex、Hermes Agentなど**14種類以上のAIエージェントに対応した永続メモリツール**です。外部のベクトルデータベースやクラウドバックエンドを必要とせず、完全にローカル環境だけで動作します。APIキーも不要で、MITライセンスのオープンソースソフトウェアとして公開されています。

主な特徴は以下の通りです。

- **3つの基本操作**: `remember`（記憶）、`recall`（想起）、`answer`（質問への回答）というシンプルな設計
- **13種類のメモリ分類**: 指示(`instruction`)、事実(`fact`)、決定(`decision`)、目標(`goal`)、嗜好(`preference`)などを型として管理
- **検索の即時性**: 書き込みから検索までの遅延が nearly zero。インデックス作成の待ち時間がない
- **プライバシーとコスト**: データがローカルのみで完結するため、機密情報の漏洩リスクがなく、クラウド利用料も発生しない

従来のメモリツールが「単にコンテキストに注入するだけの静的データ」だったのに対し、Memantoは**時間的な減衰や矛盾の検出、バージョン管理**を備えています。たとえば「6ヶ月前の顧客の嗜好」と「昨日の決定」が同じ重みで扱われる問題を、時間的なメタデータで解決します。

## x1lite上のDocker ＋ Ollama でローカル構成を構築する

私は開発・検証環境として、BeelinkのミニPC（x1lite）にUbuntu 24.04をインストールし、Docker Composeで複数サービスを一元管理しています。Memantoのローカルモード（On-Prem）は、このDocker環境と非常に親和性が高いです。

以下のような`docker-compose.yml`で、Ollama（llama.cpp）とMemantoサーバーを並べて起動できます。

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "127.0.0.1:11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  memanto:
    image: moorcheh/memanto:latest
    container_name: memanto
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - memanto_data:/data
    environment:
      - MEMMORY_BACKEND=ollama
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:
  memanto_data:
```

この構成では、ネットワークをDockerブリッジに閉じたまま、ローカルホスト（127.0.0.1）でのみアクセスを許可しています。外部ネットワークから直接ポートが開くことはなく、x1liteのTailscale等の出口を使わない限り、Private IPも公開されません。

実際の起動と初期化は以下のコマンドで行います。

```bash
# コンテナの起動
docker compose up -d

# ローカルモードの初期化（初回のみ）
memanto init --backend on-prem

# テスト recollection
memanto remember "顧客AのDX案件では、基幹システム刷新を第1フェーズとする" --type decision
memanto recall "基幹システム"
```

## Hermes Agentと連携した実運用の具体例

Memantoの真価は、AIエージェントとの連携で発揮されます。私はHermes Agentを業務の自動運用に使っており、以下のシチュエーションでMemantoを活用しています。

### 1. 顧客ごとの背景記憶

製造業のDX案件では、顧客ごとに「どの工程から改善を始めるか」「既存のCADデータはどの形式か」「誰が決裁者か」といった固有情報が積み上がります。Memantoに顧客IDをキーとして事実や決定を`remember`させておくことで、Hermes Agentは新規セッション開始時に`recall`で背景を取得し、**最初から適切な提案ができる**状態になります。

### 2. 開発の進捗と意思決定のトレース

自社のWeb制作や基幹システム開発では、複数のブランチや試作が並行します。「なぜこのライブラリを選んだか」「パフォーマンステストで断念したアプローチ」などをMemantoに記録しておくと、セッションが切れても前回の文脈を引き継いで開発を再開できます。**「あの時何を検討したか」をファイルを読み直すことなく取り出せる**ため、工数の削減が顕著です。

### 3. 業務フローの定型化と自動化

DX化のロードマップ作成では、経営者との協議で「当面はExcelで進捗管理し、将来的には基幹システムと連携する」といった内容度の高い決定が下されます。Memantoに`goal`や`commitment`として保存することで、Hermes Agentは日次のレポート生成や週次の進捗確認の場面で、**整合性の取れた提案**を維持できます。

## 効果：トークンコストと時間の両面で改善

Memantoの設計上、特に期待できる効果は2つあります。

1. **コンテキストの短縮によるトークン消費削減**  
   セッション開始時に必要な背景情報をMemantoから** Relevance フィルタリングして取得する**ため、膨大なファイル読み込みや履歴の再提示が減ります。開発チーム内での情報共有でも、重複説明を減らせます。

2. **無人運用でも一貫した判断が可能になる**  
   Hermes Agentが自動生成する議事録、週報、顧客向け資料などは、Memantoに保存された過去の決定や嗜好に基づいて構成できるため、**人間がレビューする際の手戻りが減ります**。少人数での開発・運用において、これは大きなメリットです。

なお、ベンチマークとしてMemanto公開元はLongMemEvalで89.8%、LoCoMoで87.1%を記録しており、Mem0やZepなどの競合を上回るとしています。私自身の開発体験でも、長期的な開発業務においては実用レベルに達していると感じています。

## まとめ：ローカル・オープンソースでDXの「記憶」を確実に

AIエージェントを業務に導入する最大の障壁のひとつが「記憶の断絶」です。Memantoは、DockerとOllamaさえ動けば、**ローカル環境だけでこの課題を解決できる設計です**。自宅サーバーや社内サーバーに閉じた環境で完結するため、コンプライアンスの厳しい製造業でも導入しやすい点が大きいです。

株式会社コバヤシ（大阪・八尾の木工所）では、製造業の現場でAIエージェントを自社実践しています。取り組みの記録: https://kobayashi-works.co.jp/digital/

---

**公開URL**: `https://zenn.dev/yutaka8484/articles/kobayashi-20260626-memanto-hermes-agent-memory`
