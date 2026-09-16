# WI-5 — The maze, generated

**Developer:** DEV-A · **Branch:** `r6/wi-5-maze-generated` · **Base:** `main`
**Depends on:** nothing · **Iteration:** M0 · **Requirements:** MAZE-1 … MAZE-6

---

## What this is

The Domain layer's maze. Three modules, all pure: no windowing toolkit, no
clock, no globally reached-for randomness. The generator is *handed* a random
source and everything it decides comes from there.

| Module | What it holds |
| --- | --- |
| `terminalgame/domain/maze.py` | `Square`, `Direction`, `SquareKind`, and `Maze` — the immutable grid and the query surface |
| `terminalgame/domain/maze_invariants.py` | MAZE-2, MAZE-3, MAZE-5 and MAZE-6 written as predicates over a finished grid |
| `terminalgame/domain/maze_generator.py` | `generate_maze(random_source)` — carve, then repair, then verify |

## The shape of the grid, and why three requirements come free

MAZE-1 asks for 19 across and 29 deep. Both are odd:

```
19 = 2 * 9 + 1        29 = 2 * 14 + 1
```

so the grid is exactly a **9 × 14 arrangement of cells at odd coordinates**,
with the square between two adjacent cells as the connector carved out when
they are joined. This is the same shape as the specimen picture in
`FUNCTIONAL_REQUIREMENTS.md`: on its even rows, corridor appears only at odd
columns.

Three properties then follow from the arithmetic rather than needing to be
policed:

- a square with **two even coordinates is never carved**, so no two-by-two
  block of corridor can exist and corridors are one square wide (MAZE-2);
- the outer ring has an even coordinate in at least one axis everywhere, so
  the **border stays solid** (MAZE-3);
- **every cell square is corridor**, so two diagonally touching corridor
  squares always have a corridor square orthogonally between them and no
  corridor ever runs diagonally (MAZE-2 again).

## Carve, repair, verify — the architect's caution C4

1. **Carve** a spanning tree over the 126 cells with a randomised depth-first
   walk. Every cell reaches every other, so MAZE-6 holds — but a spanning tree
   is nothing *but* dead ends, so MAZE-5 does not.
2. **Repair** by braiding: every cell with only one way on has a second wall
   opened to a randomly chosen neighbour it is not already joined to. Opening
   a wall only ever *adds* a way through, so stage 1's connectivity cannot be
   lost in stage 2 — that is the argument that MAZE-5 and MAZE-6 do not fight
   here. Cells are visited in a fixed order, and a cell brought to two ways on
   cannot drop back, so one pass suffices.
3. **Verify** the finished grid against every structural requirement and raise
   `MazeGenerationError` rather than hand out a maze that fails. Verified
   *before* handing out, as C4 asks.

## The query surface — WI-5 owns it

Per section 10 of the plan, other developers ask for a query rather than
adding one. What is there now:

| Query | Answer |
| --- | --- |
| `maze.width`, `maze.height` | 19 and 29 |
| `maze.contains(square)` | is this square on the grid at all |
| `maze.squares()` | every square, row by row |
| `maze.kind_at(square)` | `SquareKind.WALL` or `SquareKind.CORRIDOR`; raises off-grid |
| `maze.is_wall(square)`, `maze.is_corridor(square)` | the same, as predicates |
| `maze.corridor_squares()` | every corridor square, row-major |
| `maze.corridor_neighbours(square)` | the adjacent corridors, N, E, S, W — a wall square may be asked |
| `maze.ways_on(square)` | the same, keyed by `Direction`, for **WI-7**'s ghost |
| `maze.wall_neighbours(square)` | the directions whose neighbour is a wall, for **WI-8**'s glyphs |
| `Maze.from_text` / `to_text` | `#` and `.` notation, for hand-built test mazes |

Two notes for the M1 consumers:

- **`wall_neighbours` treats a neighbour off the grid as not a wall**, so the
  top-left square of a bordered maze reports `{EAST, SOUTH}` — which is the
  `╔` the specimen picture shows. WI-8 should get the border corners and edges
  straight out of it.
- **`from_text` accepts any rectangular size**, so WI-7 can build the small
  hand-made mazes its tests need (a straight corridor, a T-junction, a dead
  end) without going near the generator.

## Tests

`tests/domain/test_maze.py`, `tests/domain/test_maze_invariants.py` and
`tests/domain/test_maze_generator.py`.

The generator's properties are asserted **over many seeds**, from mazes built
once and shared across the tests. The property assertions in
`test_maze_generator.py` are written **directly against the query surface**,
not through `maze_invariants`, so they do not simply re-run the generator's own
verify step; `maze_invariants` gets its own tests against hand-built mazes with
known faults. For the single algorithm most likely to ship subtly wrong, two
independent statements of the same property is the point, not duplication.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

Counts are in the final comment on this PR and in
`docs/completions/COMPLETION-M0-DEV-A.md`.

## Deviations from the work item as written

None in substance. Names, module layout and the test tree are mine, as section
1 of the plan allows. Two additions worth a ruling only if the lead disagrees:

- **`terminalgame/` as the root package with a `domain/` subpackage.** Nothing
  existed to follow. A four-package layer layout is the most useful thing to
  leave for WI-10's architecture guard.
- **`maze_invariants.py` as a module of its own**, rather than private helpers
  inside the generator. It makes the verify step testable on inputs with known
  faults, and WI-6 and WI-11 may want the same predicates.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
