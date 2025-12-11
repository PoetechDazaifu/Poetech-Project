import os
import re
import json
import io
import logging
import sqlite3
import numpy as np
from PIL import Image 
from flask import Flask, render_template, request, jsonify, send_file
from wordcloud import WordCloud
from waitress import serve

app = Flask(__name__)

# データ設定
DB_FILE = "poems.db"

# ロガー設定
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    """
    キーワード、AIタグ、データ元、場所の組み合わせ検索
    SQLiteを使用して検索を実行
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, no JSON data provided"}), 400

        query = data.get("query", "").strip()
        tag_filter = data.get("tag", "").strip()
        source_filter = data.get("source", "").strip()
        location_filter = data.get("location", "").strip()

        conn = get_db_connection()
        
        # Base query
        sql = "SELECT * FROM poems WHERE 1=1"
        params = []

        # Keyword Search (partial match on text)
        if query:
            sql += " AND text LIKE ?"
            params.append(f"%{query}%")
        
        # Source Filter (partial match)
        if source_filter:
            sql += " AND source LIKE ?"
            params.append(f"%{source_filter}%")
        
        # Location Filter (exact match)
        if location_filter:
            sql += " AND location = ?"
            params.append(location_filter)

        # Tag Filter (check if tag exists in the JSON list)
        # Note: SQLite simple LIKE is used here for "contains". 
        # Since tags are stored as JSON list e.g. ["tag1", "tag2"], LIKE '%"tag1"%' works for exact tag match inside list
        if tag_filter:
            # tag_filter usually comes as simple string.
            # Using LIKE to find the tag inside the stringified list.
            # Ideally we should use 'json_each' but standard LIKE is sufficient for this scale.
            sql += " AND tags LIKE ?"
            params.append(f"%{tag_filter}%")

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            # Convert row to dict structure expected by frontend
            # Frontend expects: "句", "AIタグ", "データ元", "場所"
            tags = json.loads(row["tags"])
            results.append({
                "句": row["text"],
                "AIタグ": tags,
                "データ元": row["source"],
                "場所": row["location"]
            })
            
        conn.close()

        return jsonify(results)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/wordcloud", methods=["POST"])
def generate_wordcloud():
    """
    検索結果の句からワードクラウド画像を生成
    事前計算されたトークン(tokensカラム)を使用するため、形態素解析は不要。
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, no JSON data provided"}), 400

        query = data.get("query", "").strip()
        tag_filter = data.get("tag", "").strip()
        source_filter = data.get("source", "").strip()
        location_filter = data.get("location", "").strip()

        conn = get_db_connection()
        
        # Re-use similar logic to search but fetch tokens
        sql = "SELECT tokens FROM poems WHERE 1=1"
        params = []

        if query:
            sql += " AND text LIKE ?"
            params.append(f"%{query}%")
        if source_filter:
            sql += " AND source LIKE ?"
            params.append(f"%{source_filter}%")
        if location_filter:
            sql += " AND location = ?"
            params.append(location_filter)
        if tag_filter:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag_filter}%")

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Aggregate all tokens
        all_words = []
        for row in rows:
            if row["tokens"]:
                all_words.append(row["tokens"])
        
        text = " ".join(all_words) if all_words else "データなし"

        # マスク画像の読み込み
        mask = np.array(Image.open("./picture/kokoro.png"))

        # ワードクラウド生成
        wc = WordCloud(
            font_path="./fonts/NotoSansJP-Medium.ttf",
            background_color="#ffffff",
            colormap="autumn",
            width=800,
            height=800,
            max_words=100,
            mask=mask,
        ).generate(text)

        img_io = io.BytesIO()
        wc.to_image().save(img_io, "PNG")
        img_io.seek(0)
        return send_file(img_io, mimetype="image/png")

    except Exception as e:
        logger.error(f"Wordcloud error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Render assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # app.run(debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
    serve(app, host='0.0.0.0', port=port, _quiet=False)

