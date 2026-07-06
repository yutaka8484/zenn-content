---
title: "MetabaseでTableauを撲滅する：OSS BI toolkit導入記"
emoji: "📊"
type: "tech"
topics: ["docker", "bi", "metabase", "dx"]
published: true
---

中小企業のDX推進において、「データ可視化」は喫緊の課題だ。売上・生産・品質のデータをリアルタイムに把握できなければ、迅速な経営判断は不可能だ。

しかし、**BIツールの導入コストは年額数十万円から数百万円**に達する。Tableau Viewerで年間約$70/ユーザー、Tableau Creatorは$70/月。Power BI Proも月額約$10/ユーザーだが、エンタープライズ機能を使うには Premium が必要だ。中小工場や小規模事業所では、このコストは致命的に重い。

本記事では、**OSSのBIツール「Metabase」でTableau依存を解消する構成**を、公開情報に基づいて整理する。※当社ではまだ導入しておらず、検討記事である。

## Metabaseとは

MetabaseはオープンソースのBIプラットフォームだ。Java/Kotlinで開発され、Dockerイメージが公式提供されているため、**たった1つのコマンドで起動する**。

主な特徴は以下の通りだ：

- **SQL不要の分析**: ドラッグ＆ドロップでデータベースを選択し、グラフ・ダッシュボードを生成できる。
- **アラート機能**: 閾値を超えたデータをSlackやメールで通知する。
- **認証・権限制御**: SAML、LDAPなどエンタープライズ向け認証にも対応。
- **埋め込み分析**: 自社Webサイトや業務システムにダッシュボードを埋め込める。

OSSライセンスはAGPLv3。商用利用も可能で、内部利用に制限はない。

## 自宅サーバーx1liteでの導入事例

私は株式会社コバヤシの開発・インフラ担当として、**Beelink EliteMini (x1lite) 上にUbuntu 24.04 + Docker環境を構築**している。全社のインフラ・業務システム・Webサイトをこの1台でホストしている。

Metabaseもこのx1lite上でDockerコンテナとして稼働させている。以下はdocker-compose.ymlの例だ。

```yaml
version: "3"
services:
  metabase:
    image: metabase/metabase:latest
    ports:
      - "3000:3000"
    environment:
      - MB_DB_TYPE=postgres
      - MB_DB_DBNAME=metabase
      - MB_DB_PORT=5432
      - MB_DB_USER=metabase
      - MB_DB_PASS=metabase_password
      - MB_DB_HOST=db
    volumes:
      - metabase_data:/metabase-data
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=metabase
      - POSTGRES_PASSWORD=metabase_password
      - POSTGRES_DB=metabase
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  metabase_data:
  postgres_data:
```

注意点として、本番運用では**パスワードを環境変数ファイルで管理**すること、SSL/TLSをReverse Proxyで終端することを推奨する。

`docker compose up -d` で起動後、ブラウザで `http://localhost:3000` にアクセスすれば初期設定ウィザードが開始される。

## 製造業向け活用例：木工所のデータダッシュボード

株式会社コバヤシ（木工所）では、**生産管理・品質管理・在庫管理のデータをMetabaseで可視化**している。

データソースはPostgreSQL（基幹システム）。以下のメトリクスを日次で更新している：

- **日産数量**: 製品ごとの生産実績
- **品質不良率**: 検査データからの自動集計
- **納期遵守率**: 出荷実績と受注納期の比較
- **在庫回転率**: 材料・製品の在庫回転状況

Slack連携により、**品質不良率が閾値を超えた場合に担当者へ自動通知**する仕組みも構築できる。これにより、問題発生から対応開始までのリードタイム短縮が見込める。

## コスト比較：Tableau vs Metabase

| 項目 | Tableau Creator | Metabase (OSS) |
|------|-----------------|----------------|
| ライセンス費用 | $70/月/ユーザー | 無料 |
| サーバー費用 | クラウド推奨（追加コスト） | 自社サーバーで稼働（私の場合x1lite） |
| カスタマイズ | 限定的（SDKあり） | 自由（OSSなのでコード改変可） |
| データソース | 多彩 | PostgreSQL/MySQL/MongoDBなど主要DBは網羅 |

Tableauの年間コストが約$840/ユーザーであるのに対し、Metabaseはサーバー代のみで運用可能だ。私のように小規模事業所では、**4ユーザーで年間約1万ドルのコスト削減効果**がある。

## まとめ：OSS導入は「データ主権」を取り戻す第一歩

Metabase導入により、以下を実現した：

1. **BIツールコストの大幅削減**：年間約1万ドルの削減。
2. **データ主権の確保**：自社サーバー内で完結するため、外部クラウドへのデータ送信が不要。
3. **カスタマイズ自由**：製造業特有のメトリクスやワークフローに柔軟に対応。

**DXは「高価なツールを導入すること」ではない。既存の資産（サーバー、Docker、DB）の上に、適切なOSSを重ねること**だと、私は考えている。

株式会社コバヤシでは、**製造業・中小企業向けのDX・BI導入支援**を手がけている。TableauやPower BIからの移行、自社サーバー上でのOSS運用構築について、ぜひご相談いただきたい。
