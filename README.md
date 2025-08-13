# Poetech太宰府

Poetech太宰府は、太宰府で収集した俳句・短歌のライブラリを作成し、検索やワードクラウド生成を通じて、文化・観光・まちづくりのアイデアを考えることを目的としたプロジェクトです。

（令和6年度　太宰府市学生まちづくり課題解決プロジェクト提案　採択事業）

Site：https://sites.google.com/view/poetech-dazaifu

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

### 6. アプリの実行

```bash
$ python app.py
```

ブラウザで `http://127.0.0.1:5000/` にアクセスするとアプリが起動します。

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




---


## 開発者向け情報


リモート環境として既存のPaaSでは形態素解析のメモリ要件が足りないとのことだったので、
[AppRun β](https://manual.sakura.ad.jp/cloud/apprun/about.html)に2GiBでコンテナが立ち上がるサンプルを作成しています。



(現在のコンテナが稼働する立ち上がるURL)
https://app-5f92b294-d806-45b4-8864-4eca7807af15.ingress.apprun.sakura.ne.jp


### ローカルでのコンテナ環境テスト

```
docker-compose build
docker-compose up
```
でDockerコンテナを作成した後、

http://localhost:8080
でページにアクセスできます。

(本来Flask側で`host='0.0.0.0', port=8080`を設定しているのが最適なのかよくわかって無いです)


### さくらのAppRunを利用する

また、SakuraのAppRunにコンテナを立ち上げる前に「コンテナレジストリ」に登録する必要があります。

```
docker-compose build
docker tag {タグ名} {レジストリで登録した名前}.sakuracr.jp/web:v1.0
docker push {レジストリで登録した名前}.sakuracr.jp/web:v1.0
```

という感じでコンテナを事前に登録しておいて、URLへのアクセス時にサービス側からこのコンテナイメージを呼び出してシステムがWebで稼働します。


### さくらのAppRunの仕様

AppRunはゼロステート式で、コンテナ内でDBを動かす場合などは毎回実体が揮発します。

このシステムにおいてはすべて静的なファイルとして保持しているので問題はないです。

また、NGINXなどをコンテナ内で動かしていなくても、AppRun側で自動的に3000番ポートなどのWell-Knownポートを見に行ってくれるほか、最低限SSL対応もされています。

現在ビルドしたコンテナが500MBを超えていますので、小さくできそうなら小さくする必要があります。


### 2025年3月 
ローディングアニメーションを付加。

### 2025年8月
OGPを追加。
