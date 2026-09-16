# M3 — DEV-C — completion record

**Developer:** DEV-C · **Iteration:** M3 · **Run:** 6
**Mode:** non-local, real pull requests, developer merges their own.

DEV-C's M3 lane was **WI-17 (days 12–13)**. **WI-17 moved to DEV-A in
amendment 4** and landed there, and **WI-20a moved forward into M3 by the
same amendment**. So this lane's M3 is **WI-20a alone**.

Amendment 4 kept WI-20a out of DEV-A's lane deliberately: DEV-A wrote WI-5,
WI-6, WI-11, WI-13 and WI-15 — the whole Domain and Application layer — and
*a sweep is worth least when the author checks their own coverage and most
when a fresh reader asks whether a requirement really has a test pinning it.*
This record is written from that side of the boundary.

| PR | Branch | What |
| --- | --- | --- |
| [#60](https://github.com/replicant1/NewTerminalGame/pull/60) | `r6/wi-20a-spec-sweep` | WI-20a, this record, and WI-14's closing log lines. |

---

## WI-20a — The specification sweep, first landing · **DONE**

| | |
| --- | --- |
| Branch | `r6/wi-20a-spec-sweep`, cut from `main` @ `46101e4`, merged up to `c9c3623` |
| Pull request | [#60](https://github.com/replicant1/NewTerminalGame/pull/60) |
| PR summary | `docs/prs/PR-WI-20a-spec-sweep.md` |
| The sweep | `docs/TRACEABILITY.md` |
| Progress log | `docs/progress/r6-wi-20a-spec-sweep.md` |

### What was built

- **`docs/TRACEABILITY.md`** — all 49 requirement codes, each traced to the
  named test that pins it or the named human check that must look at it.
- **`tests/test_spec_sweep.py`** — 21 tests keeping it true.

### The result

**Nothing in this tree is a requirement ticked without evidence.** All 49
rows name something: 35 pinned outright, 8 pinned under a named assumption,
1 pinned as formatting only, 2 with a half needing a human, 2 with a half
awaiting WI-18, **0 with nothing at all**.

Four rows carry evidence stronger than a test, because somebody ran the real
thing: WIN-3, SCRN-2, CTRL-3 and CTRL-4.

### Where the sweep lives, and why it was asked rather than decided

The four prescribed document paths are all **per-something** — per work
item, per lane, per branch, per measurement. A specification sweep is per
nothing; it is about the whole project, and whole-project documents already
had a home beside `FUNCTIONAL_REQUIREMENTS.md` and `ARCHITECTURE.md`.

`developer.md` says to ask rather than invent a fifth path, so it was asked.
**Amendment 8 answered: `docs/TRACEABILITY.md`, no work-item code in the
name, one file written twice with WI-20b completing it in place.** This
branch implements that.

---

## The four things the tests catch that a reader would not

1. Every code appears **exactly once**; the sweep invents none.
2. **Every test it names still exists** — file, class, method, and the
   method must be named `test_*`.
3. **Every document it cites is on disk.**
4. **While any row says "not yet", the incompleteness notice must be there.**

**Check 3 found a bad citation in the document on its first run** — the
WI-21 answers, cited before they exist. The convention is now stated in the
sweep: a backtick is a claim that the thing exists.

Check 4 exists because the sweep lands twice into one file, and a reader who
does not know it is unfinished takes an unfinished row for a covered one.
That is the one way a traceability document can actively mislead rather than
merely be unhelpful.

---

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| Moment | Result |
| --- | --- |
| `main` @ `46101e4`, before WI-20a | **661 passed, 0 failed, 0 skipped** |
| after merging `origin/main` `c9c3623` (WI-19) | **693 passed, 0 failed, 0 skipped** |
| `r6/wi-20a-spec-sweep`, complete | **714 passed, 0 failed, 0 skipped** |

21 new. **All six of WI-10's house rules clean.**

---

## Windows opened in this lane during M3

**Zero.** WI-20a reads files and writes a document.

**DEV-C's count for the whole run — WI-8, WI-10, WI-14, WI-20a — is zero.**
The one item that touched the real toolkit, WI-14's probe, withdrew its root
before anything could be mapped and never entered an event loop. The project
ledger stands at 21 opened, 21 reaped, no modal sheet ever raised, and none
of those 21 were this lane's.

---

## Deviations

**None needing a ruling.** The one open question was asked rather than
decided and amendment 8 answered it.

Two additive things, both beyond the plan's test list, both flagged in the
PR body: the **citation checker** (every named test and document must
exist), and the **incompleteness-notice test**. The first earned its place
by finding a bad citation in its first run.

---

## What is open, and is not closed by this lane

All recorded in `docs/TRACEABILITY.md` as **open, not met**:

- **A1** — the titlebar, to a person's eye.
- **A2 revised** — the pointer as the anchor. Approved by the lead; still
  the user's to overturn.
- **A3** — WIN-5 against END-5 and END-6.
- **A4** — Menlo 16pt in a 400 × 570 window.
- **A7** — the status-line literals.
- **A8** — the dot under the player on the losing turn.
- **A10** — do the blue walls' strokes actually meet? **Ask it against
  WI-16's joinery view, not a game screen**: the specimen picture contains
  no crossing glyph at all, so a game may never show the asker one.
- **The ghost's start-corner tie-break** — breaks no requirement; gives 200
  distinct mazes only two opening positions.
- **C-7** — WIN-4 falls back for a reason no permission would clear.
