# Poetech太宰府

Poetech太宰府は、太宰府で収集した俳句・短歌のライブラリを作成し、検索やワードクラウド生成を通じて、文化・観光・まちづくりのアイデアを考えることを目的としたプロジェクトです。

（令和6年度　太宰府市学生まちづくり課題解決プロジェクト提案　採択事業）

Site：https://sites.google.com/view/poetech-dazaifu

WEBアプリリンク:https://poetech-project.onrender.com/

ChatGPT　カスタムGPT：https://chatgpt.com/g/g-67b2d0071e048191836249fc018e914a-poetechtai-zai-fu

## 📌 主な機能

- **キーワード検索**: 任意の単語で俳句・短歌を検索
- **AIタグ検索**: AIが自動で分類したタグをもとにフィルタリング
- **データ元フィルタ**: 句会・ポスト・広報などのデータ元で検索
- **場所フィルタ**: 句の投稿者の居住地で検索
- **ワードクラウド生成**: 検索結果の俳句・短歌をもとにワードクラウドを生成

---

## 🛠 セットアップ方法

### 1. 必要な環境

- Python
- Flask
- Janome (形態素解析用)
- WordCloud (ワードクラウド生成用)

### 2. リポジトリのクローン

```bash
$ git clone https://github.com/PoetechDazaifu/Poetech-Project.git
$ cd dazaihuproject
```

### 3. 仮想環境の作成

```bash
$ python -m venv venv
$ source venv/bin/activate
```

### 4. 必要なパッケージのインストール

```bash
$ pip install -r requirements.txt
```

### 5. データ検証・JSON変換・データベース再構築

データソースを検証してJSONへ変換し、SQLiteデータベースを安全に再構築します。既存のDBは、全工程が成功した場合にだけ置き換えられます。

```bash
$ python scripts/rebuild_data.py
# 例: 別の入力ファイルを使う場合
$ python scripts/rebuild_data.py path/to/poems.xlsx
```

`data-validation-report.json` に件数、必須列・空欄、重複句、未定義タグを出力します。必須列・公開に必要な列の空欄は処理を中断し、重複句と未定義タグは警告として記録します。`AIタグ` は `,` と `、` のいずれで区切られていても個別タグに正規化されます。元データの`在住地`はDBに保持し、公開検索・表示には粗い分類である`場所`（太宰府市内など）のみを用います。

### 6. テスト

DBを初期化した後、次を実行します。

```bash
$ python -m unittest discover -s tests
```

### 7. アプリの実行

```bash
$ python app.py
```

ブラウザで `http://0.0.0.0:8080` にアクセスするとアプリが起動します。

稼働確認には `GET /healthz` を使用できます。

検索キーワードが3文字以上の場合はSQLite FTS5のtrigram索引を使い、2文字以下は日本語の短い語も扱えるよう部分一致検索へフォールバックします。データ元、AIタグ、居住地分類の候補と件数は、登録済みデータから画面へ動的に表示されます。

ワードクラウドは正規化済みの検索条件ごとに、アプリケーションプロセス内で最大128件・10分間キャッシュされます。データ更新時はデプロイによるプロセス再起動でキャッシュを無効化します。


---

## 🚀 デプロイ (Render)

このプロジェクトは、Renderの無料プランで簡単にデプロイできるように設定されています。

### 手順

1. [Render](https://render.com/) にアカウント登録・ログインします。
2. ダッシュボードの「Blueprints」ボタンをクリックします。
3. 「New Blueprint Instance」を選択します。
4. このGitHubリポジトリを接続します。
5. 設定が自動的に読み込まれるので（`render.yaml`を使用）、そのまま「Apply」をクリックします。
6. デプロイが完了すると、発行されたURLからアプリケーションにアクセスできます。

> **注意**: 無料プランでは、一定期間アクセスがないとスリープ状態になり、次のアクセス時に起動するまで少し時間がかかる場合があります。

---

## 📂 プロジェクト構成

```
├── app.py                # Flaskアプリケーション
├── convert_to_json.py    # ExcelデータをJSONに変換
├── data
│   └── AIタグ付け短歌・俳句.xlsx  # データファイル
├── docker-compose.yml    # Docker Compose設定
├── Dockerfile            # Docker設定
├── fonts                 # 日本語フォント
├── init_db.py            # データベース初期化
├── picture
│   └── kokoro.png        # ワードクラウド用マスク画像
├── poems.db              # SQLiteデータベース
├── poems.json            # 変換後のJSONデータ
├── render.yaml           # Renderデプロイ設定
├── requirements.txt      # 依存ライブラリ
├── static
│   ├── script.js         # フロントエンドのスクリプト
│   ├── style.css         # スタイルシート
│   ├── poetech_logo.png  # ロゴ
│   └── primary_wc.png    # 初期ワードクラウド表示
├── templates
│   └── index.html        # メインページのテンプレート
└── README.md             # このファイル
```

---

## 🔍 使用方法

1. **キーワード検索**
   - 検索ボックスに単語を入力し「検索」ボタンを押すと、該当する句が表示されます。
2. **AIタグ検索**
   - 「まちづくり」「観光」「危機管理」などのタグボタンを押すと、関連する句が表示されます。
3. **ワードクラウド生成**
   - 検索結果に基づいて、ワードクラウド画像が自動生成されます。
4. **フィルタリング**
   - データ元や居住地のフィルタを適用して、より詳細な検索が可能です。

---

## 👥 貢献方法

1. リポジトリをフォークする
2. ブランチを作成する (`git checkout -b feature-branch`)
3. 変更をコミットする (`git commit -m 'Add new feature'`)
4. プッシュする (`git push origin feature-branch`)
5. プルリクエストを作成する

---

## 📞 問い合わせ

プロジェクトに関する質問やご連絡は、ウェブサイトの問い合わせページへお願いします。

コードへの改善提案があれば、[issues](https://github.com/PoetechDazaifu/Poetech-Project/issues) に投稿してください。
