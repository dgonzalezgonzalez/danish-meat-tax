import unittest
from pathlib import Path

from danish_meat_tax.config import PipelinePaths
from danish_meat_tax.pipeline import build_parser, run_stage


class PipelineSmokeTest(unittest.TestCase):
    def test_parser_has_expected_stages(self):
        parser = build_parser()
        args = parser.parse_args(["all", "--fixture"])
        self.assertEqual(args.stage, "all")
        self.assertTrue(args.fixture)

    def test_fixture_all_pipeline_runs(self):
        paths = PipelinePaths(Path.cwd() / "tmp_tests" / "pipeline")
        run_stage("all", paths, fixture=True, frequency="daily")
        self.assertTrue((paths.processed_dir / "commodity_panel.csv").exists())
        self.assertTrue((paths.models_dir / "ate.csv").exists())
        self.assertTrue((paths.figures_dir / "event_study_overall.png").exists())
        self.assertTrue((paths.tables_dir / "ate_results.tex").exists())


if __name__ == "__main__":
    unittest.main()
