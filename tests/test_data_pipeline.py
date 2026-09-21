import sqlite3
import unittest
from contextlib import closing

from app import app, generate_wordcloud_png
from init_db import DB_FILE, normalize_tags


class DataPipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_normalize_tags_supports_source_delimiters(self):
        self.assertEqual(normalize_tags("こども, 福祉、観光"), ["こども", "福祉", "観光"])
        self.assertEqual(normalize_tags(None), [])

    def test_database_has_normalized_tag_rows(self):
        with closing(sqlite3.connect(DB_FILE)) as connection:
            tag_rows = connection.execute("SELECT COUNT(*) FROM poem_tags WHERE tag = '福祉'").fetchone()[0]
        self.assertGreater(tag_rows, 0)

    def test_search_is_paginated_and_tag_is_exact(self):
        response = self.client.post("/search", json={"tag": "福祉", "page_size": 1})
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertGreater(payload["total"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertIn("福祉", payload["items"][0]["AIタグ"])

    def test_invalid_search_input_returns_400(self):
        response = self.client.post("/search", json={"query": "x" * 101})
        self.assertEqual(response.status_code, 400)

    def test_index_uses_static_assets_and_live_results(self):
        response = self.client.get("/")
        document = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('static/style.css', document)
        self.assertIn('static/script.js', document)
        self.assertIn('aria-live="polite"', document)
        self.assertNotIn("axios", document)

    def test_wordcloud_is_cached_for_the_same_filters(self):
        generate_wordcloud_png.cache_clear()
        first = self.client.post("/wordcloud", json={"tag": "福祉"})
        second = self.client.post("/wordcloud", json={"tag": "福祉"})
        cache_info = generate_wordcloud_png.cache_info()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data, second.data)
        self.assertEqual(cache_info.misses, 1)
        self.assertEqual(cache_info.hits, 1)


if __name__ == "__main__":
    unittest.main()
