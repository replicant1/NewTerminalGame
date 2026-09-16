# M1 — DEV-C — completion record

**Developer:** DEV-C · **Iteration:** M1, *the pieces of the game* · **Run:** 6
**Mode:** non-local, real pull requests, developer merges their own.

DEV-C's M1 lane is **WI-8 (days 6–7)** and **WI-10 (day 8)**. **Both are
finished.** WI-10 landed last in the iteration, as the plan requires of it.

This record is written by the developer that took the lane over after M0. The
previous DEV-C completed WI-3 and WI-4 and ended; nothing of M1 had been
started when the lane changed hands, and nothing was lost.

Four pull requests, in this order:

| PR | Branch | What |
| --- | --- | --- |
| [#43](https://github.com/replicant1/NewTerminalGame/pull/43) | `r6/wi-8-wall-glyphs` | WI-8. Merged as `7374aeb`. |
| [#46](https://github.com/replicant1/NewTerminalGame/pull/46) | `r6/wi-8a-close-the-log` | WI-8's closing log lines, which describe #43's own merge and so could not ride on it. Merged as `f1bdade`. |
| [#52](https://github.com/replicant1/NewTerminalGame/pull/52) | `r6/wi-10-house-rules` | WI-10, and this document. |

---

## WI-8 — Wall glyphs · **DONE, MERGED**

| | |
| --- | --- |
| Branch | `r6/wi-8-wall-glyphs`, cut from `main` @ `6eb731e` |
| Pull request | [#43](https://github.com/replicant1/NewTerminalGame/pull/43) — **merged** as `7374aeb` |
| Commits | `db615a0`, `50add73`, `ecc73a2` |
| PR summary | `docs/prs/PR-WI-8-wall-glyphs.md` |
| Finding | `docs/findings/WI-8-glyph-census.md` |
| Progress log | `docs/progress/r6-wi-8-wall-glyphs.md` |

### What was built

`terminal_game/presentation/wall_glyphs.py` — SCRN-3 in one module. A pure
function from a wall square's four neighbours to the character it is drawn
as, the rule for the connector column, and the whole wall skeleton as frame
cells. All of it in `Colour.WALL_BLUE`. It names the Domain and its own frame
vocabulary and imports no toolkit.

### The table was measured, not remembered

The specimen picture was inverted back into a 19 × 29 grid of wall and
corridor and every wall square's glyph read off against the neighbours that
square actually has. **Fifteen of the sixteen combinations occur there and
all fifteen agree.** The sixteenth, the crossing, does not occur in the
specimen — and it occurs **61 times in 55 of the 200 shared seeds**, first at
seed 1, so the one reasoned entry is reachable in play rather than dead code.

### Announced for WI-12, and taken up

`wall_layer(maze)` and `wall_layer_text(maze)`, per first-lander rule 4.
`terminal_game/presentation/frame_composer.py` imports `wall_layer`, so the
frame composer names no wall character.

### Boundaries held

- **No query was added to the maze and DEV-A was not asked for one.**
  `Maze.wall_neighbours` already returned exactly the frozenset needed, and
  its own docstring says it was written for the border ring.
- **No ASCII-maze test helper was written.** `Maze.from_text`, also DEV-A's,
  already existed and is used by WI-6, WI-7 and WI-8 alike.
- **WI-8 declares neither the dot nor the actor motifs.** Pinned by a test
  that shows everything the module emits over forty generated mazes is a
  wall character or a blank, without naming either of the things it does not
  own.

---

## WI-10 — The rules of the house, enforced · **DONE**

| | |
| --- | --- |
| Branch | `r6/wi-10-house-rules`, cut from `main` @ `b7dd6ea`, merged up to `4c82efe` |
| Pull request | [#52](https://github.com/replicant1/NewTerminalGame/pull/52) |
| PR summary | `docs/prs/PR-WI-10-house-rules.md` |
| Progress log | `docs/progress/r6-wi-10-house-rules.md` |

### What was built

`tests/house_rules.py` — the inspector: **amendment 2's six rules**, each a
function returning a `Report(rule, inspected, violations)` that names the
file and the line. `tests/test_house_rules.py` — 41 tests running it over
this repository and over small planted trees.

Every check parses with `ast` rather than grepping, because
`grid_surface.py`'s own docstring lists the forbidden `create_*` names in
order to forbid them and a text scan would fail the file whose documentation
keeps the rule.

Rule 5 is built to amendment 2's corrected wording — it guards that no Tk
interpreter is ever **constructed**, not that the toolkit is never imported —
and there is a test asserting both halves at once: `tkinter` is in
`sys.modules` and the rule is still clean. No interpreter is created to check
it.

### Rule 6 was blocked, asked, and cleared without an escalation

`tools/walking_skeleton.py:208` imported `tests.specimen`. Amendment 2 had
already ruled the fixture must leave `tests/` and made the destination
DEV-B's call, so the question went to DEV-B on the record as a comment on PR
#45 rather than to a lead. DEV-B landed it as **PR #50**, moving it to
`terminal_game/presentation/specimen.py`. All six rules are now clean with
nothing exempted.

---

## Suite

From the repository root, every count on this exact command:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| Moment | Result |
| --- | --- |
| Baseline, `main` @ `6eb731e`, before WI-8 | **349 passed, 0 failed, 0 skipped** |
| WI-8's branch, before merging `main` | **392 passed, 0 failed, 0 skipped** |
| WI-8's branch, after merging `origin/main` `6cee5c9` | **417 passed, 0 failed, 0 skipped** |
| `main` @ `7374aeb`, WI-8 landed beside WI-13 | **445 passed, 0 failed, 0 skipped** |
| WI-10's branch, after merging `origin/main` `4c82efe` | **574 passed, 0 failed, 0 skipped** |

WI-8 added **43** tests and WI-10 added **41**.

**No Tk interpreter is created by any of them**, and rule 5 now enforces that
rather than leaving it to discipline.

---

## Windows opened in this lane during M1

**None.** WI-8 is pure Presentation and WI-10 is a tree inspector; neither
opens a window, imports a toolkit, or needs a real screen. Nothing to reap,
and no modal sheet was raised.

M0's eight windows were all reaped by the previous DEV-C. That record is
intact.

---

## What is open, and deliberately not closed here

**Whether the strokes of the blue double lines actually meet on screen.**

The spacing is settled by measurement — all 113 glyphs the picture uses share
one advance in Menlo at 14, 16, 18 and 20pt, with a control proving that is
Menlo's own coverage and not a fallback artefact. The characters will land in
the right places.

Whether the *ink* joins at the cell boundary is about glyph shapes, not
metrics, and **only an eye can settle it**. It is recorded as open in
`wall_glyphs.py`, in `tests/test_wall_glyphs.py`, in
`docs/prs/PR-WI-8-wall-glyphs.md` and in `docs/findings/WI-8-glyph-census.md`
§4, and **nowhere is it recorded as verified**. It belongs to WI-16.

---

## Deviations, both additive, both needing a ruling

1. **`wall_layer` / `wall_layer_text` in WI-8.** More than "a pure function
   from a wall square's four neighbours to the glyph" — that function plus
   the connector rule applied across a grid, both of which WI-8 owns, so that
   WI-12 need not re-derive the layout. Announced per rule 4 and taken up by
   WI-12.
2. **Rule 4's second half in WI-10.** As well as counting top-level packages,
   it reports any first-party import whose top-level name is a different
   top-level directory holding Python. The directory count alone can be
   dodged by a root spelled as a namespace package; the import half cannot.

Two smaller records, neither needing a ruling:

- Two tests were written for WI-8 and removed before merge for re-asserting
  behaviour `tests/test_maze.py` already owns.
- DEV-B's PR #50 changed one import line in `tests/test_wall_glyphs.py`,
  which is DEV-C's file. A mechanical conform to a ruling already made; noted
  only so the record is straight.

---

## No contradictions found

Neither item turned up a contradiction in the plan or the architecture. Two
things were checked specifically and found **correct**:

- Section 5's measured picture — 29 maze rows, every one 37 characters,
  square *c* at column 2c, odd columns connectors — matches the specimen
  exactly, confirmed by inverting the picture programmatically.
- Section 8's WI-10 entry carries **amendment 2's corrected six rules**, not
  amendment 1's wrong wording. The conductor asked for this to be checked and
  it holds; there is nothing to take back to the lead.
