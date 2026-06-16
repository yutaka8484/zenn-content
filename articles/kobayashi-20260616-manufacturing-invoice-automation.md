---
title: "製造業の請求書業務をPythonで自動化した話: 基幹入れ替えPJの実録"
emoji: "📄"
type: "tech"
topics: ["python", "manufacturing", "automation", "dx"]
published: true
---

# 製造業の請求書業務をPythonで自動化した話：基幹入れ替えPJの実録

小さな製造業でも「請求」には人件費がかかる。
月に1回とはいえ、案件ごとに金額を拾い、消費税を乗せ、PDFや出力し、メールで送る。本来の業務の合間にやる作業は、小さなミスを生みやすい。
私が基幹システム入れ替えPJのリーダーをした際に真っ先に着手したのが、**受注から請求までのフローの自動化**だった。

この記事では、当時に実際に作った業務の型と、Pythonで再現可能な自動化のアプローチを紹介する。

## 1. 自動化のきっかけ: 手作業の“見えないコスト”

2年半のプロジェクトの間、受注から請求までに以下の工程が毎月発生していた。

- 案件ごとの売上データを集計
- 請求書PDFの作成
- PostgreSQLへの記帳
- メール送信

Excelで柔軟に集計できる一方、PDF化と送信は手作業で重複しやすく、漏れや遅延の原因になった。

> これらの工程の**「間違いを減らす」「リードタイムを短くする」**ことが自動化の目的だった。

## 2. 方針: 既存の文脈を維持しながらできるところから

当時の基幹システムは運用しつつ、請求フローだけをPythonでカプセル化するアプローチを選んだ。

- 売上データはPostgreSQLに統一
- 金額計算ロジックはPythonで定義
- 請求書PDF生成を自動化
- メール送信をPythonから実行

「人とシステムの分業」を明確にし、自動化は安全装置として動かした。

## 3. Pythonで再現する請求フロー

ここでは、実際のコードに近い形で、受注リストから請求書PDFを生成するミニマルな例を示す。

```python
from dataclasses import dataclass
from datetime import date

@dataclass
class Order:
    id: str
    client: str
    amount: int
    tax_rate: float = 0.10

def build_invoice_rows(orders: list[Order]) -> list[dict]:
    total = sum(order.amount for order in orders)
    tax = int(total * 0.10)
    return {
        "client": orders[0].client,
        "items": [
            {"id": o.id, "amount": o.amount} for o in orders
        ],
        "subtotal": total,
        "tax": tax,
        "total": total + tax,
        "issue_date": date.today().isoformat(),
    }

orders = [
    Order("A001", "株式会社サンプル", 180000),
    Order("A002", "株式会社サンプル", 120000),
]

invoice = build_invoice_rows(orders)
print(invoice)
```

例の出力:

```json
{
  "client": "株式会社サンプル",
  "items": [{"id": "A001", "amount": 180000}, {"id": "A002", "amount": 120000}],
  "subtotal": 300000,
  "tax": 30000,
  "total": 330000,
  "issue_date": "2026-06-16"
}
```

このあと `reportlab` や `pdfplumber` でPDF化し、SMTPライブラリで送信する流れに接続できる。

実際の業務では、PDFテンプレートを1枚作成すれば同じフォーマットで量産できるため、「請求書作成の専門家」を新たに雇うよりはるかに高速だ。

## 4. 運用した結果: “属人化の解消”が最大のメリット

自動化だけが目的ではない。
**「誰がやっても同じ結果になる」** ようにフローを固定化したことが、長期的に大きな価値になっている。

- 新人でも請求書作成を即戦力化
- 習慣化したマニュアル作業の工数を削減
- 計算ロジックの一元管理によるミス撲滅

金額計算や出力条件をコードで管理することで、変更があったときも「コードを修正すれば全案件に適用される」という強さが得られる。

## 5. ここから始める: 自社でも“最初の一手”を

何も全社的に一気に置き換える必要はない。
Pythonで構築した“請求カプセル”を一部署に導入し、数ヶ月運用して効果を数字で掴む。そのあとに他部署や他フローへ広げていけばよい。

DXは、小さく始めて検証する投資である。

## 6. コバヤシWEBシステムへの相談

製造業における基幹業務の自動化や、Pythonを用いたDX推進は、コバヤシWEBシステムが得意とする領域です。
ご興味があれば、まず30分のオンライン相談で現状の課題を整理しましょう。

- 相談ページ: https://note.com/yutaka8484

---

あなたの会社の“請求業務のムリ・ムダ”を、小さな自動化から解決しませんか。
