# WI-4: Wall glyphs

Risk: LOW
This is the plan's floor: an isolated pure presentation leaf with no window, no state and no callers yet. A defect would show up in the drawing and be local to it.

Lane A, Dev A. Branch `r8/wi-4-wall-glyphs`, cut from `origin/main` at `75723e7` (WI-1 merged). It also carries `r8/wi-1-completion` (WI-1's completion record and post-merge log lines), on the conductor's ruling.

**What it adds:** `terminal_game/presentation/wall_glyphs.py`, a pure module in the presentation layer:

- `wall_glyph(north, south, east, west)` returns the character for a wall square.
- `joining_glyph(west_is_wall, east_is_wall)` returns the joining cell between two squares.
- `square_glyph(is_wall, width, height, col, row)` and `joining_cell(...)` do the same from any `is_wall(col, row)` predicate. They treat squares beyond a `width` x `height` grid as not wall, whatever the predicate says. A `Maze` from WI-2 can be passed as `maze.is_wall`, or wrapped in a lambda.
- `WALL_CHARACTERS` is every character the module can draw.

`tests/specimen.py` reads the specimen picture from `docs/FUNCTIONAL_REQUIREMENTS.md` §3 at test time, so the WI-4 tests (and later WI-10's) are pinned to the document itself. It is a helper, not a test module.

## Claims

Commands run from the repository root with the §1.2 environment.

| Claim | Statement (word for word from the plan) | Evidence | What the output shows |
|---|---|---|---|
| **WI-4/C1** | A wall square gets its character from which of its north, south, east and west neighbours are wall, for all 16 combinations: none `■`; east and/or west only `═`; north and/or south only `║`; south+east `╔`; south+west `╗`; north+east `╚`; north+west `╝`; north+south+east `╠`; north+south+west `╣`; east+west+south `╦`; east+west+north `╩`; all four `╬`. | Executable: `.venv/bin/python -m pytest -v tests/test_wall_glyphs.py -k "c1 or sixteen"` | 17 PASSED lines: the table has 16 entries, and there is one parametrised case per (north, south, east, west) combination, each asserting the character the plan names. |
| **WI-4/C2** | The cell between two horizontally adjacent grid squares shows `═` when both squares are wall, and is blank otherwise. | Executable: `.venv/bin/python -m pytest -v tests/test_wall_glyphs.py -k c2` | 4 PASSED lines, one each for wall/wall giving `═`, and wall/corridor, corridor/wall and corridor/corridor giving a blank. |
| **WI-4/C3** | A square beyond the edge of the grid counts as not wall, so the four corners of the outer wall come out `╔`, `╗`, `╚` and `╝`. | Executable: `.venv/bin/python -m pytest -v tests/test_wall_glyphs.py -k c3` | 2 PASSED lines. A 3 x 3 ring's corners come out `╔ ╗ ╚ ╝`. So do a predicate's corners when the predicate calls *every* square wall, even off the grid: the edge comes from `width`/`height`, not from the predicate. |
| **WI-4/C4** | Applied to the maze in the specimen picture (`docs/FUNCTIONAL_REQUIREMENTS.md` §3), every wall square and every joining cell comes out exactly as the specimen shows it. | Executable: `.venv/bin/python evidence/WI-4/specimen_glyphs.py`, and `.venv/bin/python -m pytest -v tests/test_wall_glyphs.py -k c4` | The harness prints the specimen's walls, redrawn from nothing but the wall/corridor grid. It ends `WI-4/C4 HOLDS: 287 wall squares and 518 joining cells compared with the specimen, 0 mismatches; 4 joining cells under sprites, all blank underneath`. The 4 cells left out are `▐ ▌` around the player and `▗ ▖` around the ghost, which the composer (WI-10) draws over blank joining cells. The tests assert the same, plus the two lone `■` squares at grid (6, 18) and (6, 22). Which specimen squares are wall is decided from the twelve characters in the plan's C1 table, written out in the test and the harness, not from the module under test. Both check that every other square holds a dot or the player's block, and that there are 287 wall squares (551 minus the lead's independent count of 264 corridor squares, plan X5). |

Suite at the head: `.venv/bin/python -m pytest -q` gives **159 passed, 1 skipped**. `.venv/bin/python -m tools.layer_check` reports `presentation 2` and PASS.

## Diff map

```
terminal_game/presentation/wall_glyphs.py (new) -> WI-4/C1, C2, C3
tests/specimen.py (new)                         -> evidence for C4 (reads the specimen from the requirements)
tests/test_wall_glyphs.py (new)                 -> evidence for C1-C4
evidence/WI-4/specimen_glyphs.py (new)          -> evidence for C4
docs/prs/PR-WI-4-wall-glyphs.md                 -> this brief
docs/progress/r8-wi-4-wall-glyphs.md            -> progress log
docs/completions/COMPLETION-M1-DEV-A.md         -> WI-1 completion record (mechanical)
docs/progress/r8-wi-1-scaffold.md               -> WI-1 completion record (mechanical): post-merge log lines
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
