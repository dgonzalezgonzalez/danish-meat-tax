import unittest

import pandas as pd

from danish_meat_tax.data_sources.heissepreise import _fixture_records
from danish_meat_tax.normalize_products import normalize_records
from danish_meat_tax.panel_builder import build_balanced_panel


class PanelBuilderTest(unittest.TestCase):
    def test_balanced_panel_has_equal_pre_post_periods(self):
        products = normalize_records(_fixture_records())
        result = build_balanced_panel(products, frequency="daily", require_complete_units=True)
        self.assertEqual(result.diagnostics["balanced_periods_pre"], result.diagnostics["balanced_periods_post"])
        relative = set(result.panel["relative_time"].unique())
        self.assertNotIn(0, relative)
        self.assertGreater(result.diagnostics["treated_units"], 0)
        self.assertGreater(result.diagnostics["control_units"], 0)

    def test_weekly_panel_uses_balanced_periods(self):
        products = normalize_records(_fixture_records())
        result = build_balanced_panel(products, frequency="weekly")
        self.assertEqual(result.diagnostics["balanced_periods_pre"], result.diagnostics["balanced_periods_post"])

    def test_monthly_and_quarterly_panel_frequencies(self):
        products = normalize_records(_fixture_records())
        expanded = pd.concat(
            [
                products.assign(date=products["date"] - pd.DateOffset(months=4)),
                products.assign(date=products["date"] - pd.DateOffset(months=1)),
                products,
                products.assign(date=products["date"] + pd.DateOffset(months=1)),
                products.assign(date=products["date"] + pd.DateOffset(months=4)),
            ],
            ignore_index=True,
        )
        monthly = build_balanced_panel(expanded, frequency="monthly")
        quarterly = build_balanced_panel(expanded, frequency="quarterly")
        self.assertEqual(monthly.diagnostics["frequency"], "monthly")
        self.assertEqual(quarterly.diagnostics["frequency"], "quarterly")
        self.assertIn(-1, set(monthly.panel["relative_time"]))
        self.assertIn(1, set(monthly.panel["relative_time"]))

    def test_unbalanced_units_can_be_retained_with_pre_and_post_support(self):
        products = normalize_records(_fixture_records())
        partial = products[~((products["product_id"].str.contains("milk")) & (products["date"].dt.day.isin([11, 12, 13])))]
        result = build_balanced_panel(partial, frequency="daily", require_complete_units=False, unit_level="product_store")
        self.assertIn("Netto::netto_milk", set(result.panel["unit_id"]))

    def test_insufficient_coverage_errors(self):
        products = pd.DataFrame(
            [
                {
                    "date": pd.Timestamp("2024-06-20"),
                    "unit_id": "a",
                    "price": 1.0,
                    "store": "s",
                    "product_id": "a",
                    "product_name": "milk",
                    "commodity": "dairy",
                    "treated": False,
                    "treatment_group": "control_non_meat",
                    "policy_confidence": "control",
                }
            ]
        )
        with self.assertRaises(ValueError):
            build_balanced_panel(products)


if __name__ == "__main__":
    unittest.main()
