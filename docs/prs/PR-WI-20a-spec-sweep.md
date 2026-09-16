# WI-20a — The specification sweep, first landing

**The sweep is `docs/TRACEABILITY.md`** — beside the specification, the
architecture and the plan, not under one of the four per-something
directories, and with **no work-item code in its name**. Amendment 8 settled
that. **One file, written twice**: this landing creates it and WI-20b
completes it in place.

**Branch:** `r6/wi-20a-spec-sweep`, based on `main` at `46101e4`, merged up
to `c9c3623` (WI-19). **Developer:** DEV-C. **Depends on:** WI-15, landed.

---

## The headline

**Nothing in this tree is a requirement ticked without evidence.** All 49
rows name something.

| | |
| --- | --- |
| Pinned outright | **35** |
| Pinned under a named assumption | **8** |
| Pinned as formatting only | **1** — STAT-3 (A7, A9) |
| Half pinned, half needing a human | **2** — SCRN-3 (A10), SCRN-7 |
| Half pinned, half awaiting **WI-18** | **2** — GAME-1, START-5 |
| **With no test and no named human check at all** | **0** |
| Additionally **observed on a real screen** | **4** — WIN-3, SCRN-2, CTRL-3, CTRL-4 |

Read as an outsider, which amendment 4 says is the point of keeping this out
of the lane that wrote the Domain. The question asked of every row was not
*"is there a test somewhere near this"* but **"which named test fails if
this requirement stops being true?"** Where the answer was "none", the row
says so.

---

## What the sweep is checked by, and what that caught

`tests/test_spec_sweep.py`, 21 tests, checking **four different things**:

1. **Every requirement code appears in the sweep, exactly once** — the check
   the plan asks for.
2. **The sweep invents no code** the specification does not have.
3. **Every test the sweep names exists** — the file, the class, the method,
   and the method must be named `test_*`. A citation is a promise that
   something is pinned; a renamed test turns that promise into a lie without
   anybody noticing.
4. **Every document the sweep cites exists.** WI-20b's list asks for this
   and it costs nothing to have from the first landing.

None can pass over an empty set: each asserts a floor first.

**Check 4 found a defect in my own document on its first run.** I had cited
`docs/findings/WI-21-human-answers.md`, which does not exist — a forward
instruction to WI-20b that read as a claim. Fixed, and the convention is now
stated in the document itself: **a backtick is a claim that the thing
exists**, and a file that does not exist yet is named in plain text.

### And one test for the way this document could actively mislead

The sweep lands twice into the same file, so between the landings it is
deliberately incomplete. A reader who does not know that takes an unfinished
row for a covered one — which is worse than no document, because the point
of the thing is to be trusted.

So the file opens with a notice saying **which landing it is and what is not
yet covered**, and `AnIncompleteSweepSaysSo` enforces the pairing: **while
any row says "not yet", the notice must be there.** The second landing
removes the rows and the notice together, and this is what stops one going
without the other. It does not demand the notice be removed — deciding the
sweep is finished is a person's call.

---

## Three things recorded as open rather than ticked

A traceability document turning an open question into a tick is the exact
failure this item exists to prevent.

**1. A10 — do the wall strokes actually meet?** The spacing is settled: all
113 glyphs share one advance in Menlo at four sizes, with a control. **Equal
advance proves the cells line up; it does not prove the strokes touch.**
Four developers each declined to convert one into the other; this sweep is
the fifth reader to decline.

And a sting it carries forward: **the specimen picture contains no crossing
glyph at all** — measured across the whole picture in
`docs/findings/WI-8-glyph-census.md`, which found 15 of 16 combinations
there and not the crossing. So checking SCRN-3 against the specimen, or
against a game screen, **may never put a crossing in front of anybody**.
WI-16's joinery view is the only thing that has ever rendered one. Crossings
are not rare in play: 61 across the 200 shared seeds, in 55 of those mazes.

**2. C-7 — WIN-4 falls back for a reason no permission would clear.** The
row records it as *satisfied by fallback, with a known cause*, not as a gap,
and says plainly that granting Accessibility would change nothing.

**3. The ghost's start-corner tie-break.** START-2 is pinned and holds. But
the furthest square is always a corner, all four corners are always
corridor, and the tie is broken deterministically — so **the ghost always
starts in the left-hand column, and 200 distinct mazes gave two distinct
opening positions** (`docs/findings/WI-6-start-squares.md`). Nothing in the
specification is broken. It is in the sweep because a reader who only asked
*"is START-2 pinned?"* would have missed it, and a player sees it in three
games.

---

## A9 / C-6 honoured, and checked rather than assumed

**No row claims 274 as an achieved score.** Every use of 274 in the tree was
inspected: it is an input to the formatter, and `terminal_game/presentation/status_line.py`
and `tests/test_status_line.py` both say in as many words that it is not
reachable. WI-19 pinned the negative directly —
`tests/test_scripted_game.py::AWholeSeededGame::test_the_score_is_not_the_number_in_the_specifications_example`.
There is also a test in this branch asserting the sweep does not claim it.

---

## Findings

1. **Two requirement codes are named nowhere in the suite — GAME-1 and
   SCRN-1.** Both turn out to be pinned, by tests that do not cite them. No
   code change is needed; it is recorded because it shows why a sweep must
   read the tests rather than grep for codes, and because anyone maintaining
   those two has no way to find their tests by searching.
2. **WIN-4's real obstacle is not A2** — C-7, above.
3. **Two requirements are half-pinned because WI-18 has not landed.** Listed,
   not ticked.
4. **START-2 holds and a player would still notice something** — the
   tie-break, above.
5. **Nothing is ticked without evidence.**
6. **Four rows have evidence stronger than a test**, all from real-medium
   exercises the plan only began demanding after amendment 2.

---

## Proved by a double is not proved — what was exercised against the real thing

**Nothing, and nothing here needs to be.** This item reads files and writes
a document; it touches no Shell code, opens no window and uses no double.

It does, though, **cite four things other people exercised against the real
toolkit** rather than re-deriving them, which is what
`docs/findings/` is for: SCRN-2 observed as `["text"]` across eight real
windows, WIN-3's title read back eight times, CTRL-3 observed on a real
screen with the four squares matching the pure Domain's prediction for that
seed, and CTRL-4's real `q` ending a real session at 1.483 s.

**Windows opened by this item: zero.**

---

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
714 passed, 0 failed, 0 skipped
```

693 on `main` after WI-19, so 21 new. **All six of WI-10's house rules are
clean** over the tree with this branch on it.

---

## Deviations needing a ruling

**None outstanding.** The one open question — where a traceability document
lives — was asked rather than decided, and amendment 8 answered it as
`docs/TRACEABILITY.md`. This branch implements that answer.

Two additive things, both beyond what the plan's test list asks for, and
both flagged:

1. **The citation checker** (checks 3 and 4 above). The plan asks only for
   the completeness check. This adds "every test and document named still
   exists", which is what stops the document rotting between the landings —
   and it earned its place by finding a bad citation in its first run.
2. **The incompleteness-notice test.** Also additive, and aimed at the one
   way this document can mislead rather than merely be unhelpful.

---

## Also on this branch

The closing lines of `docs/progress/r6-wi-14-anchor.md`, which record PR
#54's own merge and so could not ride on it.

---

## What needs a human

Unchanged by this item, and all recorded in the sweep as **open, not met**:
**A1** (titlebar), **A2 revised** (approved, still the user's to overturn),
**A3** (WIN-5 against END-5/END-6), **A4** (type size), **A7** (status-line
literals), **A8** (the dot on the losing turn), **A10** (the strokes), and
the ghost's start-corner tie-break.

**A10 should be asked against WI-16's joinery view, not a game screen** — a
game may never render a crossing.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
