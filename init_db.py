import sqlite3
import json
import os
from janome.tokenizer import Tokenizer

# Config
DATA_FILE = "poems.json"
DB_FILE = "poems.db"

def get_stopwords():
    return set([
        "あ","い","う","え","お","か","が","き","ぎ","く","ぐ","け","げ","こ","ご",
        "さ","ざ","し","じ","す","ず","せ","ぜ","そ","ぞ",
        "た","だ","ち","ぢ","つ","づ","て","で","と","ど",
        "な","に","ぬ","ね","の",
        "は","ば","ぱ","ひ","び","ぴ","ふ","ぶ","ぷ","へ","べ","ぺ","ほ","ぼ","ぽ",
        "ま","み","む","め","も","や","ゆ","よ","ら","り","る","れ","ろ","わ","を","ん",
        "する", "れる", "いる", "ある", "なる", "これ", "それ", "です", "ます", "も", "だ",
        "成る", "為る", "居る", "て", "な", "思う", "。", "、", "！", "？", ",", "から"
    ])

def init_db():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return

    # Load JSON
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        poems = json.load(f)

    # Prepare Tokenizer
    t = Tokenizer()
    stopwords = get_stopwords()

    # Connect to DB
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create Table
    # tags will be stored as JSON string "tag1,tag2" or JSON array if FTS needs it, 
    # but for simple filtering, we might normalize.
    # Actually, for performance, normalized tables are better, but for simplicity of migration:
    # We'll store tags as a comma-separated string for "LIKE" queries or a separate table?
    # Original app used "tag in list".
    # Let's use a single table with JSON column for tags, and FTS for text?
    # Or just standard columns.
    
    c.execute('''
        CREATE TABLE poems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            source TEXT,
            location TEXT,
            age TEXT,
            tags TEXT,
            tokens TEXT
        )
    ''')
    
    # Create Indexes
    c.execute('CREATE INDEX idx_location ON poems(location)')
    c.execute('CREATE INDEX idx_source ON poems(source)')

    print(f"Processing {len(poems)} poems...")

    data_to_insert = []
    
    for poem in poems:
        text = poem.get("句", "")
        source = poem.get("データ元", "")
        location = poem.get("場所", "")
        age = poem.get("年齢", "")
        
        # Tags: JSON list -> string (normalized for LIKE search if needed, but JSON is safer)
        tags_raw = poem.get("AIタグ", [])
        if isinstance(tags_raw, str):
            tags_list = [tags_raw]
        else:
            tags_list = tags_raw
        
        # Serialize tags as JSON for easy retrieval
        tags_json = json.dumps(tags_list, ensure_ascii=False)

        # Pre-compute tokens for WordCloud
        tokens = []
        try:
            for token in t.tokenize(text):
                word = token.surface
                if word not in stopwords:
                    tokens.append(word)
        except Exception as e:
            print(f"Tokenization error for {text}: {e}")
        
        tokens_str = " ".join(tokens)

        data_to_insert.append((text, source, location, age, tags_json, tokens_str))

    c.executemany('INSERT INTO poems (text, source, location, age, tags, tokens) VALUES (?, ?, ?, ?, ?, ?)', data_to_insert)
    
    conn.commit()
    conn.close()
    print(f"Successfully created {DB_FILE} with {len(data_to_insert)} records.")

if __name__ == "__main__":
    init_db()
