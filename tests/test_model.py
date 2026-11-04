"""Model rules on a tiny hand-made schedule where the answers are obvious."""

from hts import model as m

ROWS = [
    ["6109", 0, "T-shirts, singlets, tank tops and similar garments, knitted or crocheted:", "", ""],
    ["6109.10.00", 1, "Of cotton", "16.5%", ""],
    ["6109.10.00.04", 2, "Men's or boys'", "", "doz."],
    ["6109.90", 1, "Of other textile materials:", "", ""],
    ["6109.90.10", 2, "Of man-made fibers", "32%", ""],
    ["8518", 0, "Microphones and stands therefor; loudspeakers, whether or not mounted in their enclosures:", "", ""],
    ["", 1, "Loudspeakers, whether or not mounted in their enclosures:", "", ""],
    ["8518.21.00.00", 2, "Single loudspeakers, mounted in their enclosures", "4.9%", "No."],
    ["8518.30", 1, "Headphones and earphones:", "", ""],
    ["8518.30.20.00", 2, "Other", "4.9%", "No."],
    ["0409.00.00", 0, "Natural honey", "1.9¢/kg", "kg"],
]


def schedule():
    return m.Schedule(ROWS)


def test_words_fold_plurals_and_drop_filler():
    assert m.words("Loudspeakers and T-shirts of cotton") == ["loudspeaker", "t-shirt", "shirt", "cotton"]
    assert m.stem("batteries") == "battery" and m.stem("brushes") == "brush" and m.stem("glass") == "glass"


def test_synonyms_add_schedule_words_and_say_so():
    toks, used = m.expand("Bluetooth speaker")
    assert used == ["bluetooth", "speaker"] and "loudspeaker" in toks and "speaker" in toks
    toks, used = m.expand("Bluetooth speaker", use_synonyms=False)
    assert used == [] and "loudspeaker" not in toks


def test_headings_and_paths():
    s = schedule()
    assert set(s.heading_text) == {"6109", "8518", "0409"}  # 0409 has no 4-digit line of its own
    line = next(ln for ln in s.lines if ln["code"] == "8518.21.00.00")
    assert line["path"][0].startswith("Microphones") and line["path"][-1].startswith("Single loudspeakers")
    assert line["path"][1].startswith("Loudspeakers")  # the uncoded group line is part of the path


def test_suggests_heading_and_best_line():
    r = schedule().suggest("Portable Bluetooth speaker")
    c = r["candidates"][0]
    assert c["heading"] == "8518" and c["line"]["code"] == "8518.21.00.00" and c["line"]["general"] == "4.9%"
    tee = next(ln for ln in schedule().lines if ln["code"] == "6109.10.00.04")
    assert tee["general"] == "16.5%"  # inherited from the 8-digit line above it
    assert r["sure"]


def test_not_sure_when_nothing_matches_or_its_close(monkeypatch):
    s = schedule()
    r = s.suggest("quantum zebra")
    assert not r["sure"] and r["candidates"] == [] and "none of its words" in r["reason"]
    r = s.suggest("cotton loudspeaker")  # words from two headings: 8518 wins, but not by much
    assert r["candidates"][0]["heading"] == "8518" and r["margin"] < 0.5
    monkeypatch.setattr(m, "MIN_MARGIN", 0.5)
    r = s.suggest("cotton loudspeaker")
    assert not r["sure"] and "too close" in r["reason"]


def test_evaluate_counts():
    r = m.evaluate(schedule(), [{"product": "Natural honey", "heading": "0409"},
                                {"product": "Men's cotton T-shirt", "heading": "6109"},
                                {"product": "quantum zebra", "heading": "8518"}])
    assert (r["n"], r["top1"]) == (3, round(2 / 3, 4))
    assert r["rows"][2]["got"] is None and not r["rows"][2]["sure"]
