"""How the settings in hts/model.py were picked, on the development set only.

    python scripts/tune.py

1. BLEND: how much of a heading's score comes from the whole heading document versus its single
   best line. Picked 0.3 (top-1 on dev: 0.0 -> 81.5%, 0.3 -> 83.1%, 1.0 -> 69.2%).
2. MIN_MARGIN: how far ahead the top heading must be before it answers. Picked 0.15: on dev it
   answers 71% of products and 95.7% of those are right. MIN_SCORE made no difference in the
   range tried, so it stays at 0.12.

data/golden_test.json is not read here.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hts import model as m  # noqa: E402


def main() -> int:
    rows = json.loads((ROOT / "data" / "hts.json").read_text(encoding="utf-8"))["rows"]
    dev = json.loads((ROOT / "data" / "golden_dev.json").read_text(encoding="utf-8"))["items"]
    schedule = m.Schedule(rows)
    for blend in (0.0, 0.3, 0.5, 0.7, 1.0):
        m.BLEND = blend
        r = m.evaluate(schedule, dev)
        print(f"BLEND {blend}: top-1 {r['top1']:.1%}, top-3 {r['top3']:.1%}")
    m.BLEND = 0.3
    results = [schedule.suggest(it["product"]) for it in dev]
    for margin in (0.0, 0.05, 0.1, 0.15, 0.2, 0.3):
        sure = [(r, it) for r, it in zip(results, dev, strict=True) if r["candidates"] and r["margin"] >= margin]
        right = sum(r["candidates"][0]["heading"] == it["heading"] for r, it in sure)
        print(f"MIN_MARGIN {margin}: answers {len(sure) / len(dev):.0%}, right when it answers {right / len(sure):.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
