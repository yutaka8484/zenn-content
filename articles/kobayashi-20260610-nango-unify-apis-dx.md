---
title: "製造業のデータサイロをNangoで統合：AIに必要なデータだけを通す実践構成"
emoji: "🛠️"
type: "tech"
topics: ["api", "ai", "dx", "integration", "nango"]
published: true
---

# 製造業のデータサイロをNangoで統合：AIに必要なデータだけを通す実践構成

「AIは便利なのに、社内のデータを渡すたびにファイル出し入れが発生する」
製造業の現場でDXを進めるとき、実はここが最初の関門になる。

私は2022年に個人事業を開業してから、基幹システムの入れ替えや生産管理の電子化を手掛けてきた。その中で、Docker＋ローカルLLMによる業務支援の環境をx1lite上に整えることはできた。しかし、**基幹システムから取得したデータを、Claude Codeや外部AIに安全に渡す仕組み**は意外と整わなかった。

今回は「データサイロをどう越えるか」という課題に対し、[Nango](https://github.com/nango/nango)というオープンソースのAPI統合基盤を組み合わせた実践例を紹介する。

## 1. Gassanな環境構築の限界

データをAIにつなぐ場合、よくあるのは「CSVやExcelで出力してプロンプトに貼り付ける」方法だ。小さい業務ならこれでも成立する。だが、製造業の基幹システムには、数百の明細、リードタイム、部品構成が含まれる。

私が実際に経験したパターンはこうだ。

- 毎朝、受注入力表をCSV出力する
- ファイルを共有フォルダに置く
- 担当者がSlackに貼る
- LLMに要約させる

これは「人を経路」にしているため、ある日 Slack の貼り間違いで古いデータが混入し、生産指示の誤りにつながった。**正規化と人為的ミスは相性が悪い**。

## 2. Nangoが解消する3つのノイズ

Nangoは、800以上のSaaS・APIを共通のインターフェースで扱えるオープンソースの統合基盤だ。

私が評価しているのは次の3点だ。

1. **OAuth 2.0フローの共通化**
   基幹システムのAPI、Google Workspaceのカレンダー、CRMのAPIがそれぞれOAuth実装を持っていても、Nangoが認証を肩代わりする。
2. **レートリミット・リトライ・型定義の肩代わり**
   外部APIとの接続で最も面倒な「429が来たときのリトライ」「型の不一致」はNango本体が吸収する。自前での小さいラッパーを量産する必要がなくなる。
3. **監査ログの一元化**
   「いつ、誰のアカウントで、どのAPIが呼ばれたか」は、統合基盤側に記録される。製造業の監査対応や「後から追えない」事故の防止に直結する。

## 3. 実装：x1lite上のDockerでNangoを動かす

私は自宅のBeelink EliteMini（x1lite）上でDockerを使い、Nangoをローカルで動作させている。最小限のDocker Compose例を示す。

```yaml
services:
  nango:
    image: nango/nango:latest
    ports:
      - "127.0.0.1:3000:3000"
    volumes:
      - ./nango-data:/app/data
    environment:
      - NANGO_DEFAULT_SECRET_KEY=${NANGO_SECRET_KEY}
      - NANGO_DB_TYPE=sqlite
      - NANGO_DB_HOST=./nango-data/nango.sqlite
    restart: unless-stopped
```

Docker Composeの手軽さは、x1liteのような小規模サーバーでテストする場合に特に有利だ。SQLiteをデータストアに選ぶことで、追加のデータベースサーバーを起動する必要がない。

次に、PythonからNangoに投げる最小限の例を示す。

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

NANGO_BASE = "http://127.0.0.1:3000"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch_from_erp(integration_id: str, connection_id: str, endpoint: str) -> dict:
    resp = httpx.get(
        f"{NANGO_BASE}/api/v1/integrations/{integration_id}/connections/{connection_id}/proxy",
        params={"endpoint": endpoint},
        timeout=20.0,
    )
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    data = fetch_from_erp("erp", "prod-main", "/api/orders?limit=10")
    print(data)
```

責務が明確に分離している。Docker Composeは「動かす仕組み」、Nangoは「認証とAPIプロキシ」、スクリプトは「業務の用途」だ。

## 4. AI活用へつなぐ具体的な流れ

Nangoを使って、実際にClaude Codeに業務データを渡す流れを簡単に説明する。

1. 基幹システムのAPIをNangoに登録し、OAuth接続を確立する
2. PythonスクリプトからNango経由で受注データを取得する
3. 取得したJSONを、秘匿キーを排除した上でLLMのプロンプトに渡す
4. Claude Codeが要約・分類・異常検知を行う
5. 結果をGoogle Sheetsや社内Wikiに返す

ポイントは、AIへ渡すデータを「最小限のスキーマに落とし込む」工程をNangoの前処理で担保することだ。たとえば機密情報となる顧客住所やコスト原価は事前に除外し、分析に必要な「品目・数量・納期」だけをLLMの入力にする。

## 5. 効果と今後の改善点

この組み合わせを試した段階で、次の効果を確認した。

- **データ出し入れの手間が減った**: CSVでの手動出力が不要になり、取得からLLM入力までが1本のスクリプトで完結する
- **認証一元化**: 複数のSaaSで独立していたトークン管理がNangoに集約され、更新漏れが減った
- **再利用性**: Docker Composeの構成とPythonスクリプトをgitで管理することで、別案件にも30分程度で流用できた

一方で改善点も残る。

- 基幹システムのAPIドキュメントが古い場合、Nango側の型定義が合わず、実行時に例外が出ることがある。この場合、Nangoのレスポンスを正規化する小さなミドルウェアを自前で用意している。
- LLMへ渡す前に機密情報を削除する整形プロセスを、Docker Composeの別サービスとして分離する予定だ。

## まとめ

**データサイロを越える最短ルートは、認証と接続を共通化すること**だ。

Nangoを使うことで、製造業の複雑なシステム群も「1つのAPI群」としてAIエージェントに渡せる。さらにDocker Composeでローカルに閉じることで、機密保持の要件にも応えられる。

私は個人事業の一環として、中小企業のDX推進・サーバー構築・業務システムのAPI設計を支援している。基幹システムとAIをどうつなぐか、具体案から相談に乗れる。

---

## 参考

- Nango GitHub: https://github.com/nango/nango
- 素のOllama＋Open WebUI環境: https://zenn.dev/yutaka8484/articles/kobayashi-20260419-ollama-openwebui-local
- Docker＋Claude Code環境: https://zenn.dev/yutaka8484/articles/kobayashi-20260609-docker-claude-code-local-dev
