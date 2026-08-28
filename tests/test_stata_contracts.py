import unittest
from pathlib import Path

import pandas as pd

from danish_meat_tax.stata_runner import prepare_micro_panel


class StataContractsTest(unittest.TestCase):
    def test_prepare_micro_panel_round_trip(self):
        root = Path.cwd() / "tmp_tests" / "stata_contract"
        root.mkdir(parents=True, exist_ok=True)
        source = root / "panel.csv"
        destination = root / "panel.dta"
        pd.DataFrame(
            {
                "unit_id": ["store::1"],
                "period": ["2024-07-01"],
                "price": [100.0],
                "store": ["store"],
                "commodity": ["beef"],
                "treated": [True],
                "treatment_group": ["beef"],
                "relative_time": [1],
                "did": [1],
                "log_price": [4.60517],
            }
        ).to_csv(source, index=False)
        prepare_micro_panel(source, destination)
        converted = pd.read_stata(destination)
        self.assertEqual(converted.loc[0, "treatment_group"], "beef")
        self.assertEqual(int(converted.loc[0, "relative_time"]), 1)

    def test_analysis_windows_and_estimators_are_stata_owned(self):
        aggregate = Path("scripts/stata/aggregate_analysis.do").read_text(encoding="utf-8")
        micro = Path("scripts/stata/microdata_analysis.do").read_text(encoding="utf-8")
        master = Path("scripts/stata/master.do").read_text(encoding="utf-8")
        self.assertIn("local window_start = tm(2023m4)", aggregate)
        self.assertIn("local window_end = tm(2025m9)", aggregate)
        self.assertIn("pre_count == 15 & post_count == 15", aggregate)
        self.assertIn('inlist(product_code, "011222", "011223"', aggregate)
        self.assertNotIn("synth ln_cpi", aggregate)
        self.assertIn("sdid ln_cpi", aggregate)
        self.assertIn("newey cpi_diff_bar post_hac, lag(2)", aggregate)
        self.assertIn("(`panel_observations') (`panel_units')", aggregate)
        self.assertIn("keep if relative_time <= 15", micro)
        self.assertIn("areg log_price treated_post", micro)
        self.assertIn("replace event_time = relative_time - 1 if relative_time > 0", micro)
        self.assertNotIn("sdid log_price", micro)
        self.assertIn("microdata_analysis.do", master)
        self.assertFalse(Path("src/danish_meat_tax/estimators.py").exists())
        self.assertFalse(Path("src/danish_meat_tax/output.py").exists())


if __name__ == "__main__":
    unittest.main()
