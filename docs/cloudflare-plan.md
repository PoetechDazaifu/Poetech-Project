# Cloudflare 導入の段階計画

## 決定

当面は **Render上のFlaskアプリを継続運用し、CloudflareをDNS・CDN・WAFの前段として導入する**。Cloudflare Workers/D1への全面移行は実施しない。

`/wordcloud`は日本語フォント、Pillow、NumPy、WordCloudによるCPU集約的なPNG生成を行う。WorkersのPython実行環境（Pyodide/Wasm）へ同等に移植することは、現時点では移行コストと実行制約に見合わない。

## 段階1: Render + Cloudflare（採用）

- Cloudflareでドメイン、TLS、WAF、静的資産キャッシュを管理する。
- Renderをオリジンとして登録し、`/healthz`でアプリケーションの準備完了を確認する。
- 静的資産はCloudflareの標準キャッシュを利用する。
- `/search`と`/wordcloud`は利用者ごとの条件に依存するため、明示的なキャッシュルールを設けるまでCDNキャッシュしない。
- Cloudflare側でも`/wordcloud`にWAFレート制限を設定し、アプリ内レート制限を補完する。

## 段階2: 検索専用APIのWorkers/D1移行（条件付き）

以下を満たした場合にのみ検討する。

- Renderの応答時間・コスト・可用性が要件を満たさない。
- 検索リクエストが継続的に増え、世界各地からの低遅延応答が必要になる。
- D1へ移す検索データ、FTS仕様、データ更新手順を再現可能な移行テストで検証できる。

移行対象は`/search`と`/facets`に限る。`/wordcloud`はRenderに残し、WorkersからサービスバインディングまたはHTTPS経由で呼ばない設計を維持する。

## 全面移行の判断基準

次のすべてを満たすまで全面移行しない。

1. ワードクラウドをクライアント側生成へ移すか、別の画像生成基盤へ分離済みである。
2. 日本語フォント・画像生成・検索結果が既存環境と同じ品質であることを自動テストで確認できる。
3. Cloudflareの実行時間、メモリ、パッケージ互換性、費用を実アクセス量で評価済みである。

## ロールバック

1. Cloudflareをプロキシ利用した後に障害が起きた場合、対象DNSレコードをDNS onlyへ切り替える。
2. キャッシュ起因の障害は対象URLのキャッシュをパージし、必要に応じてキャッシュルールを無効化する。
3. D1の試験導入時はRenderのSQLite検索を残し、DNS・ルーティングを切り替える前に即時復帰できる状態を保つ。
4. 変更前後で`/healthz`、検索、ワードクラウドの3操作を確認する。

## 参考資料

- [Cloudflare Workers Python packages](https://developers.cloudflare.com/workers/languages/python/packages/)
- [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Cloudflare D1](https://developers.cloudflare.com/d1/)
