FROM --platform=linux/amd64 python:3.9

WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt .

# pipをアップグレード
RUN pip install --upgrade pip

# Pythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# データベースを初期化（形態素解析の事前計算）
RUN python init_db.py

# ポート8080を公開
EXPOSE 8080

# Waitressでアプリケーションを実行
CMD ["python", "app.py"]