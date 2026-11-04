"""Build data/hts.json from the US International Trade Commission's HTS export.

    python scripts/make_snapshot.py            # downloads chapters 01-97 (run on GitHub's servers)

The workflow .github/workflows/snapshot.yml runs this. For each chapter it calls the USITC's
public export (hts.usitc.gov/reststop/exportList) and keeps every line: code (when it has one),
indent, description, general duty rate and units. Chapters 98 and 99 (special provisions and
temporary legislation) are left out because they aren't product descriptions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

BASE = "https://hts.usitc.gov/reststop"
UA = "hts-code-assistant snapshot (github.com/henfredpietersen/hts-code-assistant)"
CHAPTERS = [f"{c:02d}" for c in range(1, 98) if c != 77]  # chapter 77 is reserved


def get_json(url: str, tries: int = 3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def build() -> dict:
    releases = get_json(f"{BASE}/releaseList")
    current = next((r for r in releases if r.get("status") == "current"), releases[0])
    rows = []
    for ch in CHAPTERS:
        data = get_json(f"{BASE}/exportList?from={ch}00&to={ch}99&format=JSON&styles=false")
        for d in data:
            desc = " ".join((d.get("description") or "").split())
            if not desc:
                continue
            rows.append([(d.get("htsno") or "").strip(), int(d.get("indent") or 0), desc,
                         (d.get("general") or "").strip(), ", ".join(d.get("units") or [])])
        time.sleep(0.3)
    body = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return {
        "source": {"export": f"{BASE}/exportList", "release": current.get("name"),
                   "release_title": current.get("title"), "release_start": current.get("releaseStartDate"),
                   "publisher": "U.S. International Trade Commission, Harmonized Tariff Schedule",
                   "rows_sha256": hashlib.sha256(body.encode()).hexdigest()},
        "chapters": CHAPTERS,
        "rows": rows,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/hts.json", type=Path)
    a = p.parse_args(argv)
    snap = build()
    a.out.write_text(json.dumps(snap, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    coded = sum(1 for r in snap["rows"] if r[0])
    print(f"{snap['source']['release']}: {len(snap['rows']):,} lines, {coded:,} with a code -> {a.out} "
          f"({a.out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
