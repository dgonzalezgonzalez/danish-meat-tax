import unittest

from scripts.verify_paper_numbers import PAPER, verify_main_table


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


if __name__ == "__main__":
    unittest.main()
