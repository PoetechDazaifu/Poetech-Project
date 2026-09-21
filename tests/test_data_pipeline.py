import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import app as application_module
from app import app, clear_wordcloud_cache, clear_wordcloud_rate_limits, wordcloud_cache_stats
from convert_to_json import has_blocking_errors, validate_dataframe
from init_db import DB_FILE, build_database, normalize_tags


class DataPipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        clear_wordcloud_rate_limits()

    def test_normalize_tags_supports_source_delimiters(self):
        self.assertEqual(normalize_tags("こども, 福祉、観光"), ["こども", "福祉", "観光"])
        self.assertEqual(normalize_tags(None), [])

    def test_validation_reports_unknown_tags_without_blocking_import(self):
        import pandas as pd

        report = validate_dataframe(pd.DataFrame([{
            "句": "テスト句", "データ元": "テスト", "年齢": None, "在住地": None,
            "AIタグ": "観光、独自タグ", "場所": "太宰府市内",
        }]))
        self.assertEqual(report["unknown_tags"], ["独自タグ"])
        self.assertFalse(has_blocking_errors(report))

    def test_atomic_database_build_preserves_existing_db_on_invalid_input(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            database = directory / "poems.db"
            database.write_text("previous database", encoding="utf-8")
            invalid_json = directory / "invalid.json"
            invalid_json.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_database(invalid_json, database)
            self.assertEqual(database.read_text(encoding="utf-8"), "previous database")

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

    def test_facets_and_three_character_full_text_search(self):
        facets = self.client.get("/facets")
        facet_payload = facets.get_json()
        search = self.client.post("/search", json={"query": "太宰府"})
        self.assertEqual(facets.status_code, 200)
        self.assertTrue(any(item["value"] == "福祉" for item in facet_payload["tags"]))
        self.assertTrue(any(item["value"] == "太宰府市内" for item in facet_payload["locations"]))
        self.assertEqual(search.status_code, 200)
        self.assertGreater(search.get_json()["total"], 0)

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
        self.assertIn('<option value="ポスト">ポスト</option>', document)
        self.assertIn('<option value="句会">句会</option>', document)
        self.assertIn('<option value="広報">広報</option>', document)
        self.assertNotIn("axios", document)

    def test_security_headers_are_returned(self):
        response = self.client.get("/healthz")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")

    def test_wordcloud_rate_limit(self):
        original_limit = application_module.WORDCLOUD_RATE_LIMIT
        application_module.WORDCLOUD_RATE_LIMIT = 1
        try:
            self.assertEqual(self.client.post("/wordcloud", json={"tag": "福祉"}).status_code, 200)
            response = self.client.post("/wordcloud", json={"tag": "福祉"})
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.headers["Retry-After"], "60")
        finally:
            application_module.WORDCLOUD_RATE_LIMIT = original_limit

    def test_wordcloud_is_cached_for_the_same_filters(self):
        clear_wordcloud_cache()
        first = self.client.post("/wordcloud", json={"tag": "福祉"})
        second = self.client.post("/wordcloud", json={"tag": "福祉"})
        cache_info = wordcloud_cache_stats()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data, second.data)
        self.assertEqual(cache_info["misses"], 1)
        self.assertEqual(cache_info["hits"], 1)


if __name__ == "__main__":
    unittest.main()
