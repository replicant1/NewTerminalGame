# COMPLETION — M0, DEV-A

**Run:** 6 · **Iteration:** M0, *the two hard things proved*
**Lane:** DEV-A · **Work items in this lane this iteration:** WI-5, and nothing else
**Mode:** non-local — real pull requests, merged by the developer

---

## What was finished

**WI-5 — The maze, generated.** Branch `r6/wi-5-maze-generated`, cut from
`main` at `1f6ea32`. Pull request **#24**, opened as a draft on the first
commit and merged by DEV-A once green.

| File | What it is |
| --- | --- |
| `terminal_game/domain/maze.py` | `Square`, `Direction`, `SquareKind` and the immutable `Maze` — the grid and the query surface WI-5 owns |
| `terminal_game/domain/maze_invariants.py` | MAZE-2, MAZE-3, MAZE-5 and MAZE-6 as predicates over a finished grid, each returning the squares at fault |
| `terminal_game/domain/maze_generator.py` | `generate_maze(random_source)` — carve a spanning tree, braid away every dead end, verify, and only then hand the maze out |
| `tests/domain/test_maze.py` | the maze value and every query on it |
| `tests/domain/test_maze_invariants.py` | each predicate against a sound maze and a hand-built maze that breaks it in one named way |
| `tests/domain/test_maze_generator.py` | the structural properties over 200 seeds, asserted against the query surface |
| `docs/findings/WI-5-specimen-grid-structure.md` | what the specimen picture's maze is actually made of, measured |
| `docs/prs/PR-WI-5-maze-generated.md` | the pull request's body |
| `docs/progress/r6-wi-5-maze-generated.md` | the progress log |

Requirements this item is responsible for: **MAZE-1** (shape),
**MAZE-2** (single-width, axis-aligned), **MAZE-3** (solid border),
**MAZE-4** (random, from a handed-in source), **MAZE-5** (no dead ends),
**MAZE-6** (fully connected). All six are asserted over 200 seeds.

## The state of the test suite as it was left

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 68 tests in 3.0s

OK
```

**68 passed, 0 failed, 0 skipped.** Every one of them is WI-5's; the tree had
no suite before this branch. No test in it opens a window, reads a clock, or
reaches for a global random source.

The post-merge confirmation — `main` brought onto the branch and the whole
suite run again — is recorded as a `MERGE` line and a `TEST` line in
`docs/progress/r6-wi-5-maze-generated.md`.

## Measurements worth carrying forward

In `docs/findings/WI-5-specimen-grid-structure.md`:

- the specimen picture's maze is **exactly** a 9 × 14 odd-coordinate cell
  grid — all 126 odd/odd squares corridor, all 190 even/even squares wall, in
  all 551 squares with no exceptions;
- every one of its 29 maze rows is **37 characters**, corroborating the plan's
  contradiction **C-1** independently;
- generated mazes hold **260 to 272 corridor squares, mean 265.5**, against
  the specimen's 264 — so **WI-6 should expect roughly 265 dots**;
- seeded generation is **identical across `PYTHONHASHSEED` values**, which
  WI-19's scripted game will depend on;
- WI-5's share of the suite is about 3 s, of which 0.78 s is the deliberate
  200-seed verification sweep.

## What the next items in this lane inherit

**WI-6 (the opening position)** has everything it needs:
`maze.corridor_squares()` in row-major order, `maze.is_corridor`, and
`Maze.from_text` for hand-built fixtures.

**The query surface is WI-5's, per section 10 of the plan.** DEV-B (WI-7) and
DEV-C (WI-8) were built for: `maze.ways_on(square)` returns the ways on keyed
by `Direction`, with `Direction.opposite` for "the way it came"; and
`maze.wall_neighbours(square)` returns the directions whose neighbour is a
wall, counting a neighbour off the grid as **not** a wall so that the border
corners resolve to `╔ ╗ ╚ ╝` unaided. If either needs a query that is not
there, ask DEV-A rather than adding one.

## Nothing is left open in this lane

No `ASK` was raised and nothing in WI-5 needs a human: the Domain layer needs
neither a clock nor a terminal, and no part of this work put a window on
anybody's screen.
