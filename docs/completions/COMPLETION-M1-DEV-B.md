# Lane B, iteration M1 — completion record

Lane B's M1 was **WI-2**, and that is all of it: WI-8 was moved out of M1 and
into M2 when it was reassigned from lane C to lane B, so that one developer
owns WI-8 and WI-10 and the seam between them disappears rather than being
managed. WI-8 is recorded in `COMPLETION-M2-DEV-B.md`.

---

## WI-2 — maze generation

| | |
|---|---|
| Branch | `r7/wi-2-maze-generation`, cut from `main` at `ddc250e` |
| Head of branch | `942f2d3` |
| Pull request | [#85](https://github.com/replicant1/NewTerminalGame/pull/85) — opened as a draft, marked ready, merged by developer B |
| Merged to `main` as | `589902d` |
| PR summary | `docs/prs/PR-WI-2-maze-generation.md` |
| Progress log | `docs/progress/r7-wi-2-maze-generation.md` |
| Finding | `docs/findings/WI-2-odd-cell-lattice.md` |

### What it delivers

`terminal_game/domain/generation.py` — a fresh maze per run from an injected
random source, satisfying MAZE-2 through MAZE-6.

### The state of the test suite as it was left

```
.venv/bin/python -m pytest -q
```

**235 passed, 0 failed, 0 skipped** after merging `main` down, and the same
again after PR #85 landed. 43 of those were new here.

The suite time rose from 0.13 s to 2.28 s, and about 1.8 s of that is the
200-seed sweep. `SEEDS` is a named constant at the top of
`tests/test_generation.py` if that ever needs revisiting.

### The thing worth carrying forward

**Caution C4 — the biggest algorithmic risk on the board — did not bite, and
the reason is structural.** Carving on a lattice of cells at odd coordinates
makes two of the four requirements impossible rather than repaired:

* **MAZE-2**: every 2 x 2 block contains a square whose column and row are
  both even, and no carveable square is both-even. A corridor two squares
  wide is unrepresentable.
* **MAZE-3**: cells occupy columns 1-17 and rows 1-27, connectors lie strictly
  between them, so nothing carveable reaches the border ring.

Both are asserted exhaustively over the whole lattice rather than sampled.
The remaining repair pass converges in one go because adding an edge only
raises degrees, so it never creates the fault it removes and never
disconnects what the carve joined.

Measured over 500 seeds: **0 unsound, 0 with a 2 x 2 corridor block, 500
distinct mazes, 3.16 ms each.**

### The parity trap this uncovered, which WI-8 then had to build against

The grid centre `(9, 14)` has an **even row**, so on the carving lattice it is
a connector rather than a cell and is carved only when that wall happens to be
opened — **corridor in 109 of 200 seeds**. The always-corridor squares nearest
the middle are `(9, 13)` and `(9, 15)`, both 200 of 200.

I got this wrong in the first draft of the finding and caught it by checking
my own arithmetic against the generator. It went on to become the load-bearing
constraint on START-1: an implementation assuming the centre is walkable
passes a single-seed test and fails on nearly half of real games.
