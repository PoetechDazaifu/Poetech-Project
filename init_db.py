"""Build the application SQLite database from normalized poem JSON."""

import argparse
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from janome.tokenizer import Tokenizer

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "poems.json"
DB_FILE = BASE_DIR / "poems.db"


def get_stopwords():
    return {
        "あ", "い", "う", "え", "お", "か", "が", "き", "ぎ", "く", "ぐ", "け", "げ", "こ", "ご",
        "さ", "ざ", "し", "じ", "す", "ず", "せ", "ぜ", "そ", "ぞ", "た", "だ", "ち", "ぢ", "つ", "づ",
        "て", "で", "と", "ど", "な", "に", "ぬ", "ね", "の", "は", "ば", "ぱ", "ひ", "び", "ぴ", "ふ",
        "ぶ", "ぷ", "へ", "べ", "ぺ", "ほ", "ぼ", "ぽ", "ま", "み", "む", "め", "も", "や", "ゆ", "よ",
        "ら", "り", "る", "れ", "ろ", "わ", "を", "ん", "する", "れる", "いる", "ある", "なる", "これ",
        "それ", "です", "ます", "も", "だ", "成る", "為る", "居る", "思う", "。", "、", "！", "？", ",", "から",
    }


def normalize_tags(tags_raw):
    """Convert inconsistent source delimiters into a unique list of exact tags."""
    if tags_raw is None:
        return []
    values = tags_raw if isinstance(tags_raw, list) else [tags_raw]
    tags = []
    for value in values:
        if isinstance(value, str):
            tags.extend(tag.strip() for tag in re.split(r"[,、]", value) if tag.strip())
    return list(dict.fromkeys(tags))


def dataset_metadata(data_file: Path):
    return {
        "source_file": data_file.name,
        "source_sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }


def create_schema(cursor):
    cursor.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            source TEXT NOT NULL,
            residence TEXT,
            location_category TEXT NOT NULL,
            age TEXT,
            tags TEXT NOT NULL,
            tokens TEXT NOT NULL
        );
        CREATE TABLE poem_tags (
            poem_id INTEGER NOT NULL REFERENCES poems(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            PRIMARY KEY (poem_id, tag)
        );
        CREATE TABLE dataset_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE poem_search USING fts5(text, tokenize='trigram');
        CREATE INDEX idx_location_category ON poems(location_category);
        CREATE INDEX idx_source ON poems(source);
        CREATE INDEX idx_poem_tags_tag ON poem_tags(tag);
        """
    )


def build_database(data_file=DATA_FILE, db_file=DB_FILE):
    """Build a temporary DB and atomically replace db_file only on success."""
    data_file, db_file = Path(data_file), Path(db_file)
    if not data_file.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {data_file}")

    poems = json.loads(data_file.read_text(encoding="utf-8"))
    if not isinstance(poems, list):
        raise ValueError("JSONの最上位要素は配列である必要があります")

    temporary_db = db_file.with_suffix(f"{db_file.suffix}.tmp")
    if temporary_db.exists():
        temporary_db.unlink()

    connection = None
    try:
        connection = sqlite3.connect(temporary_db)
        cursor = connection.cursor()
        create_schema(cursor)
        tokenizer = Tokenizer()
        stopwords = get_stopwords()
        poem_rows, tag_rows = [], []

        for poem_id, poem in enumerate(poems, start=1):
            text = str(poem.get("句") or "")
            source = str(poem.get("データ元") or "")
            residence = poem.get("在住地")
            location_category = str(poem.get("場所") or "")
            age = poem.get("年齢")
            tags = normalize_tags(poem.get("AIタグ"))
            tokens = " ".join(token.surface for token in tokenizer.tokenize(text) if token.surface not in stopwords)
            poem_rows.append((text, source, residence, location_category, age, json.dumps(tags, ensure_ascii=False), tokens))
            tag_rows.extend((poem_id, tag) for tag in tags)

        cursor.executemany(
            "INSERT INTO poems (text, source, residence, location_category, age, tags, tokens) VALUES (?, ?, ?, ?, ?, ?, ?)",
            poem_rows,
        )
        cursor.executemany("INSERT INTO poem_search (rowid, text) VALUES (?, ?)", enumerate((row[0] for row in poem_rows), start=1))
        cursor.executemany("INSERT INTO poem_tags (poem_id, tag) VALUES (?, ?)", tag_rows)
        cursor.executemany("INSERT INTO dataset_metadata (key, value) VALUES (?, ?)", dataset_metadata(data_file).items())
        connection.commit()
        connection.close()
        connection = None
        os.replace(temporary_db, db_file)
    except Exception:
        if connection is not None:
            connection.close()
        if temporary_db.exists():
            temporary_db.unlink()
        raise

    print(f"{len(poem_rows)} 件を {db_file} に登録しました。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DATA_FILE)
    parser.add_argument("--output", type=Path, default=DB_FILE)
    arguments = parser.parse_args()
    build_database(arguments.input, arguments.output)
