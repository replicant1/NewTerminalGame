# WI-1 — The shared value vocabulary and the maze generator

**Branch** `wi-1-vocabulary-maze` · **Base** `main` · **Iteration** M0 · **Dev A**

Lands GAME-1, GAME-3 (by absence), MAZE-1, MAZE-2, MAZE-3, MAZE-4, MAZE-5,
MAZE-6.

## What this adds

| File | What it is |
|---|---|
| `termgame/__init__.py` | package docstring stating the pure/impure rule |
| `termgame/model.py` | the frozen value types — `Position`, `Direction`, `Outcome`, `Maze`, `GameState`, and the picture (`Frame`, `FrameBuilder`) |
| `termgame/maze.py` | `generate(rng)`, the text-grid loader, and the MAZE-1..6 invariant checks |
| `tests/test_model.py` | the value types, immutability, GAME-3 by absence, the picture |
| `tests/test_maze.py` | 1000-seed invariants, determinism, the loader, the neighbour query, the spec fixture |
| `tests/test_purity.py` | every pure module imports with `curses` and `subprocess` unavailable |
| `tests/fixtures/spec_maze.txt` | the mock-up from the specification, 29 rows × 37 columns |

## The two obligations the plan singled out

**The corridor / open-neighbour query ships now.** `Maze` answers, for any
cell, whether it is corridor and which of its four neighbours are:

```
maze.is_corridor(pos)          -> bool    (False off the grid, so no caller needs a bounds check)
maze.is_wall(pos)              -> bool
maze.open_directions(pos)      -> Tuple[Direction, ...]   in DIRECTIONS order
maze.open_neighbours(pos)      -> Tuple[Position, ...]
maze.corridor_degree(pos)      -> int
maze.is_open(pos, direction)   -> bool
maze.corridors()               -> FrozenSet[Position]
```

`open_directions` returns them in the fixed `DIRECTIONS` order
(`UP, DOWN, LEFT, RIGHT`), so a seeded `rng.choice` over the result is
reproducible — WI-7's ghost policy depends on that. The lookup is derived once
at construction, so the query is a dictionary hit, not a recount. Neither WI-6
nor WI-7 needs to introduce anything shared.

**The picture type ships now, empty.** `Frame` is an immutable grid of
`Cell(char, style)` carrying **style identifiers, not curses attributes**, and
reads back as plain strings:

```
Frame.rows()   -> Tuple[str, ...]     30 strings of 40 characters
Frame.styles() -> Tuple[Tuple[str, ...], ...]
Frame.cell/char_at/style_at(row, col)
Frame.text()   -> one newline-joined block
```

`FrameBuilder(height, width, char, style)` with `.put`, `.put_text` and
`.build()` is the scratch pad WI-3 fills; it is mutable on purpose and is
meant to live inside one pure function. Style identifiers are plain strings;
`model.py` defines only `STYLE_DEFAULT`, so `theme.py` (WI-3) owns the rest of
the vocabulary without ever editing this module.

## The maze

A braided randomised depth-first search over the 9 × 14 node lattice, exactly
as architecture §5.2 reasons:

1. randomised DFS → a spanning tree (MAZE-6 holds: connected);
2. one braid pass in node order giving every degree-1 node one more edge to a
   uniformly-chosen lattice neighbour it is not already joined to (MAZE-5);
3. painted onto the 29 × 19 cell grid.

**One pass is provably enough**, which is why there is no loop: a node's degree
never falls, so after the pass has visited every node in order, every node has
degree ≥ 2. The architecture measured "max braid passes ever needed: 1"; this
is the reason.

MAZE-2 falls out of the lattice rather than being checked for: every 2 × 2
block of cells straddles both parities on both axes, so it always contains
exactly one `(even, even)` pillar, which is always wall. MAZE-3 likewise: row
0, row 28, column 0 and column 18 are never nodes, and never links with a node
on both sides.

## Measurements

| | |
|---|---|
| 1000 seeds, all invariants | **0 failures** |
| generating 1000 mazes | **0.767 s** (0.77 ms each; architecture §7 measured 0.642 ms) |
| checking 1000 mazes (border, dead ends, 2×2, flood fill) | **0.938 s** |
| mean corridors per maze | **265.4** (architecture §7 measured 265.3) |
| the spec's mock-up decoded | **264 corridors** = 126 nodes + 138 links, `check()` returns `()` (architecture §7: 264, 0 dead ends, all reachable) |
| the joiner-column invariant (architecture C9) in the mock-up | holds on all 29 rows × 18 joiner columns |

## Suite

The whole suite, from the root of the worktree:

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 96 tests in 2.819s

OK
```

Cross-checked on the other interpreter, which is not the gate:

```
$ /opt/homebrew/bin/python3 -m unittest discover -s tests
Ran 96 tests in 1.724s

OK
```

There is no `tests/__init__.py` and no nested test module; all three test
files sit flat in `tests/`, and `tests/fixtures/` holds one data file.

**Mutation checks:** not applicable — not part of this workflow.

## Each thing the plan said the tests must establish, and where it is

| The plan's bullet | Test |
|---|---|
| solid border over 1000 seeds (MAZE-3) | `test_maze.TestGeneratedMazeInvariants.test_every_maze_has_a_solid_wall_border` |
| no corridor cell with fewer than two corridor neighbours (MAZE-5) | `…test_no_corridor_square_has_fewer_than_two_ways_on` |
| all corridors mutually reachable by flood fill (MAZE-6) | `…test_every_corridor_square_is_reachable_from_every_other` |
| no 2 × 2 block of corridor (MAZE-2) | `…test_no_maze_has_a_two_by_two_block_of_corridor` |
| 29 × 19 (MAZE-1) | `…test_every_maze_is_twenty_nine_by_nineteen` |
| two seeds, two mazes (MAZE-4) | `TestRandomness.test_two_different_seeds_produce_two_different_mazes`, and `…test_a_thousand_seeds_produce_hundreds_of_distinct_mazes` (200 seeds, 200 distinct) |
| the same seed twice | `TestRandomness.test_the_same_seed_produces_the_identical_maze_twice` |
| the spec's picture decoded and loaded satisfies every invariant | `TestTheSpecificationsOwnMaze` — six tests, including the 264 count |
| the state type is frozen | `test_model.TestGameState.test_the_state_is_frozen` |
| the neighbour query agrees with a naive recount | `test_model.TestNeighbourQuery.test_open_directions_agrees_with_a_naive_recount` |
| every core module imports with `curses` and `subprocess` unavailable | `test_purity.TestTheCoreImportsCleanlyWithoutTheShell` |

Two of those are worth a second look. `test_the_poison_really_bites` asserts
the poison itself raises, because the import test proves nothing if it does
not. And `test_generation_draws_only_from_the_rng_it_was_given` reseeds the
*global* `random` between two identical seeded calls and asserts the result
does not move — C7 asserted as a consequence rather than by inspection.

## Deviations from the plan, for a ruling

1. **`from_text` does not enforce 29 × 19.** The plan calls it "a loader that
   turns a text grid into a maze value, so tests and later items can
   hand-write boards". WI-6 and WI-7 will want small hand-written boards to
   test one move on, and a 29 × 19 minimum would forbid that. So `from_text`
   accepts any rectangular grid and `Maze` carries its own height and width;
   MAZE-1 is asserted against `generate` instead, where it belongs. Additive,
   but it is a deviation and it needs a ruling.

2. **Style identifiers are plain strings, and `model.py` names only
   `STYLE_DEFAULT`.** The alternative was an enum in `model.py` listing every
   style, which would mean WI-3 editing this module to add one. Strings let
   `theme.py` own the vocabulary outright. WI-4 maps identifiers to colour
   pairs and so needs the vocabulary `theme.py` exports, not one here.

3. **`tests/fixtures/spec_maze.txt` holds the 29 maze rows only** — no status
   line, no annotation arrows, 37 columns each. A frame fixture for WI-3 will
   want the status row and the 3-column right margin too; that is WI-3's to
   add, because it is a picture fixture and not a maze one.

4. **`termgame/maze.py` also exports the invariant checks** (`has_solid_border`,
   `dead_ends`, `open_blocks`, `is_fully_connected`, `reachable_from`,
   `check`). The tests need them; putting them in the module rather than in the
   test file means WI-10's verification harness can call them too, and
   `reachable_from` is a flood fill that WI-5 may want for START-2. Additive.

5. **`tests/test_purity.py` guards more than §2.4's "cheap way".** The plan
   suggests one test that imports every core module with `curses` and
   `subprocess` poisoned. That one is here, and so are four more, because the
   plan says "whoever builds WI-1 should write it; it then protects everyone":

   - a static AST scan refusing a *direct* import of `curses`, `time`,
     `subprocess`, `os`, `sys`, `pathlib` and nine more, which catches the ones
     that cannot be poisoned because the test runner has already imported them;
   - the core never imports `screen`, `loop` or `window` — arrows inward only;
   - **at most one** module in `termgame/` imports `curses`, at most one
     imports `subprocess`, and no module does both (§2.4, third and fourth
     paragraphs);
   - no core module calls `random.*` or does `from random import …` — C7.

   Both guards **discover the modules by listing `termgame/`** and subtracting
   the three the architecture declares impure, so `theme.py`, `view.py` and
   `rules.py` are covered the moment they land, without WI-3, WI-5, WI-6 or
   WI-7 touching this file. The "at most one" tests pass vacuously today; they
   are there to fail on the day WI-4 or a later item slips.

   This is additive and it constrains other people's work items, so it needs a
   ruling more than the rest of this does.

## Contradictions found

None between the plan and the architecture on this item. Three measurements
were re-run rather than trusted, and all three reproduced: the mean corridor
count (265.4 against 265.3), the spec mock-up's 264 corridors with no broken
invariant, and the joiner-column rule of C9.

One number came out slightly worse than the architecture's, and it is worth
recording rather than hiding: architecture §7 measured **0.642 ms** per maze;
this generator measures **0.767 ms** on the pinned 3.9.6 interpreter. That is
0.125 ms on a 143 ms tick and generation happens once per game, so it changes
nothing — but it is not the same number, and the difference is most likely the
`Maze` constructor deriving its neighbour lookup up front, which the
prototype did not do.

## What needs a human

Nothing. This item is pure: no window, no terminal, no clock, no file read
outside the tests.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
