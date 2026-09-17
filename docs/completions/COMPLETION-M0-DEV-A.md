# M0 — developer A — completion record

**Iteration:** M0, *Ground to stand on*.
**Lane:** A. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-ad9b18e196f2c349f`.
**Recorded** 17 Sep 2026, 01:42Z.

## What was finished

**Both of lane A's M0 items: S-1 (toolkit feasibility) and WI-3 (wall glyph resolution).**
M0 lane A is complete.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#72](https://github.com/replicant1/NewTerminalGame/pull/72) | S-1: toolkit feasibility — Tk 8.5 is testable headlessly; Menlo 16 is the cell grid | `main` | `5c1d54c` |
| [#75](https://github.com/replicant1/NewTerminalGame/pull/75) | S-1: progress log tail — merge record and post-merge suite count | `main` | `c76bc37` |
| [#77](https://github.com/replicant1/NewTerminalGame/pull/77) | S-1: M0 lane A completion record | `main` | `d033ff4` |
| [#80](https://github.com/replicant1/NewTerminalGame/pull/80) | WI-3: wall glyph resolution | `main` | `ead97a7` |

All merged by me. Branches `r7/s-1-tk-feasibility` (cut from `main` at `4015c96`) and
`r7/wi-3-wall-glyphs` (cut from `main` at `d033ff4`). Neither was stacked on anything.

**Files added by S-1:**

- `docs/findings/S-1-tk-headless.md` — the verdict and every number behind it.
- `docs/prs/PR-S-1-tk-feasibility.md`, `docs/prs/PR-S-1-progress-log-tail.md`.
- `docs/progress/r7-s-1-tk-feasibility.md`.

**Files added by WI-3:**

- `terminal_game/presentation/wall_glyphs.py` — `wall_glyph(north, south, east, west)`,
  the twelve glyph constants, and all sixteen cases written out as an explicit table.
- `tests/test_wall_glyphs.py` — 25 tests.
- `docs/prs/PR-WI-3-wall-glyphs.md`, `docs/progress/r7-wi-3-wall-glyphs.md`.

## S-1's verdict

> **Yes — the Presentation layer can be tested headlessly on Tcl/Tk 8.5.**
> **Assumption P8 holds in both halves.** WI-5, WI-6, WI-7, WI-14 and WI-16 proceed as
> written, and **human item 5 of section 9 does not open.** Nothing was installed.

**Recommended:** **Menlo, size 16 — cell 10 × 19 px, so a 40 × 30 window is 400 × 570 px.**
16 is the largest Menlo size at which a 40-column row laid out per cell and the same row
drawn as one string land on identical pixels, which is why it is the recommendation.

## WI-3's result

Fifteen of the sixteen neighbour combinations were **measured** by parsing the specimen
picture square by square, not recalled. Each occurs with exactly one glyph across all
19 × 29 squares, so SCRN-3 really is a function of four booleans. Two things the picture
settled that are easy to guess wrong: **a single wall neighbour draws the full line, not a
stub** (37 squares, no exceptions), and **outside the grid is not a wall** (the border
corners prove it). The sixteenth case — the crossing `╬` — does not occur in the specimen,
is derived, and is labelled as derived in the code and in a test that asserts exactly which
case is missing.

## State of the test suite as I left it

```
.venv/bin/python -m pytest -q      # from the repository root
81 passed in 0.08s
```

**81 passed, 0 failed, 0 skipped, nothing deselected**, on `r7/wi-3-wall-glyphs` at
`ead97a7`, which is `origin/main`. **WI-3 added 25 of them; S-1 added none** — see the
deviation below.

At the moment PR #72 merged the count was **0 passed, 0 failed, 0 skipped**, because no
suite existed: WI-0 had not landed and `.venv/bin/python` did not exist. It was 56 by the
time PR #77 merged and 81 by PR #80.

## Deviations needing a ruling

**S-1 committed no test, although its bar in plan section 5 says one should exist if the
conclusions can be pinned headlessly — and they can.** WI-0 was creating the package layout
in parallel; a test written here would have guessed at it and raced it. **The conductor
ruled it be left to WI-5.** The four assertions WI-5 should write, including the control
that stops the substitution check passing vacuously, are set out in section 7 of the
finding.

**WI-3 exports `ALL_WALL_GLYPHS`, which nothing in its brief asks for** (additive). It is
the twelve-character alphabet the resolver can return; WI-5's font check needs exactly that
set, and WI-3's own specimen test uses it to prove the wall/corridor partition.

## Contradiction found in the plan

**SCRN-3's colour has no owner.** Section 4 traces SCRN-3 to WI-3 alone, and SCRN-3 calls
the walls *blue*. But WI-3's own "tests must establish" clause asks only about glyphs, and
section 7 gives WI-4 the whole field of **glyph-and-colour**. WI-3 therefore ships glyphs
and names no colour, leaving the blue half of SCRN-3 unrealised by the item the trace table
points at. Either the trace row becomes `SCRN-3 | WI-3 (glyph) + WI-4 (colour)`, or WI-3 is
meant to export a wall-colour token. Not guessed at; PR #80's body has the full argument.

## Two things for a human

1. **A "Python" tile appears in the Dock whenever a Tk root is built**, including in a
   headless test run. Not a window, never takes focus, but visible and nobody agreed to it.
   Steps and what a good answer looks like are in section 5 of the finding.
2. **Whether Menlo's box-drawing ink spans the full cell** — so a run of `═` reads as one
   unbroken double line — could not be measured. Only *advance* was measurable. The first
   chance to see it is WI-7's window; WI-17 should put it in front of a person.

## Window hygiene

No Terminal window was opened, so none needed reaping. No window was ever mapped. Every
S-1 probe carried a `SIGALRM` hard deadline, contained no `mainloop`, and could not block.
No permission dialog was raised; `/usr/bin/lsappinfo`, which needs none, was the only thing
that touched the desktop. WI-3 is a pure function over four booleans and touches nothing.

**The later ruling against reaching Objective-C, AppKit, Quartz or CoreGraphics through
`ctypes` was never in play here** — S-1 found no PyObjC on the interpreter and used the
shipped `lsappinfo` command instead, and WI-3 imports nothing but `typing`.
