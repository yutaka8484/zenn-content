---
title: "同じDockerホストの複数サービスをTailscale ServeだけでHTTPS公開する実務手順"
emoji: "🛠️"
type: "tech"
topics: ["docker", "nginx", "tailscale", "https"]
published: true
---

## はじめに

自宅サーバーで Docker コンテナを複数動かしていると、「ポート番号違いの URL を他人に説明するのが面倒」「外部から安全に使いたい」という課題にぶつかります。

私も日頃から x1lite 上で Docker を運用していますが、特に変化があったわけでもないのに、複数サービスの公開方法を整理する機会がありました。

本記事では、Tailscale Serve とホスト nginx を組み合わせ、Docker ホスト1台で複数のサービスをドメインごとに HTTPS 公開する実務の手順を整理します。

## 前提条件

- Ubuntu/Debian 系のホスト
- Docker がインストール済み
- nginx がホストに導入済み
- Tailscale のアカウントを作成し、`tailscale up` で接続済み
- `sudo` 権限を持つユーザー

## 1. Tailscale Serve の有効化

Tailscale Serve を使うと、Tailscale 上のマシンが持つポートを HTTPS で公開できます。

```bash
# Tailscale Serve を有効化
sudo tailscale serve --bg --https 443

# バックエンドのコンテナポートを公開
sudo tailscale serve --bg --https 443 --serve-backend http://localhost:3000
```

ここで `localhost:3000` は Next.js アプリケーションの例です。Docker で別ポートを使うサービスでも同様に指定できます。

## 2. ホスト nginx による TLS 終端

私の構成では、ホスト nginx を Reverse Proxy として利用しています。

```nginx
# /etc/nginx/sites-available/app
server {
  listen 80;
  listen [::]:80;
  server_name app.example.com;

  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

この設定により、ホスト上で完結する証明書更新とリバースプロキシを維持できます。

## 3. Docker サービスの HTTPS 対応

Docker Compose で起動したサービスも、同様の流れで対応できます。

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

# ホスト nginx からのみ転送
# ホスト firewall で 8080 を localhost からに限定
```

この例では `localhost` からのみ 8080 へ転送するように firewall で制限します。

## 4. 複数サービスの分離

同じホストで複数サービスを運用する場合、サブドメインで分けるのが基本です。

| サービス | ローカルポート | 公開 URL |
|---|---|---|
| Web アプリ | 3000 | app.example.com |
| API | 8000 | api.example.com |
| 管理画面 | 4000 | admin.example.com |

nginx の設定ファイルをサービスごとに配置し、`sites-enabled` から symlink で有効化します。

## 5. 運用のポイント

- **ヘルスチェック**: 複数サービスのうち1つが停止しても nginx が503を返すように、`proxy_next_upstream` の検討余地があります
- **ログ管理**: Docker Compose のログドライバを `json-file` に統一し、ローテーションを設定
- **更新フロー**: nginx 設定変更後は `nginx -t` で構文確認してから reload

## まとめ

Docker + Tailscale Serve + ホスト nginx の3要素で、外部公開と内部運用の分離を実現できます。

私は基幹システム入れ替え PJ で多数の Web システムを管理してきましたが、最小の変更で最大の効果を出す構成として、この形に落ち着いています。

同じような複数サービス公開の課題に直面している中小企業の DX 担当の方、同じホスト上で複数コンテナを運用している方は、ぜひ参考にしてください。

株式会社コバヤシでは、製造業・建設業の Web 制作・インフラ構築・業務システムの DX 支援を承っています。
