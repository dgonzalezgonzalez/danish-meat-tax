import unittest

from danish_meat_tax.data_sources.heissepreise import _fixture_records
from danish_meat_tax.estimators import estimate_ate, estimate_event_study, estimate_heterogeneity, estimate_synthetic_did
from danish_meat_tax.normalize_products import normalize_records
from danish_meat_tax.panel_builder import build_balanced_panel


class EstimatorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        products = normalize_records(_fixture_records())
        cls.panel = build_balanced_panel(products, frequency="daily").panel

    def test_ate_returns_metadata_and_coefficient(self):
        result = estimate_ate(self.panel)
        self.assertIn("treated x post", set(result.coefficients["term"]))
        self.assertTrue(result.coefficients["p_value"].notna().all())
        self.assertGreater(result.metadata["n_obs"], 0)

    def test_heterogeneity_returns_subtype_terms(self):
        result = estimate_heterogeneity(self.panel)
        terms = " ".join(result.coefficients["term"])
        self.assertIn("beef", terms)
        self.assertIn("pork", terms)
        self.assertIn("lamb_sheep_goat", terms)

    def test_event_study_includes_reference_period_as_zero(self):
        result = estimate_event_study(self.panel)
        reference = result.coefficients[result.coefficients["relative_time"] == -1].iloc[0]
        self.assertEqual(reference["estimate"], 0.0)
        self.assertTrue(reference[["std_error", "conf_low", "conf_high"]].isna().all())

    def test_synthetic_did_returns_trends_and_weights(self):
        result = estimate_synthetic_did(self.panel)
        self.assertIn("synthetic DiD", set(result.coefficients["term"]))
        self.assertGreater(len(result.trends), 0)
        self.assertAlmostEqual(result.unit_weights["weight"].sum(), 1.0, places=6)
        self.assertAlmostEqual(result.time_weights["weight"].sum(), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
