"""Tests for scripts/regen.py (stdlib unittest, no network): python3 -m unittest -v"""
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import regen  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "performance.json"


class RegenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.raw = FIXTURE.read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *extra):
        out = io.StringIO()
        old, sys.stdout = sys.stdout, out
        try:
            code = regen.main(["--source", str(FIXTURE), "--data-dir", str(self.data), "--date", "2026-01-03", *extra])
        finally:
            sys.stdout = old
        return code, out.getvalue()

    def read_csv(self):
        with open(self.data / "performance.csv", newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_rows_published_cells_only(self):
        rows = regen.csv_rows(regen.parse(self.raw))
        self.assertEqual([(r["row_id"], r["model"]) for r in rows],
                         [("linux-cpu", "essence-2"), ("phone-sustained", "expression-2")])

    def test_csv_columns_and_values(self):
        self.assertEqual(self.run_main()[0], 0)
        rows = self.read_csv()
        self.assertEqual(list(rows[0].keys()), regen.COLUMNS)
        self.assertEqual(rows[0]["hardware"], "Test CPU, 8 threads")  # comma survives quoting
        self.assertEqual(rows[0]["x_realtime"], "2.0")
        self.assertEqual(rows[1]["sustained"], "true")
        self.assertEqual(rows[1]["clip_seconds"], "16.285")

    def test_no_fps_or_memory_in_csv(self):
        self.run_main()
        header = (self.data / "performance.csv").read_text(encoding="utf-8").splitlines()[0]
        self.assertNotIn("fps", header)
        self.assertNotIn("ram", header)

    def test_snapshot_keeps_source_verbatim(self):
        self.run_main()
        snap = json.loads((self.data / "performance.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["source_url"], regen.SOURCE_URL)
        self.assertEqual(snap["fetched"], "2026-01-03")
        self.assertEqual(snap["generated"], "2026-01-02")
        self.assertEqual(snap["performance"], json.loads(self.raw))
        self.assertEqual(len(snap["sha256"]), 64)

    def test_rerun_is_idempotent_and_check_passes(self):
        self.run_main()
        before = (self.data / "performance.json").read_bytes()
        code, out = self.run_main("--date", "2099-01-01")  # a later --date overrides the first
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "up to date")
        self.assertEqual((self.data / "performance.json").read_bytes(), before)  # fetch date not churned
        self.assertEqual(self.run_main("--check")[0], 0)

    def test_check_detects_stale_data_and_writes_nothing(self):
        code, out = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("would change", out)
        self.assertFalse((self.data / "performance.csv").exists())

    def test_rejects_unknown_schema(self):
        with self.assertRaises(ValueError):
            regen.parse(json.dumps({"schema": 2, "rows": []}).encode())

    def test_rejects_non_numeric_speed(self):
        bad = json.loads(self.raw)
        bad["rows"][0]["cells"]["essence-2"]["x_realtime"] = "fast"
        with self.assertRaises(ValueError):
            regen.csv_rows(regen.parse(json.dumps(bad).encode()))


class RepoDataTests(unittest.TestCase):
    """The committed data/ must be exactly what regen.py makes from the committed snapshot."""

    def test_committed_csv_matches_committed_snapshot(self):
        snap = json.loads((REPO / "data" / "performance.json").read_text(encoding="utf-8"))
        expected = regen.render_csv(regen.csv_rows(snap["performance"]))
        self.assertEqual((REPO / "data" / "performance.csv").read_text(encoding="utf-8"), expected)

    def test_every_published_row_is_real_time(self):
        with open(REPO / "data" / "performance.csv", newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["realtime"], "true", r)
            self.assertGreaterEqual(float(r["x_realtime"]), 1.0, r)


if __name__ == "__main__":
    unittest.main()
