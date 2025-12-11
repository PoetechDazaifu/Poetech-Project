import os
import re
import json
import io
import logging
import numpy as np
from PIL import Image 
from flask import Flask, render_template, request, jsonify, send_file
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer
from waitress import serve

app = Flask(__name__)

# JSONデータをロード（エラーハンドリング付き）
DATA_FILE = "poems.json"
if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"データファイル {DATA_FILE} が見つかりません")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    try:
        poems = json.load(f)
    except json.JSONDecodeError:
        raise ValueError("poems.json の JSON 形式が正しくありません")

logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    """
    キーワード、AIタグ、データ元、場所の組み合わせ検索（場所は「exact match」で照合）
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, no JSON data provided"}), 400

        query = data.get("query", "").strip().lower()
        tag_filter = data.get("tag", "").strip().lower()
        source = data.get("source", "").strip().lower()
        location_filter = data.get("location", "").strip()

        results = []
        for poem in poems:
            poem_text = poem["句"].lower()
            # AIタグの処理（リスト or 文字列）
            if isinstance(poem["AIタグ"], list):
                poem_tags = [t.lower() for t in poem["AIタグ"]]
            else:
                poem_tags = [poem["AIタグ"].lower()]

            query_match = re.search(re.escape(query), poem_text, re.IGNORECASE) if query else True
            tag_match = any(tag_filter == tag or tag_filter in tag for tag in poem_tags) if tag_filter else True
            source_match = re.search(re.escape(source), poem["データ元"].lower(), re.IGNORECASE) if source else True

            # 場所フィルターは、["場所"]がボタンで指定された文字列と完全一致するかどうかで判定
            if location_filter:
                place = poem.get("場所", "").strip()
                location_match = (place == location_filter)
            else:
                location_match = True

            if query_match and tag_match and source_match and location_match:
                results.append(poem)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/wordcloud", methods=["POST"])
def generate_wordcloud():
    """
    検索結果の句から形態素解析を行い、ストップワードを除いたテキストで
    ワードクラウド画像を生成（場所フィルターは「exact match」で照合）
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request, no JSON data provided"}), 400

        query = data.get("query", "").strip().lower()
        tag_filter = data.get("tag", "").strip().lower()
        source = data.get("source", "").strip().lower()
        location_filter = data.get("location", "").strip()

        results = []
        for poem in poems:
            poem_text = poem["句"].lower()
            if isinstance(poem["AIタグ"], list):
                poem_tags = [t.lower() for t in poem["AIタグ"]]
            else:
                poem_tags = [poem["AIタグ"].lower()]

            query_match = re.search(re.escape(query), poem_text, re.IGNORECASE) if query else True
            tag_match = any(tag_filter == tag or tag_filter in tag for tag in poem_tags) if tag_filter else True
            source_match = re.search(re.escape(source), poem["データ元"].lower(), re.IGNORECASE) if source else True

            if location_filter:
                place = poem.get("場所", "").strip()
                location_match = (place == location_filter)
            else:
                location_match = True

            if query_match and tag_match and source_match and location_match:
                results.append(poem)

        # 形態素解析用のトークナイザー生成
        tokenizer = Tokenizer()

        # ストップワード（必要に応じて調整）
        stopwords = set([
            "あ","い","う","え","お","か","が","き","ぎ","く","ぐ","け","げ","こ","ご",
            "さ","ざ","し","じ","す","ず","せ","ぜ","そ","ぞ",
            "た","だ","ち","ぢ","つ","づ","て","で","と","ど",
            "な","に","ぬ","ね","の",
            "は","ば","ぱ","ひ","び","ぴ","ふ","ぶ","ぷ","へ","べ","ぺ","ほ","ぼ","ぽ",
            "ま","み","む","め","も","や","ゆ","よ","ら","り","る","れ","ろ","わ","を","ん",
            "する", "れる", "いる", "ある", "なる", "これ", "それ", "です", "ます", "も", "だ",
            "成る", "為る", "居る", "て", "な", "思う", "。", "、", "！", "？", ",", "から"
        ])

        words = []
        for poem in results:
            tokens = tokenizer.tokenize(poem["句"])
            for token in tokens:
                word = token.surface
                if word not in stopwords:
                    words.append(word)
        text = " ".join(words) if words else "データなし"

        # マスク画像の読み込み
        mask = np.array(Image.open("./picture/kokoro.png"))

        # ワードクラウド生成（日本語フォント指定）
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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Render assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    # app.run(debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
    serve(app, host='0.0.0.0', port=port, _quiet=False)
