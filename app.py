import io
import json
import logging
import os
import sqlite3
import time
from collections import OrderedDict
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image
from waitress import serve
from wordcloud import WordCloud

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "poems.db"
MASK_FILE = BASE_DIR / "picture" / "kokoro.png"
FONT_FILE = BASE_DIR / "fonts" / "NotoSansJP-Medium.ttf"
MAX_QUERY_LENGTH = 100
DEFAULT_PAGE_SIZE = 30
MAX_PAGE_SIZE = 100
WORDCLOUD_CACHE_TTL_SECONDS = 600
WORDCLOUD_CACHE_MAX_ITEMS = 128
WORDCLOUD_RATE_LIMIT = 20
WORDCLOUD_RATE_WINDOW_SECONDS = 60

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
wordcloud_cache = OrderedDict()
wordcloud_cache_hits = 0
wordcloud_cache_misses = 0
wordcloud_request_times = {}


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def parse_search_request(data):
    if not isinstance(data, dict):
        raise ValueError("JSON body is required")

    def string_value(key):
        value = data.get(key, "")
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        value = value.strip()
        if len(value) > MAX_QUERY_LENGTH:
            raise ValueError(f"{key} must be {MAX_QUERY_LENGTH} characters or fewer")
        return value

    try:
        page = max(int(data.get("page", 1)), 1)
        page_size = min(max(int(data.get("page_size", DEFAULT_PAGE_SIZE)), 1), MAX_PAGE_SIZE)
    except (TypeError, ValueError) as error:
        raise ValueError("page and page_size must be integers") from error

    return {
        "query": string_value("query"),
        "tag": string_value("tag"),
        "source": string_value("source"),
        "location": string_value("location"),
        "page": page,
        "page_size": page_size,
    }


def build_where(filters):
    clauses, params = [], []

    def escaped_like(value):
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    if len(filters["query"]) >= 3:
        clauses.append("p.id IN (SELECT rowid FROM poem_search WHERE poem_search MATCH ?)")
        params.append(f'"{filters["query"].replace(chr(34), chr(34) * 2)}"')
    elif filters["query"]:
        clauses.append("p.text LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped_like(filters['query'])}%")
    if filters["source"]:
        clauses.append("p.source LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped_like(filters['source'])}%")
    if filters["location"]:
        clauses.append("p.location_category = ?")
        params.append(filters["location"])
    if filters["tag"]:
        clauses.append("EXISTS (SELECT 1 FROM poem_tags pt WHERE pt.poem_id = p.id AND pt.tag = ?)")
        params.append(filters["tag"])
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def get_matching_rows(filters, columns):
    where, params = build_where(filters)
    with db_connection() as conn:
        return conn.execute(f"SELECT {columns} FROM poems p{where} ORDER BY p.id", params).fetchall()


@lru_cache(maxsize=1)
def wordcloud_assets():
    with Image.open(MASK_FILE) as image:
        return np.array(image), str(FONT_FILE)


def generate_wordcloud_png(query, tag, source, location):
    """Generate a PNG with a bounded, TTL-based cache per application process."""
    global wordcloud_cache_hits, wordcloud_cache_misses
    key = (query, tag, source, location)
    now = time.monotonic()
    cached = wordcloud_cache.pop(key, None)
    if cached and cached[0] > now:
        wordcloud_cache_hits += 1
        wordcloud_cache[key] = cached
        return cached[1]

    wordcloud_cache_misses += 1
    filters = {
        "query": query,
        "tag": tag,
        "source": source,
        "location": location,
        "page": 1,
        "page_size": DEFAULT_PAGE_SIZE,
    }
    rows = get_matching_rows(filters, "p.tokens")
    text = " ".join(row["tokens"] for row in rows if row["tokens"]) or "データなし"
    mask, font_path = wordcloud_assets()
    wordcloud = WordCloud(
        font_path=font_path, background_color="#ffffff", colormap="autumn",
        width=800, height=800, max_words=100, mask=mask,
    ).generate(text)
    image = io.BytesIO()
    wordcloud.to_image().save(image, "PNG")
    png = image.getvalue()
    wordcloud_cache[key] = (now + WORDCLOUD_CACHE_TTL_SECONDS, png)
    while len(wordcloud_cache) > WORDCLOUD_CACHE_MAX_ITEMS:
        wordcloud_cache.popitem(last=False)
    return png


def clear_wordcloud_cache():
    global wordcloud_cache_hits, wordcloud_cache_misses
    wordcloud_cache.clear()
    wordcloud_cache_hits = 0
    wordcloud_cache_misses = 0


def wordcloud_cache_stats():
    return {"size": len(wordcloud_cache), "hits": wordcloud_cache_hits, "misses": wordcloud_cache_misses}


def clear_wordcloud_rate_limits():
    wordcloud_request_times.clear()


def wordcloud_request_allowed(client_address):
    now = time.monotonic()
    recent = [timestamp for timestamp in wordcloud_request_times.get(client_address, []) if now - timestamp < WORDCLOUD_RATE_WINDOW_SECONDS]
    if len(recent) >= WORDCLOUD_RATE_LIMIT:
        wordcloud_request_times[client_address] = recent
        return False
    recent.append(now)
    wordcloud_request_times[client_address] = recent
    return True


@app.route("/")
def index():
    return render_template("index.html")


@app.after_request
def set_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' https://github.githubassets.com blob:; "
        "script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@app.route("/healthz")
def healthz():
    try:
        with db_connection() as conn:
            conn.execute("SELECT 1 FROM poems LIMIT 1").fetchone()
    except sqlite3.Error:
        logger.exception("Health check failed")
        return jsonify({"status": "unhealthy"}), 503
    return jsonify({"status": "ok"})


@app.route("/facets")
def facets():
    try:
        with db_connection() as conn:
            source_rows = conn.execute(
                "SELECT source AS value, COUNT(*) AS count FROM poems GROUP BY source ORDER BY source"
            ).fetchall()
            location_rows = conn.execute(
                "SELECT location_category AS value, COUNT(*) AS count FROM poems GROUP BY location_category ORDER BY location_category"
            ).fetchall()
            tag_rows = conn.execute(
                "SELECT tag AS value, COUNT(*) AS count FROM poem_tags WHERE tag != ? GROUP BY tag ORDER BY tag",
                ("ERROR",),
            ).fetchall()
    except sqlite3.Error:
        logger.exception("Facet query failed")
        return jsonify({"error": "絞り込み候補を取得できませんでした。"}), 500
    return jsonify({
        "sources": [dict(row) for row in source_rows],
        "locations": [dict(row) for row in location_rows],
        "tags": [dict(row) for row in tag_rows],
    })


@app.route("/search", methods=["POST"])
def search():
    try:
        filters = parse_search_request(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    where, params = build_where(filters)
    offset = (filters["page"] - 1) * filters["page_size"]
    try:
        with db_connection() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM poems p{where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT p.id, p.text, p.source, p.age, p.location_category, p.tags "
                f"FROM poems p{where} ORDER BY p.id LIMIT ? OFFSET ?",
                [*params, filters["page_size"], offset],
            ).fetchall()
    except sqlite3.Error:
        logger.exception("Search failed")
        return jsonify({"error": "検索を実行できませんでした。"}), 500

    items = [
        {
            "句": row["text"],
            "AIタグ": json.loads(row["tags"]),
            "データ元": row["source"],
            "年齢": row["age"],
            "居住地分類": row["location_category"],
        }
        for row in rows
    ]
    return jsonify({"items": items, "total": total, "page": filters["page"], "page_size": filters["page_size"]})


@app.route("/wordcloud", methods=["POST"])
def generate_wordcloud():
    if not wordcloud_request_allowed(request.remote_addr or "unknown"):
        response = jsonify({"error": "ワードクラウドの生成回数が多すぎます。しばらくしてから再試行してください。"})
        response.headers["Retry-After"] = str(WORDCLOUD_RATE_WINDOW_SECONDS)
        return response, 429
    try:
        filters = parse_search_request(request.get_json(silent=True))
        image = generate_wordcloud_png(
            filters["query"], filters["tag"], filters["source"], filters["location"],
        )
        return send_file(io.BytesIO(image), mimetype="image/png", max_age=600)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        logger.exception("Word cloud generation failed")
        return jsonify({"error": "ワードクラウドを生成できませんでした。"}), 500


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), _quiet=False)
