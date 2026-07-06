# 技術記事

## 概要

目的: 技術記事で専門性を示し、株式会社コバヤシの認知とシステム関連の相談・受注に繋げる。

## yutakaの強み

機械メーカーで基幹システム入替PJのプロジェクトマネージャー(受注→請求/生産管理)、製造業DX、自社サーバーのDocker運用、Claude Code・Hermes自律エージェント運用。現在は木工所を経営し製造現場でデジタルを実運用。

## 2つの記事モード

### モードA: 一般技術記事

- ネタ源: /srv/common/obsidian/wiki/ 配下(AI・LLM/Docker/Claude/Cursor/Dify/Python 等)、/srv/common/obsidian/outputs/

- 世の中の技術トピックを、実体験を交えて解説。

### モードB: 実運用技術の詳細解説

自社(株式会社コバヤシ)で実際に動いているシステムの構成・設計判断・ハマった点を、エンジニア向けに具体的に解説。

- ネタ源:
  - 会社サイトの記事: /srv/projects/kobayashi-works/hp/site/src/content/digital/*.md
  - スキャン→AI読取→会計CSVパイプライン: /srv/scan/
  - Odoo(見積〜請求・日本式帳票・弥生連携): /srv/docker-compose/odoo/ /srv/projects/odoo-contact-sync/

- 書き方: 課題→アーキテクチャ→実装の要点(動くコード/設定断片)→運用して分かったこと→まとめ。

## 記事共通の導線

「株式会社コバヤシ(大阪・八尾の木工所)では、こうしたシステムを自社実践しています。取り組みの一覧: https://kobayashi-works.co.jp/digital/ 」

## ⚠️ 実体験の捏造禁止

- 「使っている・導入した・運用している・実際に感じた」と書いてよいのは、/srv に実体(コンテナ・設定・データ)が存在するシステムだけ。

## ⚠️ 内容の禁則

- 承継元の実名(かわくす工芸)・「創業30年」等の年数主張は書かない。

## ネタ選定

既存記事と重複しないテーマを選ぶ → /srv/workspace/zenn-content/articles/ のslug一覧を確認。

## 記事の作り方

/srv/workspace/zenn-content/articles/ に新規mdを作る。

## ⚠️ Zenn制約

- slug=ファイル名(拡張子除く): 半角 a-z0-9 とハイフン/アンダースコアのみ・12〜50文字。

## 公開

bash /srv/workspace/zenn-content/publish.sh "blog: <記事タイトル>" を実行 → git push → Zennが自動公開。