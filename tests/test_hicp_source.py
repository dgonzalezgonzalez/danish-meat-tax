from __future__ import annotations

import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from danish_meat_tax.data_sources.hicp import HICP_FILENAME, download_hicp, prepare_hicp_panel


class HicpSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Path("tmp_tests").mkdir(exist_ok=True)

    def payload(self):
        categories = {
            "freq": ["M"], "unit": ["I15"], "coicop": ["CP01121"],
            "geo": ["DK", "SE", "EU27_2020", "NO"], "time": ["2024-05", "2024-06"],
        }
        return {
            "class": "dataset", "id": list(categories),
            "size": [len(c) for c in categories.values()],
            "dimension": {k: {"category": {"index": {c:i for i,c in enumerate(v)}}} for k,v in categories.items()},
            "value": {"0": 120.3, "1": 121.0, "2": 118.5, "4": 119, "5": 120, "6": 115, "7": 116},
            "status": {"1": "p", "3": "c"},
        }

    def test_preserves_country_month_alignment_missing_values_and_flags(self):
        with TemporaryDirectory(dir="tmp_tests") as folder:
            root=Path(folder)
            (root/"data/raw").mkdir(parents=True)
            (root/"data/raw"/HICP_FILENAME).write_text(json.dumps(self.payload()))
            with prepare_hicp_panel(root).open(encoding="utf-8") as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),4)
            self.assertEqual([(r["geo"],r["month"]) for r in rows],[("DK","2024-05"),("DK","2024-06"),("SE","2024-05"),("SE","2024-06")])
            self.assertEqual(rows[1]["flag"],"p")
            self.assertEqual(rows[3]["hicp"],"")
            self.assertEqual(rows[3]["flag"],"c")
            self.assertEqual(rows[2]["hicp"],"118.5")

    def test_rejects_wrong_index_unit(self):
        with TemporaryDirectory(dir="tmp_tests") as folder:
            root=Path(folder)
            (root/"data/raw").mkdir(parents=True)
            data=self.payload()
            data["dimension"]["unit"]["category"]["index"]={"RCH_A":0}
            (root/"data/raw"/HICP_FILENAME).write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                prepare_hicp_panel(root)

    def test_cached_download_does_not_refresh_snapshot(self):
        with TemporaryDirectory(dir="tmp_tests") as folder:
            raw=Path(folder)
            cached=raw/HICP_FILENAME
            cached.write_text("existing snapshot")
            with patch("danish_meat_tax.data_sources.hicp.urlopen") as request:
                self.assertEqual(download_hicp(raw),cached)
                request.assert_not_called()
            self.assertEqual(cached.read_text(),"existing snapshot")


if __name__ == "__main__":
    unittest.main()
