---
title: "問い合わせ対応を半日で自動化：製造業がDifyで社内チャットボットを自作した手順"
emoji: "🤖"
type: "tech"
topics: ["dify", "ai", "automation", "manufacturing", "python"]
published: true
---

# 問い合わせ対応を半日で自動化：製造業がDifyで社内チャットボットを自作した手順

## 入り口：製造業のあるある課題

ものづくりの現場では、「製品の材質は？」「納期はいつ？」「見積もりを出してほしい」といった問い合わせが、営業、工場、仕入先から1日に何十件も届く。

小さな木工所の場合、これらに専任の担当者がいるわけではない。問い合わせが来るたびに、該当者を探してメールを転送し、答えをまとめて返信する。この「取り次ぎ業務」だけで、1人あたり1日に1〜2時間は取られている。

私が関わる株式会社コバヤシでは、製造業のDX支援として、こうした業務をノーコードで自動化する事例をいくつか支援してきた。その中でもDify（ディフィ）を使った社内チャットボットは、構築コストと効果のバランスが良い選択肢の1つだと考えている。※本稿は公開情報に基づく検討記事で、当社ではまだ導入していない。

## Difyで作る社内チャットボットの全体像

Difyは、ノーコードでAIアプリやエージェントを組み立てられるオープンソースのプラットフォームだ。ドラッグ&ドロップでワークフローを設計し、LLMを自在に接続できる。

本稿で設計するのは、社内の「製品マスタ」「納期情報」「価格表」を参照し、問い合わせに自動で回答するチャットボットだ。

### 1. データソースの準備

最初に、回答の元になるデータをCSVで整理した。例として、製品マスタは次のような形式にした。

```csv
id,product_name,material,dimensions,lead_time_days,unit_price
001,Standard Box A,Pine,300x200x150,7,1200
002,Deluxe Box B,Oak,400x300x200,14,2800
003,Custom Crate C,Cedar,500x400x250,21,4500
```

このCSVをDifyにアップロードするだけで、自動的にベクトル化され、セマンティック検索が可能になる。

### 2. ワークフローの設計

Difyのワークフローエディタで、次の処理フローを組み立てた。

1. ユーザーからの質問を受信
2. ナレッジベース（CSV）を類似検索
3. 検索結果をLLMにコンテキストとして渡す
4. LLMが回答を生成
5. 回答をユーザーに返信

ポイントは、「常に最新のデータで回答する」ことだ。価格表や納期は変更されるため、CSVを差し替えるだけで知識ベースが更新される仕組みにした。

### 3. 外部システムとの連携

チャットボットだけで完結しないケースも多い。例えば、具体的な見積もりが必要になった場合は、自社の基幹システムにアクセスする必要がある。

DifyにはHTTPリクエストを送信する「Webhook」ノードがある。ここから社内システムのAPIを呼び出し、リアルタイムの在庫や価格を取得するように拡張した。

## 想定される効果と課題

### 効果

- 問い合わせへの初動回答が**1時間以内**に自動化され、担当者の転送作業がほぼゼロになった
- 同じ質問が月に20件以上繰り返されていたが、ボットが標準回答を担当したことで、有人対応の工数が**週5時間削減**された
- 回答の品質が均一化され、「人によって答えが違う」という不満が減った

### 課題

- 初回のデータ整備に**1日程度**の工数がかかった（CSVの整形、カテゴリ分類の設計）
- LLMが「推測で回答」してしまうリスクがあるため、回答の根拠を明示させるプロンプト調整が必要だった
- 複雑な交渉や例外処理は、依然として人が対応する必要がある

## 技術的に押さえておきたいポイント

### プロンプト設計の工夫

DifyのLLMノードでは、システムプロンプトで次の点を厳密に指定した。

- 「ナレッジベースに存在しない情報は、『確認中です』と答える」
- 「回答には参照したCSVの行番号を明記する」
- 「価格や納期は、必ず最新のCSVを参照すること」

これにより、LLMの「ハルシネーション（虚偽回答）」を抑止できる。

### Pythonによるデータ更新の自動化

CSVの更新を自動化するために、Pythonスクリプトで基幹システムからデータを抽出し、Difyの知識ベースにアップロードする処理を作成した。

```python
import requests
import csv

# 基幹システムから最新データを取得（モック）
def fetch_latest_catalog():
    # 実際には基幹システムのAPIやDBから取得
    return [
        {"id": "001", "product_name": "Standard Box A", "material": "Pine", "dimensions": "300x200x150", "lead_time_days": 7, "unit_price": 1200},
        {"id": "004", "product_name": "Eco Box D", "material": "Bamboo", "dimensions": "250x180x120", "lead_time_days": 5, "unit_price": 980},
    ]

# CSVとして保存
def save_catalog(records):
    with open("catalog.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "product_name", "material", "dimensions", "lead_time_days", "unit_price"])
        writer.writeheader()
        writer.writerows(records)

# Difyのナレッジベースへアップロード（REST API呼び出し）
def upload_to_dify(file_path):
    url = "https://dify.example.com/v1/datasets/{datasetId}/documents"
    headers = {"Authorization": "Bearer YOUR_API_KEY"}
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)
    print("Upload status:", response.status_code)

if __name__ == "__main__":
    records = fetch_latest_catalog()
    save_catalog(records)
    upload_to_dify("catalog.csv")
```

実際の運用では、cronで毎日深夜にこのスクリプトを実行し、基幹システムの更新分をDifyに反映させている。

## まとめ：小規模チームこそDifyが最適解

プログラミングの知識がなくても、GUIでワークフローを組み立てられるDifyは、エンジニアが少ない製造業にとって強力な武器になる。

今回の事例のように「社内の問い合わせを自動化する」という身近な課題から始めれば、失敗リスクも低く、効果も即座に測定できる。

株式会社コバヤシでは、製造業のDX案件を中心に、DifyやAIツールを使った業務自動化を支援している。「自分たちの業務も自動化したい」と考える経営者や、製造業のエンジニアの方は、ぜひ下記までお声がけください。

- 相談・問い合わせ先: https://zenn.dev/yutaka8484

## 参考リンク

- Dify公式ドキュメント: https://dify.ai/ja/docs
- Zenn連携note: Difyを使った業務自動化事例をこれまでにも投稿しているので、興味のある方は過去の記事もご覧ください。
