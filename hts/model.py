"""Suggest US tariff (HTS) codes for a product description, or say it isn't sure.

Standard library only, so the same file runs in the browser (Pyodide) and in CI.

1. Every line of the schedule is attached to its 4-digit heading (from the first four digits
   of its code, or the code above it for uncoded group lines like "Horses:").
2. Two kinds of search document: each heading (its text counted three times, because it's the
   legal description, plus every line under it), and each 8- or 10-digit line with its full
   path ("Footwear > Other footwear > With uppers of textile materials > ...").
3. A query is scored with TF-IDF word matching. Plurals are folded, and everyday words get the
   schedule's own words added (hts/synonyms.py).
4. A heading's score is 0.3 x its heading-document match + 0.7 x its best line's match. That
   blend was picked on the development set (scripts/tune.py), never on the test set. The best
   line inside each top heading is the suggested code.
5. Not sure: if the top heading's score is low, or the runner-up is close behind, it says so
   and shows the candidates instead of one answer.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .synonyms import SYNONYMS

MIN_SCORE = 0.12   # below this, the best heading is too weak a match
MIN_MARGIN = 0.15  # (top - second) / top below this means a near tie
HEADING_WEIGHT = 3
BLEND = 0.3        # weight of the heading-document score; the rest is the best line's score
STOP = set("""a an and or of the for with without to in on at by from its it their other others not than
    whether nor kind kinds used use such as be is are this that these those thereof parts accessories articles
    article etc including include includes excluding except new old type types style""".split())
WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("es") and w[:-2].endswith(("s", "x", "ch", "sh")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def words(text: str) -> list[str]:
    out = []
    for w in WORD.findall(text.lower().replace("’", "'").replace("'s ", " ")):
        for part in [w] + (w.split("-") if "-" in w else []):
            if part not in STOP and len(part) > 1 and not part.isdigit():
                out.append(stem(part))
    return out


def expand(query: str, use_synonyms: bool = True) -> tuple[list[str], list[str]]:
    """Query words, plus schedule words from the synonym list. Returns (words, synonyms used)."""
    base = words(query)
    if not use_synonyms:
        return base, []
    low = " " + " ".join(WORD.findall(query.lower())) + " "
    used, extra = [], []
    for phrase in sorted(SYNONYMS, key=len, reverse=True):
        if f" {phrase} " in low:
            used.append(phrase)
            extra += words(SYNONYMS[phrase])
            low = low.replace(f" {phrase} ", " ")
    return base + extra, used


def _idf(docs) -> dict[str, float]:
    docs = list(docs)
    df = Counter()
    for toks in docs:
        df.update(set(toks))
    n = len(docs)
    return {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}


def _vec(toks: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(t for t in toks if t in idf)
    v = {t: (1 + math.log(c)) * idf[t] for t, c in tf.items()}
    norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {t: x / norm for t, x in v.items()}


def code_digits(code: str) -> str:
    return code.replace(".", "")


class Schedule:
    def __init__(self, rows: list[list]):
        self.rows = rows
        self.heading_text: dict[str, str] = {}
        self.heading_docs: dict[str, list[str]] = defaultdict(list)
        self.lines: list[dict] = []  # 8/10-digit lines with their path inside the heading
        stack: list[tuple[int, str, str]] = []  # (indent, description, general rate)
        heading = None
        for code, indent, desc, general, units in rows:
            digits = code_digits(code)
            if digits:
                heading = digits[:4]
            if heading is None:
                continue
            if indent == 0 and digits and len(digits) == 4:
                stack = []
            while stack and stack[-1][0] >= indent:
                stack.pop()
            path = [d for _, d, _ in stack] + [desc]
            # 10-digit statistical lines carry no rate; the rate is on the 8-digit line above them
            rate = general or next((g for _, _, g in reversed(stack) if g), "")
            stack.append((indent, desc, general))
            if heading not in self.heading_text:
                self.heading_text[heading] = desc
            self.heading_docs[heading].append(desc)
            if len(digits) >= 8:
                self.lines.append({"code": code, "heading": heading, "path": path, "general": rate, "units": units})
        # heading documents
        docs = {h: words(" ".join([self.heading_text[h]] * HEADING_WEIGHT + self.heading_docs[h])) for h in self.heading_text}
        self.idf = _idf(docs.values())
        self.vecs = {h: _vec(toks, self.idf) for h, toks in docs.items()}
        # line documents, with their own word weights and an inverted index
        line_toks = [words(" ".join(ln["path"])) for ln in self.lines]
        self.line_idf = _idf(line_toks)
        self.postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        self.lines_by_heading = defaultdict(list)
        for i, (ln, toks) in enumerate(zip(self.lines, line_toks, strict=True)):
            ln["vec"] = _vec(toks, self.line_idf)
            for t, w in ln["vec"].items():
                self.postings[t].append((i, w))
            self.lines_by_heading[ln["heading"]].append(i)

    @staticmethod
    def _cos(a: dict, b: dict) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(w * b.get(t, 0.0) for t, w in a.items())

    def suggest(self, query: str, k: int = 3, use_synonyms: bool = True) -> dict:
        toks, used = expand(query, use_synonyms)
        qh, ql = _vec(toks, self.idf), _vec(toks, self.line_idf)
        line_scores: dict[int, float] = defaultdict(float)
        for t, w in ql.items():
            for i, x in self.postings.get(t, ()):
                line_scores[i] += w * x
        best_line: dict[str, tuple[float, int]] = {}
        for i, sc in line_scores.items():
            h = self.lines[i]["heading"]
            if sc > best_line.get(h, (0.0, -1))[0]:
                best_line[h] = (sc, i)
        scores = {}
        for h, v in self.vecs.items():
            sc = BLEND * self._cos(qh, v) + (1 - BLEND) * best_line.get(h, (0.0, -1))[0]
            if sc > 0:
                scores[h] = sc
        top = sorted(scores, key=lambda h: (-scores[h], h))[:k]
        candidates = []
        for h in top:
            ls, i = best_line.get(h, (0.0, -1))
            ln = self.lines[i] if i >= 0 else None
            candidates.append({
                "heading": h, "heading_text": self.heading_text[h], "score": round(scores[h], 4),
                "line": None if ln is None else {"code": ln["code"], "path": ln["path"], "general": ln["general"],
                                                 "units": ln["units"], "score": round(ls, 4)},
            })
        s1 = candidates[0]["score"] if candidates else 0.0
        s2 = candidates[1]["score"] if len(candidates) > 1 else 0.0
        margin = (s1 - s2) / s1 if s1 else 0.0
        if not candidates:
            reason = "none of its words appear in the schedule"
        elif s1 < MIN_SCORE:
            reason = f"the best match is weak (score {s1:.2f}, needs {MIN_SCORE})"
        elif margin < MIN_MARGIN:
            reason = f"the top two headings are too close ({margin:.0%} apart, needs {MIN_MARGIN:.0%})"
        else:
            reason = None
        return {"query": query, "sure": reason is None, "reason": reason, "margin": round(margin, 4),
                "synonyms_used": used, "words": toks, "candidates": candidates}


def evaluate(schedule: Schedule, items: list[dict], use_synonyms: bool = True) -> dict:
    rows = []
    for it in items:
        r = schedule.suggest(it["product"], use_synonyms=use_synonyms)
        heads = [c["heading"] for c in r["candidates"]]
        rows.append({"product": it["product"], "expected": it["heading"],
                     "expected_text": schedule.heading_text.get(it["heading"], ""),
                     "got": heads[0] if heads else None, "top3": heads, "sure": r["sure"],
                     "right": bool(heads) and heads[0] == it["heading"], "in_top3": it["heading"] in heads})
    n = len(rows)
    sure = [r for r in rows if r["sure"]]
    return {
        "n": n,
        "top1": round(sum(r["right"] for r in rows) / n, 4),
        "top3": round(sum(r["in_top3"] for r in rows) / n, 4),
        "answered": round(len(sure) / n, 4),
        "right_when_sure": round(sum(r["right"] for r in sure) / len(sure), 4) if sure else None,
        "wrong_but_sure": sum(1 for r in sure if not r["right"]),
        "rows": rows,
    }
