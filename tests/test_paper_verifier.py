import unittest

from scripts.verify_paper_numbers import PAPER, verify_main_table, verify_magnitude_table, verify_window_table


class PaperVerifierTest(unittest.TestCase):
    def test_swapped_official_columns_fail_reconciliation(self):
        paper = PAPER.read_text(encoding="utf-8")
        verify_main_table(paper)
        swapped = paper.replace(
            "0.102*** & 0.064** & 0.076* & 0.016",
            "0.102*** & 0.016 & 0.076* & 0.064**",
            1,
        ).replace(
            "(0.013) & (0.030) & (0.046) & (0.029)",
            "(0.013) & (0.029) & (0.046) & (0.030)",
            1,
        )
        self.assertNotEqual(swapped, paper)
        with self.assertRaisesRegex(AssertionError, "ATT columns"):
            verify_main_table(swapped)

    def test_wrong_appendix_rounding_fails_reconciliation(self):
        paper = PAPER.read_text(encoding="utf-8")
        verify_window_table(paper)
        wrong = paper.replace(
            "Danish beef versus food CPI & 0.076 & 0.043 & 0.061 & 0.060",
            "Danish beef versus food CPI & 0.076 & 0.043 & 0.062 & 0.060",
            1,
        )
        self.assertNotEqual(wrong, paper)
        with self.assertRaisesRegex(AssertionError, "Appendix window ATT"):
            verify_window_table(wrong)

    def test_swapped_magnitude_headers_fail_reconciliation(self):
        paper = PAPER.read_text(encoding="utf-8")
        verify_magnitude_table(paper)
        wrong = paper.replace(
            "Anchor, DKK/kg & Domestic CPI DiD & Country beef HICP SDiD",
            "Anchor, DKK/kg & Country beef HICP SDiD & Domestic CPI DiD",
            1,
        )
        self.assertNotEqual(wrong, paper)
        with self.assertRaisesRegex(AssertionError, "Table 3 estimator headings"):
            verify_magnitude_table(wrong)


if __name__ == "__main__":
    unittest.main()
