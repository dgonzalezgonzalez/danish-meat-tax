import unittest

from danish_meat_tax.normalize_products import normalize_records


class CommodityClassifierTest(unittest.TestCase):
    def test_normalize_records_adds_policy_fields(self):
        frame = normalize_records(
            [
                {
                    "date": "2024-06-20",
                    "store": "Netto",
                    "product_id": "1",
                    "product_name": "Hakket oksekød",
                    "category": "meat",
                    "price": "45,2",
                }
            ]
        )
        self.assertEqual(frame.loc[0, "commodity"], "beef")
        self.assertTrue(bool(frame.loc[0, "treated"]))
        self.assertEqual(frame.loc[0, "quality_flag"], "ok")

    def test_invalid_price_is_excluded(self):
        frame = normalize_records(
            [
                {
                    "date": "2024-06-20",
                    "store": "Netto",
                    "product_name": "Svinekotelet",
                    "price": "bad",
                }
            ]
        )
        self.assertEqual(len(frame), 0)


if __name__ == "__main__":
    unittest.main()
