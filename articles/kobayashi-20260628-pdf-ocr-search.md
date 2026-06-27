---
title: "製造業の図面PDF・帳票を検索可能にするOCRとDockerでの構築例"
emoji: "🛠️"
type: "tech"
topics: ["docker", "python", "ocr", "manufacturing-dx"]
published: true
---

# 製造業の図面PDF・帳票を検索可能にするOCRとDockerでの構築例

## 1. 背景：製造業の“紙の山”がDXを阻む

製造業では、設計図面、検査成績表、見積書、納品書など、**PDF帳票が年々増え続ける**。ファイル名で管理している場合、必要な図面を探すために毎回フォルダを開き、目視で確認する——そんな "ファイル探し" の工数が、現場のDXを阻む理由の1つだ。

本稿では、**Docker + Python + Tesseract OCR** を用いて、手元にあるPDF帳票を全文検索可能にする仕組みを紹介する。

読み手：
- 中小製造業の経営者・DX推進担当者
- 同様の課題を抱えるエンジニア

## 2. 仕組みの全体像

図1に示すように、本システムは3つのステップで動作する。

1. **PDFの文字列抽出**：`pdfplumber` や `PyMuPDF` でPDFのレイヤーに保持されたテキストを抽出する。
2. **画像PDFのOCR処理**：スキャンされた図面（画像PDF）は、`pytesseract` + `pdf2image` で画像化し、OCRでテキスト化する。
3. **検索用インデックス生成**：抽出したテキストとファイルパスを `SQLite + FTS5` に登録し、SQL全文検索を可能にする。

> 本記事では、実運用可能な最小構成のコードを示す。

## 3. 環境構築（Docker Compose）

`docker-compose.yml` を使い、**Pythonランタイム + Tesseractエンジン** を1コマンドで起動する。

```yaml
version: "3.9"
services:
  ocr-worker:
    image: python:3.12-slim
    container_name: pdf-ocr
    volumes:
      - ./data:/app/data
      - ./ocr-output:/app/output
    working_dir: /app
    command: >
      bash -c "
        apt-get update -y &&
        apt-get install -y --no-install-recommends
          tesseract-ocr
          tesseract-ocr-jpn
          poppler-utils &&
        pip install --no-cache-dir
          pdfplumber
          pdf2image
          pytesseract
          Pillow &&
        python index_pdfs.py
      "
    environment:
      - TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
```

**ポイント**：
- `tesseract-ocr-jpn` を入れることで、日本語OCRが可能になる。
- `poppler-utils` は `pdf2image` が内部的に使用する。

## 4. PythonによるPDFインデックス化

`index_pdfs.py` は、`./data` に配置されたPDFを走査し、全文検索用のSQLite FTS5テーブルを構築する。

```python
import os
import sqlite3
from pathlib import Path
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

DATA_DIR = Path("/app/data")
DB_PATH = Path("/app/output/paper_index.db")
LANG = "jpn+eng"  # 日本語＋英語

def extract_text_from_pdf(pdf_path: Path) -> str:
    """テキスト埋め込みPDFのテキストを抽出"""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:10]:  # 最大10ページ
            txt = page.extract_text()
            if txt:
                texts.append(txt)
    return "\n".join(texts)

def ocr_image_pdf(pdf_path: Path) -> str:
    """画像PDF（スキャン図面など）をOCR"""
    texts = []
    try:
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=5,  # ページ数多い場合は一部のみ
            fmt="png",
            thread_count=1,
        )
        for img in images:
            txt = pytesseract.image_to_string(img, lang=LANG)
            texts.append(txt)
    except Exception as e:
        print(f"[WARN] OCR failed: {pdf_path} : {e}")
    return "\n".join(texts)

def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents
        USING fts5(path, content);
    """)
    conn.commit()

def index_pdfs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    pdfs = list(DATA_DIR.rglob("*.pdf"))
    print(f"[INFO] Target PDFs: {len(pdfs)}")

    for pdf in pdfs:
        relative = pdf.relative_to(DATA_DIR)
        # テキスト抽出を試行 → 失敗/空ならOCRへフォールバック
        text = extract_text_from_pdf(pdf)
        if not text.strip():
            print(f"[INFO] OCR fallback: {relative}")
            text = ocr_image_pdf(pdf)

        if not text.strip():
            print(f"[WARN] No text extracted: {relative}")
            continue

        conn.execute("INSERT INTO documents VALUES (?, ?)", (str(relative), text))
        print(f"[OK] indexed: {relative} ({len(text)} chars)")

    conn.commit()
    conn.close()
    print("[DONE] Index build complete.")

if __name__ == "__main__":
    index_pdfs()
```

## 5. 実際に動かす手順

### 5.1 ファイル配置

```
project/
├── docker-compose.yml
├── index_pdfs.py
└── data/
    ├── drawings/
    │   └── frame-assembly-A3.pdf
    └── invoices/
        └── invoice-2026-04.pdf
```

### 5.2 ビルドとインデックス生成

```bash
docker compose up --build
```

完了後、`./ocr-output/paper_index.db` が生成される。

### 5.3 SQLite FTS5で全文検索

任意のSQLiteクライアント（またはPythonスクリプト）から検索できる。

```sql
-- 「フレーム」を含む図面を検索
SELECT path, snippet(documents, 1, '...', '...', 10, 20)
FROM documents
WHERE documents MATCH 'フレーム'
LIMIT 10;
```

Pythonからは:

```python
import sqlite3
conn = sqlite3.connect("./ocr-output/paper_index.db")
cur = conn.cursor()
cur.execute("SELECT path FROM documents WHERE documents MATCH ?", ("フレーム",))
for row in cur.fetchall():
    print(row[0])
```

## 6. 本番運用に向けた拡張ポイント

今回の例は**検証用の最小構成**である。実運用では以下を検討する。

- **ページ分割**: 図面が100ページを超える場合、ページ単位のインデックス化を行う
- **メタデータ管理**: 図面番号、作成日、製品名を別テーブルで管理し、条件検索と組み合わせる
- **UIの追加**: FastAPIで検索APIを提供し、ブラウザから図面を検索できるようにする
- **差分インデックス**: 新規PDFのみを差分処理するウィンドウを定期実行する（Windows Task Schedulerやcron）

## 7. まとめ：引越しから再出発するイメージ

本システムは、**「図面を探す時間」を「設計・改善の時間」に変換する**仕組みだ。

私自身、木工所事業（株式会社コバヤシ）で図面の電子化と検索環境の整備を進めてきた。最初は手作業でフォルダ整理をしていたが、Pythonスクリプトで一括処理するようになり、**図面発見のリードタイムを数時間から数分に短縮した**。

同じ課題を持つ製造業の経営者・エンジニアの参考になれば幸いだ。

---

**コバヤシWEBシステム（yutakaの個人事業）** では、
- 製造業のDX・業務システム開発
- Dockerを活用した社内インフラ構築
- AI/OCRを使った帳票自動化

をご支援しています。興味のある方は、[Zennプロフィール](https://zenn.dev/yutaka8484) または記事内の問い合わせ導線からご相談ください。
