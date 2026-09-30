#!/usr/bin/env python3
"""Re-fetch docs.bithuman.ai/performance.json and rewrite data/performance.{json,csv}.

Standard library only. It never renders anything: it copies the published numbers.

    python3 scripts/regen.py                      # fetch the live file
    python3 scripts/regen.py --source file.json   # use a local copy (tests, offline)
    python3 scripts/regen.py --check              # exit 1 if data/ would change
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = "https://docs.bithuman.ai/performance.json"
METHOD_URL = "https://docs.bithuman.ai/performance/method"
SUPPORTED_SCHEMA = 1
COLUMNS = [
    "row_id", "runs_on", "hardware", "model", "x_realtime", "realtime",
    "sustained", "release", "measured_on", "clip_seconds",
]
REPO = Path(__file__).resolve().parent.parent


def fetch(source: str, timeout: float = 30.0) -> bytes:
    """Return the raw bytes of a URL or a local file path."""
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "avatar-speed-regen/1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    return Path(source).read_bytes()


def parse(raw: bytes) -> dict:
    perf = json.loads(raw)
    if perf.get("schema") != SUPPORTED_SCHEMA:
        raise ValueError(f"unsupported performance.json schema: {perf.get('schema')!r}")
    if not isinstance(perf.get("rows"), list):
        raise ValueError("performance.json has no rows list")
    return perf


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def csv_rows(perf: dict) -> list[dict]:
    """One row per published (configuration, model) cell, in source order."""
    out = []
    for row in perf["rows"]:
        if not row.get("published", False):
            continue
        for model, cell in (row.get("cells") or {}).items():
            if not cell or cell.get("x_realtime") is None:
                continue
            x = cell["x_realtime"]
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise ValueError(f"{row.get('id')}/{model}: x_realtime is not a number: {x!r}")
            out.append({
                "row_id": row["id"],
                "runs_on": row.get("label", ""),
                "hardware": row.get("hardware", ""),
                "model": model,
                "x_realtime": _fmt(x),
                "realtime": _fmt(cell.get("realtime")),
                "sustained": _fmt(bool(row.get("sustained", False))),
                "release": _fmt(cell.get("release")),
                "measured_on": _fmt(cell.get("measured_on")),
                "clip_seconds": _fmt((cell.get("clip") or {}).get("seconds")),
            })
    return out


def render_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def render_snapshot(raw: bytes, perf: dict, source: str, fetched: str) -> str:
    snapshot = {
        "source_url": source,
        "method_url": METHOD_URL,
        "fetched": fetched,
        "generated": perf.get("generated"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "performance": perf,
    }
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def _existing_sha(path: Path) -> str | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("sha256")
    except (OSError, ValueError):
        return None


def regen(raw: bytes, data_dir: Path, source_url: str, fetched: str, check: bool = False) -> list[str]:
    """Write the snapshot and CSV; return the file names that changed (or would change)."""
    perf = parse(raw)
    csv_text = render_csv(csv_rows(perf))
    json_path, csv_path = data_dir / "performance.json", data_dir / "performance.csv"
    changed = []
    # An unchanged source keeps the old snapshot, so re-runs do not churn the fetch date.
    if _existing_sha(json_path) != hashlib.sha256(raw).hexdigest():
        changed.append(json_path.name)
        if not check:
            json_path.write_text(render_snapshot(raw, perf, source_url, fetched), encoding="utf-8")
    old_csv = csv_path.read_text(encoding="utf-8") if csv_path.exists() else None
    if old_csv != csv_text:
        changed.append(csv_path.name)
        if not check:
            csv_path.write_text(csv_text, encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default=SOURCE_URL, help="URL or local path of performance.json")
    ap.add_argument("--source-url", default=SOURCE_URL, help="URL recorded in the snapshot")
    ap.add_argument("--data-dir", type=Path, default=REPO / "data")
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="fetch date (YYYY-MM-DD)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if data/ is stale")
    args = ap.parse_args(argv)
    args.data_dir.mkdir(parents=True, exist_ok=True)
    changed = regen(fetch(args.source), args.data_dir, args.source_url, args.date, args.check)
    verb = "would change" if args.check else "updated"
    print(f"{verb}: {', '.join(changed)}" if changed else "up to date")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
