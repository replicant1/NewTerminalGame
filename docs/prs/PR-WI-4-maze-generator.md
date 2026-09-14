# WI-4 — the maze model and its generator

**Branch:** `wi-4-maze-generator`, cut from `main` at `5269b67`
**Lane:** DEV-B, iteration M0
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **256 passed, 0 failed, 0 skipped** (6.5 s).
**Windows opened:** none. This item is pure domain and drove nothing on the desktop.

---

## What this is

A 19-across by 29-deep grid of corridor and wall, laid out at random every game, with no dead ends
and no unreachable square — MAZE-1 to MAZE-6. It is pure: no `curses`, no `subprocess`, no `os`, no
`sys`, no `time`, and no screen geometry anywhere in it.

It is the head of the critical path. WI-7 (the ghost), WI-5a (the wall glyphs) and WI-9 (wiring the
game) all build on the model this adds, so the section on **what downstream items can rely on** below
is the part of this document that matters most to them.

## The files added

Six new files, and one existing file extended. **Nothing else in the tree was touched** — in
particular `tests/__init__.py` is byte-for-byte as it was on `main`, and none of the five stale root
executables was read, changed or removed.

| File | What it is |
| --- | --- |
| `terminalgame/domain/__init__.py` | The Domain package, and the purity rule stated where a reader will meet it. |
| `terminalgame/domain/maze.py` | `Maze`, `Direction`, `WIDTH` / `HEIGHT`, `WALL` / `CORRIDOR`, `solid`. The model: immutable, four-sided neighbour queries, a walk along corridors. |
| `terminalgame/domain/maze_generator.py` | `generate_maze`, `generate_maze_with`, `MazeTooSmall`. The carve and the braid, both on the odd lattice. |
| `tests/test_maze.py` | The model alone, against mazes written out as text by hand. 29 tests. |
| `tests/test_maze_generator.py` | The seed sweep and the two passes. 30 tests. |
| `docs/findings/WI-4-maze-invariants-over-seeds.md` | 20 000 seeds measured, and what the generator actually produces. |
| `docs/progress/wi-4-maze-generator.md` | The progress log. |
| `tests/test_layering.py` | **Extended**, not created — `DomainPurityTest` added, 6 new tests. See below. |

**Names chosen to collide with nothing.** The existing test files are `test_screen_port.py`,
`test_curses_adapter.py`, `test_game_main.py`, `test_real_terminal.py`, `test_layering.py`,
`fake_terminal.py`, and DEV-A's `test_launcher_*.py` and `launcher_fakes.py`. `test_maze.py` and
`test_maze_generator.py` are new names under neither prefix. The only file this branch shares with
anyone is `tests/test_layering.py`, which was already on `main` — this is an edit to a merged file,
not a race to create a new one.

## The one idea in it: everything stays on the odd lattice

Number the squares from `(0, 0)` at the top-left. Call a square a **cell** when both coordinates are
odd, and a **connector** when exactly one is. **No pass ever opens a square with both coordinates
even.** That single restriction delivers two requirements at once:

- **MAZE-2, corridors one square wide.** Take any 2 x 2 block of squares. One of its two columns has
  an even x and one of its two rows has an even y, so **exactly one of the four squares has both
  coordinates even** — and that square is wall. So no 2 x 2 block is open all through, on any maze
  this generator can produce, at any size, under any random source. MAZE-2 is not a property measured
  over some number of mazes; it is a property of the construction.
- **MAZE-3, a solid border.** Cells run from 1 to `width - 2`, connectors lie between two cells, so
  nothing on the ring is reachable by either pass. The border is simply what the passes cannot touch.

**This is architecture caution C8, and the caution is about the braid specifically.** The carve stays
on the lattice naturally, because it moves two squares at a time. It is the braid — which is hunting
for a wall it can open — that would wander off and make a 2 x 2 block if it were not held there. It
is held there: `_braid` chooses only from `_cell_neighbours`, the same generator the carve uses.

The two passes:

1. **Carve** — a depth-first walk from a random cell, opening the connector to each unvisited cell as
   it is first reached. Every cell visited once, one connector opened per cell after the first: a
   spanning tree, so MAZE-6 holds from the start. Trees have leaves, so this leaves dead ends.
2. **Braid** — every cell with fewer than two ways on gets another connector opened, chosen at random
   from the walled ones leading to another cell. Opening only ever *adds* ways on, so the braid
   cannot create the dead end it is removing somewhere else and cannot disconnect anything. It stops
   when none is left (MAZE-5). It terminates because each step opens a connector that was wall and
   there are finitely many connectors.

A connector is never a dead end either: the only two of its four neighbours that can ever be corridor
are the two cells it joins, and both are open by the time it is.

## What was measured

Full numbers in `docs/findings/WI-4-maze-invariants-over-seeds.md`. The short form:

**`MAZE_SWEEP_SEEDS=20000 python3 -m unittest tests.test_maze_generator` — 30 tests, 0 failed,
58.8 s.** Over 20 000 mazes: 0 wrong sizes, 0 border breaches, 0 squares off the lattice, 0 2 x 2 open
blocks, 0 dead ends, 0 unreachable squares, and 20 000 distinct layouts. The architect measured the
same over 300; this is the same result two orders of magnitude further out.

Over 2 000 seeds, running the passes separately: the carve leaves **8 to 22 dead ends** every time
(mean 14.5), the braid opens **8 to 21** connectors, and the finished maze has **259 to 272 corridor
squares** — 47 % to 49 % of the grid. The most ways on from any square is 3 or 4; the fewest is always
2.

## How the tests are kept honest

Three of the required properties are satisfied *vacuously* by a grid of solid wall — no 2 x 2 open
block, no dead end, nothing unreachable, all trivially true when there are no corridor squares at
all. A sweep that only checked those would go green on a generator that did nothing. So:

- **The corridor count is asserted too** — more than 200 squares, fewer than the whole grid.
- **The carve is exercised on its own** and shown to leave dead ends in quantity on all of the first
  20 seeds. That is what makes "zero dead ends" after the braid mean something: the braid is
  demonstrably the thing removing them, not a pass that happened never to be needed.
- **A random source that never chooses randomly** (`AlwaysFirst`, which returns index 0 every time)
  still produces a maze meeting every requirement. The invariants are the algorithm's, not the random
  source's luck. The assertion is on the maze that comes out, not on any call being made.
- **The scanning helpers in `test_layering.py` are checked against literal source strings**, so a
  clean purity result means the scan looked rather than that it was blind.

**No test was proved able to fail, and no working code was broken to watch anything go red.** Every
one of the above is an assertion about what the generator returned.

**One test I would flag rather than defend:** `test_the_domain_carries_no_screen_geometry` is a text
scan for the screen port's vocabulary (`REQUIRED_WIDTH`, `Frame`, `Colour`, `Screen`). It cannot
catch a bare `40` typed out by hand, and its docstring says so. It catches the way the leak would
actually happen — the Domain reaching for the port's constants — and nothing more. If somebody wants
caution C5 guarded harder than that, it needs a different mechanism, not a longer word list.

## `tests/test_layering.py` — what the extension contains

The technical lead promoted this file from a one-off to a standing obligation, with WI-4 and WI-7
adding the domain-purity cases. **Stating what it now contains rather than that it was agreed:**

- The existing `LayerRuleTest` is **unchanged** — same three tests, same names, same assertions.
- `PACKAGE_ROOT`, `THE_ADAPTER`, `python_files`, `source_of` and `imports` are **unchanged**. `imports`
  already took the module name as a parameter, so the new cases are a list and a class, not new
  machinery.
- Three module-level names added: `THE_DOMAIN = "domain"`, and
  `FORBIDDEN_IN_DOMAIN = ("curses", "subprocess", "os", "sys", "time")`.
- Two helpers added: `domain_files()` (the files under `terminalgame/domain/`) and
  `imported_game_modules(source)` (which `terminalgame.…` modules a source imports — `imports` cannot
  tell `terminalgame.domain.maze` from `terminalgame.screen.port`, and the Domain's dependency rule is
  exactly that distinction).
- One class added, `DomainPurityTest`, with six tests: the Domain is where it is said to be; it
  imports nothing from `FORBIDDEN_IN_DOMAIN`; the scan can see the imports it is looking for and does
  not fire on prose; the dependency scan can tell the Domain from the rest; the Domain depends on
  nothing above it; the Domain carries no screen vocabulary.
- The module docstring now says that **the launcher half of the layer rule is still unguarded and is
  WI-12's**, so the gap is recorded in the file rather than left to be rediscovered. **I did not close
  that gap** — nothing here walks `launcher/`.

`sys` is on the forbidden list because `sys.stdout` is what plan §3 names: a module that cannot import
`sys` cannot write to it, and cannot reach `sys.argv` either.

## What downstream items can rely on

WI-7, WI-5a and WI-9 come next. The model's surface, and what each part is for:

```python
from terminalgame.domain.maze import (
    WIDTH, HEIGHT,            # 19, 29 — squares of the maze, not columns of a terminal
    WALL, CORRIDOR,           # what a square is
    NORTH, SOUTH, EAST, WEST, DIRECTIONS,
    Maze, solid,
)
from terminalgame.domain.maze_generator import generate_maze, generate_maze_with
```

| Call | What it gives you |
| --- | --- |
| `generate_maze()` | A fresh maze — MAZE-4, what a new game asks for. |
| `generate_maze(seed)` | The same maze every time for that seed. |
| `generate_maze_with(random.Random(n))` | The same, for a caller that owns the whole game's randomness. |
| `maze.is_corridor(x, y)` / `is_wall` / `square_at` | One square. **Anything off the grid is wall**, so a caller walking past the edge gets a sensible answer rather than an exception — and a negative x is not read as the right-hand edge. |
| `maze.neighbours(x, y)` | All four sides as `(direction, x, y)`, on the grid or not. |
| `maze.open_neighbours(x, y)` | Only the ways on. **This is the one the ghost wants.** |
| `maze.ways_on(x, y)` | How many. MAZE-5 is the statement that this is never below 2. |
| `maze.corridor_squares()` | Every corridor square in reading order — where the dots go (WI-6), and what START-1 and START-2 measure over. |
| `maze.reachable_from(x, y)` | Breadth-first along corridors. MAZE-6 stated as a set. |
| `maze.rows()` | The grid as tuples, for Presentation. |
| `maze.as_text()` / `Maze.from_text()` | For a person reading a failure, and for a test that wants a known maze. **Not** how the game is drawn. |

Three things worth knowing before building on it:

1. **Coordinates are `(x, y)`, x the column from the left, y the row from the top, so north is
   `y - 1`.** There is a test pinning that specifically, because it is the thing that is easy to get
   backwards and impossible to notice later.
2. **`Maze` is immutable and hashable.** `rows()` returns tuples and mutating them raises; changing
   the list you built it from does not change the maze.
3. **`generate_maze` carries no state between calls** — there is a test for it — so a seed names a
   maze regardless of how many were made before it.

## Deviations from the plan, for a ruling

Two, both additive.

1. **`generate_maze` takes `width` and `height`, defaulting to 19 x 29.** The plan asks only for
   19 x 29. The parameters exist because the tests want small grids, and because they demonstrate
   that MAZE-2, MAZE-5 and MAZE-6 come from the algorithm rather than from those two numbers —
   `OtherGridSizesTest` checks nine sizes. The specification's size remains the default and the sweep
   asserts it. **If the technical lead would rather the size were fixed, say so and I will drop the
   parameters**; nothing downstream needs them.
2. **`MazeTooSmall` is raised for an even dimension or a lattice under 2 x 2 cells.** The plan does
   not mention error behaviour. An even width would put the last cell hard against the edge and
   MAZE-3 could not hold; a single column of cells has cells that no braid can give a second way on,
   so MAZE-5 could not hold. Refusing loudly seemed better than returning a grid that quietly breaks
   a requirement, but it is a decision the plan did not ask for.

## Contradictions found

**None in the plan or the architecture as they bear on WI-4.** Caution C8 is correct and its
restriction is exactly what is needed; C5 is correct; MAZE-1 to MAZE-6 are consistent with each other
and all six are met. The 300-maze measurement C8 reports reproduces at 20 000.

One observation that is not a contradiction but is worth recording: **C8 is stated as a measurement
("I measured 0 such blocks … across 300 generated mazes") when it is available as a proof.** The
parity argument above holds for every maze at every size under every random source. That is a
stronger claim than 300 samples, and a later reader deciding whether the restriction can be relaxed
should be told it is a proof, because the answer is no rather than probably-not.

Separately, and **carried rather than acted on**, the three corrections the conductor flagged on
`main`: the "Agreed with DEV-B" section in `docs/prs/PR-WI-1-window-launcher.md` records an agreement
that never happened, as does line 24 of `docs/progress/wi-1-window-launcher.md`; the claim in that
passage that `tests/__init__.py` must be *empty* is false — discovery needs it to **exist**, and the
81-byte file on `main` discovers 256 tests on this branch. I changed neither file and I did not touch
`tests/__init__.py`.

## What needs a human

Two things, neither of which an agent can settle.

1. **Are the mazes any good to play?** Every property in the specification is a floor: no dead end, no
   isolated pocket, one-square corridors. Nothing in MAZE-1 to MAZE-6 asks whether the layouts are
   *interesting*, and I cannot judge it. To look:

   ```
   cd <repo root>
   python3 -c "from terminalgame.domain.maze_generator import generate_maze; print(generate_maze().as_text())"
   ```

   Run it a few times. `#` is wall, a space is corridor. What to look for: whether the corridors feel
   open enough to be chased through, whether the braid has left it too loopy or not loopy enough, and
   whether 47–49 % corridor is the density you want. **If it wants tuning, the braid is the knob** —
   opening more than one extra connector per dead end makes it more open, and the invariants survive
   it because opening never breaks any of them.

2. **Whether the parameterised grid size stays** — deviation 1 above. That is the technical lead's,
   not mine.

**No window was opened and nothing touched the desktop**, so there is no window-related human check
and nothing was left on anyone's screen.

## Commits

| | |
| --- | --- |
| `db406cc` | WI-4: the maze model, the generator, and the odd-lattice invariant |
| `6db3c50` | WI-4: the seed sweep, the two passes, and the domain-purity cases |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
