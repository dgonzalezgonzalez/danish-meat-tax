import unittest

from danish_meat_tax.data_sources.production import jsonstat_rows


class ProductionSourceTest(unittest.TestCase):
    def test_jsonstat_dimension_order_missing_and_status(self):
        payload = {
            "id": ["geo", "time"], "size": [2, 2],
            "dimension": {
                "geo": {"category": {"index": {"SE": 1, "DK": 0}}},
                "time": {"category": {"index": {"2024-06": 0, "2024-07": 1}}},
            },
            "value": {"0": 10, "1": 12, "3": 20},
            "status": {"1": "p"},
        }
        rows = jsonstat_rows(payload)
        self.assertEqual(rows[1], {"geo": "DK", "time": "2024-07", "value": 12, "flag": "p"})
        self.assertIsNone(rows[2]["value"])
        self.assertEqual(rows[3]["geo"], "SE")
        self.assertEqual(rows[3]["value"], 20)
