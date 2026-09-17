# WI-12b — row 29 as cells

Closes a gap between two **already-merged** modules that nothing was going to catch until
WI-14 tripped over it. Found while reading ahead for WI-16; dispatched as its own small
landing because **WI-14 needs it and WI-14 comes before WI-16**.

## The gap

`frame.compose_frame` takes `status_row: Sequence[Cell]` of **exactly 40**.
`status.status_text` returns a **`str`**. **Nothing bridges them.**

So WI-14 would have had to pad row 29 out to 40 itself — and padding row 29 **is** composing
part of row 29, which is the one thing the lead ruled must happen nowhere but WI-12:

> The content of row 29 is decided in exactly one place, and that place is WI-12. No part
> of row 29's text may be composed anywhere else.

Neither module is wrong on its own. The gap only exists between them, which is why both
merged green.

## The fix

Two functions in `terminal_game/presentation/status.py`, WI-12's own module:

| | |
|---|---|
| `status_cells(outcome, score)` | the same row as `status_text`, as exactly `COLUMNS` cells — the text in `STATUS_COLOUR`, then blanks |
| `cells_for(state)` | the same, from a game state, asking `turn.outcome_of` for the reason `status_for` does |

**No lane A code is touched.** It works with `compose_frame` exactly as it stands today, so
WI-14 is unblocked without anyone changing anything, and it leaves the text-and-colour
signature open if lane A later prefers it. `status_text` remains the primary answer; this is
a shape-adaptor so its caller does not write the padding.

**The padding lives here on purpose.** A row that stopped short would leave the tail of row
29 showing whatever was under it, so something has to decide how the row ends — and
STAT-1's *"and nothing else"* makes that a statement about row 29's content.

## What the tests establish

11 new tests, and one of them is the join WI-14 will actually make:

- the row is exactly `COLUMNS` cells, for every form and at score 0, 37, 274 and 551;
- the cells read back as exactly `status_text(...)` padded to the width;
- **every cell is cyan, including the padding** — a row of two colours would be a row
  composed by two decisions;
- the padding is blank;
- **the row goes through `compose_frame` unaltered** — `compose_frame` says it "does not
  read them and owns nothing of their content", and this asserts that what comes out is
  what WI-12 decided;
- `cells_for` follows `outcome_of`, not the stored field, pinned on a board with both
  actors on one square and the field left at `UNDECIDED`.

## Suite state

```
.venv/bin/python -m pytest -q          →  799 passed, 0 failed, 0 skipped, 2 deselected
```

Repository root, `.venv` from `/usr/bin/python3` 3.9.6, pytest 8.4.2. Baseline on `main` at
`54a32cf` was **788**; WI-12b adds **11**. Layer rule: no violations. No window opened;
`lsappinfo visibleApplicationCount` 7 throughout; **crash reports still 14, none new**.

## Also carried on this branch

`docs/progress/r7-wi-12-status-line.md` — WI-12's `MERGE` and `DONE` lines, which could only
be written after #93 landed, carried forward per the log-tail ruling rather than costing a
PR of their own.

`docs/progress/r7-wi-16-end-to-end.md` — the reading-ahead notes that produced this item, and
two findings that are not mine to fix: **`Session.__repr__` reads the stale `GameState.outcome`
field** that the rest of WI-11 is careful never to read (raised on PR #91, lane A's to take),
and a trap for my own WI-16 — on a maze with few junctions the ghost never consults the
random source at all, so seeds 7 and 8 gave an identical walk.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
