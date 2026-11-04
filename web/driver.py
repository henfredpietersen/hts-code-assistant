"""Glue between the demo page and hts/. The page runs this and hts/ unchanged in the browser
(Pyodide). tests/test_web_demo.py makes the same calls under CPython."""

from __future__ import annotations

import json

from hts import model as m

_state: dict = {}


def setup(snapshot_json: str, dev_json: str, test_json: str) -> str:
    snap = json.loads(snapshot_json)
    schedule = m.Schedule(snap["rows"])
    _state["s"] = schedule
    dev, test = json.loads(dev_json)["items"], json.loads(test_json)["items"]
    scores = {name: {"synonyms": m.evaluate(schedule, items, True), "no_synonyms": m.evaluate(schedule, items, False)}
              for name, items in (("dev", dev), ("test", test))}
    return json.dumps({"source": snap["source"], "scores": scores, "headings": len(schedule.heading_text),
                       "lines": len(schedule.lines), "min_margin": m.MIN_MARGIN})


def suggest(text: str) -> str:
    return json.dumps(_state["s"].suggest(text))
