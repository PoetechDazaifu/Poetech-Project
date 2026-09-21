FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 必要なファイルをコピー
COPY requirements.txt .

# pipをアップグレード
RUN pip install --upgrade pip

# Pythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# データ検証・JSON変換・データベース再構築（形態素解析の事前計算）
RUN python scripts/rebuild_data.py

# ポート8080を公開
EXPOSE 8080

# Waitressでアプリケーションを実行
CMD ["python", "app.py"]
