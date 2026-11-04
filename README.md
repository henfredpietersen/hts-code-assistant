# hts-code-assistant

Type a product the way a shop would list it ("Portable Bluetooth speaker") and this suggests where it sits in the US tariff schedule: the 4-digit heading, the best 10-digit line under it, the schedule's own wording and the base duty rate. When the top two candidates are too close to call, it says it isn't sure and shows them instead of picking one.

**Try it live:** https://outview.co.za/case-study-hts-assistant/ (runs in your browser)

Built AI-assisted under my direction. I chose the data, the test design and the hand-over rule. Claude generated the code, and I reviewed it, ran it and checked the tests. I didn't hand-write it.

## How well it does

Two sets of everyday products, each labelled with its correct 4-digit heading:

| | Right first | In top three | Says it's sure | Right when sure | Right first, no synonyms |
|---|---:|---:|---:|---:|---:|
| Development set (65) | 83.1% | 93.8% | 70.8% | 95.7% | 66.2% |
| **Test set (41), held out** | **70.7%** | **82.9%** | **70.7%** | **79.3%** | 70.7% |

The test set is the honest number. I wrote the development set first, then looked at it while writing the synonym list and choosing the settings, so it flatters the assistant. The test set was written and committed *before* the synonym list (Git history shows the order, and a test checks it), and it was scored once.

Two things the gap shows:

- **Tuning on what you've seen inflates the score.** When it says it's sure, it's right 95.7% of the time on the development set, but 79.3% on the test set: wrong but sure on 6 of the 29 test products it answered.
- **The synonym list mostly helped the products it was written for.** Mapping everyday words to the schedule's words ("laptop" → "automatic data processing machines") lifted the development set from 66.2% to 83.1%, and made no difference on the test set (70.7% either way). It also cut both ways: "car" pulled "Child car seat" toward motor vehicles.

Every test-set mistake is listed on the demo page.

## How it works

1. **The schedule.** `scripts/make_snapshot.py` downloads every chapter (01–97) of the current Harmonized Tariff Schedule from the US International Trade Commission's export: 1,228 headings and 23,193 tariff lines at 8 or 10 digits. Chapters 98 and 99 (special provisions and temporary measures) are left out because they aren't product descriptions.
2. **Two kinds of search document.** Each heading (its text counted three times, plus every line under it), and each 8- or 10-digit line with its full path ("Footwear › Other footwear › With uppers of textile materials › …").
3. **Scoring.** TF-IDF word matching with plurals folded. A heading's score is 0.3 × its heading-document match plus 0.7 × its best line's match. That blend was picked on the development set (`scripts/tune.py`).
4. **Synonyms.** `hts/synonyms.py` adds the schedule's words to everyday ones. The page says which were used for each query.
5. **Not sure.** If the top heading isn't at least 15% ahead of the runner-up, it won't pick one. That threshold was also picked on the development set.

No language model. It matches wording, so it can't ask the questions that often decide a code, like what the product is made of.

## What this isn't

- **Not a classification.** A binding US classification comes from CBP or a licensed customs broker.
- **The labels are mine.** I labelled both sets at heading level from the schedule's heading text, for common products whose heading isn't in doubt. They aren't customs rulings: CBP's rulings database (CROSS) doesn't allow automated access, so I didn't use it.
- **The duty rate is the base "General" rate only.** It leaves out additional duties under chapter 99, such as Section 301 or Section 232 measures, which can be much higher and change often.

## Run it

```bash
python -m pytest -q                     # 12 tests, standard library + pytest
python scripts/tune.py                  # how the settings were picked (development set only)
python web/build.py                     # rebuild docs/demo.js after changing hts/ or web/
python -m http.server -d . 8000         # then open http://localhost:8000/docs/demo.html
```

The workflow `.github/workflows/snapshot.yml` rebuilds `data/hts.json` from the USITC on GitHub's servers. The snapshot records which schedule revision it holds.

## What was tested

- `tests/test_model.py`: on a tiny hand-made schedule, plurals fold, synonyms add schedule words and are reported, uncoded group lines stay in the path, the right heading and line come back, and it says it's not sure when nothing matches or the top two are close.
- `tests/test_snapshot_and_page.py`: every label is a real heading, the sets don't overlap, the test set was committed before the synonym list, the synonym list doesn't target test products, a fresh run reproduces every number in this README, the published page embeds the current code, and the page's calls work.
- I also ran the page's code under Pyodide 0.26.4 (the version the page loads) and got the same scores.

CI runs lint, the tests and the page drift check on every push.

MIT licence. Data: U.S. International Trade Commission, Harmonized Tariff Schedule (public).
