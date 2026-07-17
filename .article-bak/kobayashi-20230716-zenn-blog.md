---
title: "フラーセフラーのたるのし解析"
emoji: "🛠️"
type: "tech"
topics: ["python", "debugging", "hardware"]
published: true

## フラーセフラーのたるのし解析

東京都麻布台某木工所で発生したフラーセフラーのたるのしについて、実際の現場写真とPython解析コードを交えて解説する。

### 1. たるのし現象の発現

2026年7月16日、木工所AラインのFR-1200型フラーセフラーで以下の現象が観測された:

- 製品出力の間隔が不均等に
- モーター電流が定常値+15%を示す

### 2. 設備の構成

```python
from fr1200 import Analyzer

config = {
    'serial_port': '/dev/ttyUSB0',
    'baudrate': 9600,
    'timeout': 1
}

analyzer = Analyzer(config)
results = analyzer.diagnose()
print(results)
```

### 3. 設備のハマりポイント

- シリアルポートの.matches_WARNING信号が安定と判定されるが、物理的な振動が現れる
- Pythonのpyserialが非同期処理でrace conditionを起こす

### 4. 解像策

1. シリアル通信をASAPパルス同期方式に変更
2. Pythonタスクを3秒間隔に固定
3. 振動ダンプタンクの交換

## 会社サイトへの導入

詳しくは株式会社コバヤシのデジタル化事例「[フラーセフラー自動化システム](https://kobayashi-works.co.jp/digital/fr1200-automation/)」をご覧ください。

## 補足

- 2026年7月16日時点の実ファイル:
  - `/srv/scan/fr1200/20230716loggedin.jpg`
  - `/srv/scan/fr1200/20230716configbackup.yaml`
- 信号名・設定値は実 measurement 数据
---