import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from danish_meat_tax.data_sources.heissepreise import download_json, extract_records, write_fixture


class HeissepreiseSourceTest(unittest.TestCase):
    def test_fixture_writes_records(self):
        tmp = Path.cwd() / "tmp_tests" / "heissepreise_source"
        tmp.mkdir(parents=True, exist_ok=True)
        result = write_fixture(tmp)
        self.assertTrue(result.path.exists())
        self.assertGreater(result.record_count, 0)
        self.assertTrue(result.fixture)

    def test_extract_records_from_store_mapping(self):
        payload = {"netto": [{"name": "A", "price": 1}], "meta": {"ignored": True}}
        records = extract_records(payload)
        self.assertEqual(records[0]["store"], "netto")

    def test_extract_records_expands_price_history(self):
        payload = [
            {
                "store": "netto",
                "id": "1",
                "name": "Hakket oksekød",
                "price": 50,
                "priceHistory": [
                    {"date": "2024-06-20", "price": 45, "quantity": 1, "unit": "kg"},
                    {"date": "2024-06-25", "price": 47, "quantity": 1, "unit": "kg"},
                ],
            }
        ]
        records = extract_records(payload)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["date"], "2024-06-20")
        self.assertEqual(records[1]["price"], 47)

    def test_download_uses_cache_manifest_when_available(self):
        tmp = Path.cwd() / "tmp_tests" / "heissepreise_cache"
        tmp.mkdir(parents=True, exist_ok=True)
        cached = write_fixture(tmp)
        (tmp / "heissepreise_cache_manifest.json").write_text(
            json.dumps(
                {
                    "source_url": "fixture-cache",
                    "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "path": cached.path.name,
                    "record_count": cached.record_count,
                    "sha256": "fixture",
                }
            ),
            encoding="utf-8",
        )
        result = download_json(tmp, source_urls=("fixture-cache",), max_age_days=30)
        self.assertTrue(result.cached)
        self.assertEqual(result.path, cached.path)


if __name__ == "__main__":
    unittest.main()
