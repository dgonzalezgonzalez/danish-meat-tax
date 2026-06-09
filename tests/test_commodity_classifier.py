import unittest

from danish_meat_tax.normalize_products import normalize_price, normalize_records


class CommodityClassifierTest(unittest.TestCase):
    def test_normalize_records_adds_policy_and_price_fields(self):
        frame = normalize_records(
            [
                {
                    "date": "2024-06-20",
                    "store": "Netto",
                    "product_id": "1",
                    "product_name": "Hakket oksekoed 500 g",
                    "category": "meat",
                    "price": "45,2",
                    "quantity": 500,
                    "unit": "g",
                }
            ]
        )
        self.assertEqual(frame.loc[0, "commodity"], "beef")
        self.assertTrue(bool(frame.loc[0, "treated"]))
        self.assertEqual(frame.loc[0, "quality_flag"], "ok")
        self.assertEqual(frame.loc[0, "normalized_price_unit"], "dkk_per_kg")
        self.assertAlmostEqual(frame.loc[0, "normalized_price"], 90.4)

    def test_normalize_price_converts_common_units(self):
        self.assertEqual(normalize_price(40, 500, "g", "x")[:2], (80, "dkk_per_kg"))
        self.assertEqual(normalize_price(50, 1, "kg", "x")[:2], (50, "dkk_per_kg"))
        self.assertEqual(normalize_price(12, 1, "l", "milk")[:2], (12, "dkk_per_liter"))

    def test_normalize_price_parses_name_when_unit_is_count(self):
        normalized, unit, quantity, quantity_unit, status = normalize_price(40, 1, "stk", "Oksekoed 500 g")
        self.assertEqual(status, "ok")
        self.assertEqual(unit, "dkk_per_kg")
        self.assertEqual(quantity, 500)
        self.assertEqual(quantity_unit, "g")
        self.assertAlmostEqual(normalized, 80)

    def test_invalid_price_is_excluded(self):
        frame = normalize_records(
            [
                {
                    "date": "2024-06-20",
                    "store": "Netto",
                    "product_name": "Svinekotelet 500 g",
                    "price": "bad",
                    "quantity": 500,
                    "unit": "g",
                }
            ]
        )
        self.assertEqual(len(frame), 0)


if __name__ == "__main__":
    unittest.main()
