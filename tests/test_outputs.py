import unittest
from pathlib import Path

from danish_meat_tax.data_sources.heissepreise import write_fixture
from danish_meat_tax.estimators import run_estimations
from danish_meat_tax.normalize_products import build_processed_products
from danish_meat_tax.output import make_outputs
from danish_meat_tax.panel_builder import write_panel


class OutputsTest(unittest.TestCase):
    def test_outputs_write_plot_and_latex(self):
        root = Path.cwd() / "tmp_tests" / "outputs"
        root.mkdir(parents=True, exist_ok=True)
        raw = write_fixture(root / "raw")
        products_path = root / "processed" / "products.csv"
        panel_path = root / "processed" / "panel.csv"
        diagnostics_path = root / "diagnostics" / "panel.csv"
        build_processed_products(raw.path, products_path)
        write_panel(products_path, panel_path, diagnostics_path)
        run_estimations(panel_path, root / "models")
        outputs = make_outputs(root / "models", root / "figures", root / "tables")
        self.assertTrue(outputs["event_study_plot"].exists())
        self.assertTrue(outputs["ate_table"].read_text(encoding="utf-8").startswith("\\begin{table}"))


if __name__ == "__main__":
    unittest.main()
