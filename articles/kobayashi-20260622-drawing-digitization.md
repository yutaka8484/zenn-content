---
title: "製造業の図面を電子化して10倍速く検索する方法"
emoji: "🛠️"
type: "tech"
topics: ["manufacturing", "dx", "django", "docker"]
published: true
---

# 製造業の図面を電子化して10倍速く検索する方法

「あの図面、どこにいった？」——製造業の現場で、紙の図面が原因の生産停止や手戻りは日常茶飯事です。私は2020年から2年半かけて、木工所の基幹システム入れ替えと並行して図面電子化に取り組みました。その結果、図面の検索時間が約10分から10秒に短縮され、年間約120時間の生産ロスを削減できました。今回は「個人でも始められる図面電子化の実践手順」を、コード例とともに紹介します。

## 1. なぜ紙図面が生産を阻害するのか

紙図面の主な問題は3つです。
1. **検索性の欠如**: ファイル名で管理されている場合、類似品番の図面を探すのに10分以上かかる。
2. **情報の孤立**: 図面とBOM（部品表）や生産実績が別管理で、連携が取れない。
3. **共同利用の困難**: 複数の製造現場で同じ図面を参照する場合、コピーを増やしたり、最新版の把握に混乱が生じたりする。

弊社（木工所）では、500点を超える紙図面が各部署に分散しており、管理コストも馬鹿になりませんでした。まずは「スキャン前の整理」から手を付けました。

## 2. スキャン前の整理：基準を決める

電子化の成否は、スキャン前の整理でほぼ決まります。以下の基準を設けました。

- **フォルダ構造**: `/{製品大分類}/{品番}/{版数}/` の3階層にする。
- **命名規則**: `{品番}-{版数}-{日付}.pdf` とする。例：`A-1234-A-20231201.pdf`
- **メタデータ**: 品名、材質、寸法、担当者をCSVで管理し、後から一括でDBに投入できるようにする。

この段階で、現場の担当者にルールを説明し、「最新版はかならず所定のフォルダに置く」運用を徹底しました。ツール以前に運用設計が重要です。

## 3. Djangoで検索システムを構築

PythonとDjangoを使い、OCRによる全文検索とタグ管理が可能なシステムを構築しました。モデルは極力シンプルに設計します。

```python
# models.py
from django.db import models

class Drawing(models.Model):
    part_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    revision = models.CharField(max_length=10)
    category = models.CharField(max_length=100)
    file_path = models.FileField(upload_to="drawings/")
    ocr_text = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma separated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.part_number} Rev{self.revision}"
```

OCRにはTesseractを採用しました。軽量で、Pythonから直接呼べるため開発サイクルが早かったのが決め手です。以下は定期的に図面を読み込み、`ocr_text`を更新する Celery タスクの例です。

```python
# tasks.py
import pytesseract
from celery import shared_task
from django.conf import settings
from PIL import Image
from .models import Drawing

@shared_task
def ocr_drawing(drawing_id):
    drawing = Drawing.objects.get(pk=drawing_id)
    image = Image.open(drawing.file_path.path)
    text = pytesseract.image_to_string(image, lang="jpn+eng")
    drawing.ocr_text = text
    drawing.save()

    # タグの自動提案（簡易版）
    suggested = []
    for keyword in ["アルミ", "ステンレス", "塗装", "組立"]:
        if keyword in text:
            suggested.append(keyword)
    drawing.tags = ",".join(suggested)
    drawing.save()
```

このタスクをCelery Beatで1日1回実行し、OCR結果とタグを最新に保っています。

## 4. Dockerで開発環境を再現可能に

インフラはDocker Composeで一元管理しました。以下の点を重視しています。

- **ローカルと本番の差分をなくす**: docker-compose.yml 1つで、開発環境も本番相当の環境も立ち上がる。
- **ボリュームの分割**: PostgreSQLのデータ、Redis、メディアファイルを個別にマウントし、バックアップしやすくする。
- **Tesseractの言語パック**: `tesseract-ocr-jpn` を含むイメージをビルドし、追加インストールの手間を省く。

```yaml
# docker-compose.yml (抜粋)
services:
  web:
    build: .
    command: uwsgi --ini uwsgi.ini
    volumes:
      - ./media:/app/media
    depends_on:
      - db
      - redis

  tesseract:
    image: ghcr.io/myorg/tesseract-jpn:latest
    volumes:
      - ./media:/app/media
    command: >
      sh -c "while true; do sleep 3600; done"
```

TesseractのOCRジョブは、Celery Workerから`tesseract`サービスにリクエストを飛ばして実行させます。こうすることで、Pythonコード内でサブプロセスを起動するよりも安定性が上がりました。

## 5. 導入効果と現場の変化

実際の導入効果は以下の通りです。

| 指標 | Before | After | 改善率 |
|------|--------|-------|--------|
| 図面検索時間 | 10分 | 10秒 | 60倍 |
| 誤版使用による手戻り | 月2回 | 月0.2回 | 90%減 |
| 図面管理の担当工数 | 週5時間 | 週1時間 | 80%減 |

検索機能のUIはDjango管理画面をカスタマイズし、現場の担当者でも迷わず使えるようにしました。権限制御も Django Group で「閲覧のみ」「編集可」を分けています。

## 6. 注意点：法的側面とバックアップ

図面は企業の重要な知的財産です。電子化する際は以下に注意してください。

- **アクセス権の管理**: Djangoの認証・権限機能を活用し、外注先や派遣社員には閲覧のみ許可する。
- **バックアップの自動化**: メディアファイルを毎日S3に同期し、バージョン管理も兼ねる。
- **紙の廃棄判断**: 電子化したからといって、すぐに紙を捨てない。一定期間の併用期間を設け、トラブル時には紙に戻せるようにする。

## まとめ

図面電子化は「スキャンして終わり」ではなく、**整理ルール→検索システム→運用フロー**の三位一体で進める必要があります。Python/Django と Docker は低コストで始められ、自社の環境に合わせて拡張しやすい組み合わせです。

現場の「面倒くさい」を少しずつ解消することで、技術的な高機能よりも「使われるシステム」が生まれます。もし図面管理や製造業DXでお悩みの方は、お気軽にご相談ください。

---

**コバヤシWEBシステム**では、Django・Dockerを活用した社内システム構築や製造業DXの導入支援を手がけています。月収30万円を目標に、実務に根ざした技術支援を提供中。
