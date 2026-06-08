import unittest
from pathlib import Path

from danish_meat_tax.data_sources.heissepreise import extract_records, write_fixture


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


if __name__ == "__main__":
    unittest.main()
