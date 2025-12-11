# Poetech太宰府

Poetech太宰府は、太宰府で収集した俳句・短歌のライブラリを作成し、検索やワードクラウド生成を通じて、文化・観光・まちづくりのアイデアを考えることを目的としたプロジェクトです。

（令和6年度　太宰府市学生まちづくり課題解決プロジェクト提案　採択事業）

Site：https://sites.google.com/view/poetech-dazaifu

WEBアプリリンク:https://app-5f92b294-d806-45b4-8864-4eca7807af15.ingress.apprun.sakura.ne.jp/

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
$ git clone https://github.com/yourusername/dazaihuproject.git
$ cd dazaihuproject
```

### 3. 必要なパッケージのインストール

```bash
$ pip install -r requirements.txt
```

### 4. 仮想環境の作成

```bash
$ python -m venv venv
$ source venv/bin/activate
```

### 5. JSONデータの作成

データソースとして `data/AIタグ付け短歌・俳句.xlsx` をJSON形式に変換します。

```bash
$ python convert_to_json.py
```


### 6. データベースの初期化

初回起動時やデータ更新時は、以下のコマンドでデータベースを作成・更新します。

```bash
$ python init_db.py
```

### 7. アプリの実行

```bash
$ python app.py
```

ブラウザで `http://127.0.0.1:5000/` にアクセスするとアプリが起動します。


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
├── fonts                 # 日本語フォント
├── picture
│   └── kokoro.png        # ワードクラウド用マスク画像
├── poems.json            # 変換後のJSONデータ
├── requirements.txt      # 依存ライブラリ
├── static
│   ├── script.js         # フロントエンドのスクリプト
│   └── style.css         # スタイルシート
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

コードへの改善提案があれば、[issues](https://github.com/yourusername/dazaihuproject/issues) に投稿してください。

