# ビルドステージ (AS builder でステージに名前を付ける)
FROM --platform=linux/amd64 python:3.9-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 実行ステージ
FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app
# ビルドステージからコピー
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# アプリケーションファイルのコピー (必要なものだけをコピーしてサイズを削減)
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY picture/ ./picture/
COPY fonts/ ./fonts/
COPY poems.json ./

# イメージサイズ削減のためにキャッシュをクリア
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-noto-cjk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ポート公開
EXPOSE 8080

# Waitressでアプリケーションを実行
CMD ["python", "-c", "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=8080)"]