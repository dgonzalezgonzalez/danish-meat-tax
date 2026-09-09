import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from danish_meat_tax.stata_runner import run_stata


class StataFailureTest(unittest.TestCase):
    def test_do_file_error_is_detected_with_zero_process_exit(self):
        root = Path.cwd() / "tmp_tests" / ("stata_failure_" + uuid.uuid4().hex)
        root.mkdir(parents=True)
        try:
            (root / "broken.do").write_text("error 621\n")

            def failed_run(*args, **kwargs):
                (root / "broken.log").write_text("already preserved\nr(621);\n")
                return SimpleNamespace(returncode=0)

            with patch("danish_meat_tax.stata_runner.find_stata", return_value=Path("stata.exe")):
                with patch("danish_meat_tax.stata_runner.subprocess.run", side_effect=failed_run):
                    with self.assertRaisesRegex(RuntimeError, r"r\(621\)"):
                        run_stata(root, Path("broken.do"))
        finally:
            for file in root.iterdir():
                file.unlink()
            root.rmdir()
