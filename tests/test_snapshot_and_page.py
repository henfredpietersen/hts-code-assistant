"""The real schedule, both product sets, the numbers the README quotes, and the page."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from hts import model as m

ROOT = Path(__file__).resolve().parents[1]
SNAP = json.loads((ROOT / "data" / "hts.json").read_text(encoding="utf-8"))
DEV = json.loads((ROOT / "data" / "golden_dev.json").read_text(encoding="utf-8"))["items"]
TEST = json.loads((ROOT / "data" / "golden_test.json").read_text(encoding="utf-8"))["items"]
S = m.Schedule(SNAP["rows"])


def test_every_label_is_a_real_heading_and_the_sets_dont_overlap():
    for it in DEV + TEST:
        assert it["heading"] in S.heading_text, it
    assert not {i["product"].lower() for i in DEV} & {i["product"].lower() for i in TEST}
    assert (len(DEV), len(TEST)) == (65, 41)


def test_test_set_was_committed_before_the_synonym_list():
    def first_commit(path):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%ct", "--", path], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
        return int(out[-1]) if out else None
    t_test, t_syn = first_commit("data/golden_test.json"), first_commit("hts/synonyms.py")
    if t_test is None or t_syn is None:  # shallow clone without that history: nothing to check
        return
    assert t_test < t_syn


def test_synonyms_dont_mention_test_products():
    from hts.synonyms import SYNONYMS
    test_words = {w for it in TEST for w in it["product"].lower().replace(",", " ").split()}
    leaked = {k for k in SYNONYMS if k in test_words} - {"computer", "petrol", "car"}
    # computer, petrol and car came from development products (laptop computer, petrol car)
    assert not leaked, leaked


def test_readme_numbers_match_a_fresh_run():
    dev, test = m.evaluate(S, DEV), m.evaluate(S, TEST)
    dev_n, test_n = m.evaluate(S, DEV, False), m.evaluate(S, TEST, False)
    assert (dev["top1"], dev["top3"], dev["answered"], dev["right_when_sure"]) == (0.8308, 0.9385, 0.7077, 0.9565)
    assert (test["top1"], test["top3"], test["answered"], test["right_when_sure"], test["wrong_but_sure"]) == \
        (0.7073, 0.8293, 0.7073, 0.7931, 6)
    assert (dev_n["top1"], test_n["top1"]) == (0.6615, 0.7073)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for s in ("83.1%", "93.8%", "95.7%", "70.8%", "70.7%", "82.9%", "79.3%", "66.2%", "6 of the 29", "1,228", "23,193"):
        assert s in readme, s


def test_published_page_embeds_current_code():
    spec = importlib.util.spec_from_file_location("build", ROOT / "web" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (ROOT / "docs" / "demo.js").read_text(encoding="utf-8") == mod.build(), "docs/demo.js is stale: run python web/build.py"


def test_driver_runs_like_the_page():
    sys.path.insert(0, str(ROOT / "web"))
    import driver

    files = [(ROOT / "data" / n).read_text(encoding="utf-8") for n in ("hts.json", "golden_dev.json", "golden_test.json")]
    info = json.loads(driver.setup(*files))
    assert info["scores"]["test"]["synonyms"]["top1"] == 0.7073 and info["headings"] == 1228
    out = json.loads(driver.suggest("A gift for my mum"))
    assert not out["sure"]
