# WI-10: Frame composer

Risk: MEDIUM
The plan's floor, not raised. Every picture the game shows comes through this function, but it is pure presentation code that opens no window and changes no state.

Lane A, Dev A. Branch `r8/wi-10-frame-composer`, cut from `origin/main` at `0680c8c` (WI-2, WI-4 and WI-5 merged). `main` merged in at `b1adc97` to bring in WI-7 and AMEND-1, with no conflicts. Not stacked.

**What it adds:** `terminal_game/presentation/frame_composer.py`. `compose(state)` returns 30 rows of 40 `(character, role)` cells, the shape lane C's frame check accepts (`terminal_game/shell/frame.py` on PR #123).

- Rows 0–28 are the maze. Square *n* is at cell 2*n*, and its joining cell is 2*n*+1. Walls come from WI-4's glyphs, and dots are `▪`.
- The sprites are drawn over the maze: first the player `▐█▌`, then the ghost `▗█▖`.
- Row 29 is WI-5's `status_row(score, outcome)`.

**The state it reads, and the interface with Dev B.** It reads `maze` (with `width`, `height`, `is_wall(square)` and `is_corridor(square)`), `dots`, `player`, `ghost`, `score` and `outcome`, and nothing else. WI-7's `GameState` has exactly these attributes, and its `outcome` values are the status line's. I built against this narrow duck-typed interface while WI-7 was still open, and the unit tests use a local stand-in with the same attributes. WI-7 (#127) has since merged. I merged `main` (`b1adc97`) into this branch and added a seam test (WI-10/A2) that composes the domain's own `new_game(...)` state. The composer still imports nothing from the domain.

## Claims

Commands run from the repository root with the §1.2 environment. `-v` without `-q` prints each test's name.

**Controls:** every claim is `n/a`. `frame_composer.py` is a new module, and the base (`0680c8c`) has no frame composer, so there is nothing a claim could run against there. A control could only fail on `ImportError`.

**How C9 is read.** WI-5/C5 makes *every* cell of the status row status-coloured, blanks included. WI-10/C9 lists "the status row in the status colour" separately from "every blank cell has the background colour". So I read C9's blank-cell clause as covering the maze rows, with the status row coloured as WI-5 gives it. Its trailing blanks are in the status role, which is invisible on black. `test_c9_a_blank_cell_in_the_status_row_is_in_the_status_role_as_wi5_gives_it` pins this reading. If the lead meant otherwise, WI-5/C5 and WI-10/C9 contradict each other for those cells, and that is a ruling for the lead.

| Claim | Statement (word for word from the plan) | Evidence | What the output shows | Control |
|---|---|---|---|---|
| **WI-10/C1** | Given the specimen's maze, dots, player and ghost squares and a score of 0, the composed frame reproduces the specimen picture in `docs/FUNCTIONAL_REQUIREMENTS.md` §3 character for character, all 30 rows, each specimen row padded with blanks to 40 cells, ignoring the `← …` annotations. | Executable: `.venv/bin/python evidence/WI-10/compose_probe.py`, and `.venv/bin/python -m pytest -v tests/test_frame_composer.py -k "c1 or reads_back"` | The probe reads the specimen back into a state: walls from the plan's twelve characters, dots from `▪`, the player at (10, 13) and the ghost at (1, 27). It composes the state and prints all 30 rows beside a role map. Every row is marked equal, and it ends `WI-10/C1 HOLDS: 0 of 30 rows differ from the specimen, 0 cells in all`. The test asserts each row against `docs/FUNCTIONAL_REQUIREMENTS.md`, read at test time. | n/a: new module |
| **WI-10/C2** | The frame is 40 cells by 30 rows. Rows 0 to 28 hold the maze, and row 29 is exactly the status line WI-5 gives for the same score and outcome. Nothing from the maze is ever drawn on row 29. | Executable: `-k c2` | 5 PASSED. Over 50 generated mazes × 4 score/outcome pairs, the frame is 30 × 40 and `frame[29] == status_row(score, outcome)`. With the player and ghost both on the bottom corridor row, row 29 is still exactly the status line. | n/a: new module |
| **WI-10/C3** | Grid square *n* (counting from 0) is drawn in cell 2*n*, with its joining cell to the east in cell 2*n*+1, so the maze's characters occupy cells 0 to 36. Cell 37, the joining cell after the last square, has no square east of it, and it and cells 38 and 39 are blank on every maze row, as in the specimen, whose maze rows are 37 characters wide. | Executable: `-k c3`, and the probe's role map | PASSED over 50 generated mazes. Cell 2*n* holds a wall character exactly when square *n* is wall. Cell 2*n*+1 is `═` exactly when squares *n* and *n*+1 are both wall. Cells 37–39 are blank background on all 29 maze rows. The probe's role map ends `...` on every maze row. | n/a: new module |
| **WI-10/C4** | A corridor square holding a dot shows `▪` in the dot colour. A corridor square without one shows blank. | Executable: `-k c4` | PASSED over 50 mazes, where every other corridor square holds a dot. Dotted squares are `('▪', 'dot')` and the others are `(' ', 'background')`. | n/a: new module |
| **WI-10/C5** | The player is drawn as `▐█▌` in the player colour and the ghost as `▗█▖` in the ghost colour, centred on their squares, so the two differ in colour and in outline. | Executable: `-k c5`, and the probe (row 13 `PPP`, row 27 `GGG`) | PASSED. Cells 2*c*−1 to 2*c*+1 are `▐█▌` in the player role and `▗█▖` in the ghost role. | n/a: new module |
| **WI-10/C6** | When the player and the ghost stand on the same square, the ghost is drawn and the player cannot be seen. | Executable: `-k c6`, and the probe's `C6 both on (2, 5): ▗█▖ ..GGG..` | PASSED. On a shared square, the cells show `▗█▖` in the ghost role, and no cell anywhere in the frame is in the player role. | n/a: new module |
| **WI-10/C7** | While the ghost stands on a square with a dot, the dot is hidden. Once the ghost moves off, it is drawn again. | Executable: `-k c7`, and the probe's two C7 lines | PASSED. With the ghost on the only dot, its cell is `('█', 'ghost')` and no dot-role cell exists. With the ghost elsewhere and the same dots, that cell is `('▪', 'dot')` again. | n/a: new module |
| **WI-10/C8** | When the player and the ghost stand on horizontally adjacent squares, both centre blocks `█` are drawn, each in its own colour. | Executable: `-k c8`, and the probe's `C8 … ║▐█▗█▖ WPPGGG` | 2 PASSED, with the player on the left and on the right. Each square's centre cell is `█` in its own role. | n/a: new module |
| **WI-10/C9** | Every wall character is in the wall colour, every dot in the dot colour, the status row in the status colour, and every blank cell has the background colour. | Executable: `-k c9` | 2 PASSED. Over 50 mazes, every maze-row cell outside the sprites is a wall character in the wall role, `▪` in the dot role, or a blank in the background role. Every status-row cell is in the status role (see *How C9 is read*). | n/a: new module |
| **WI-10/C10** | Composing a frame changes nothing: composing twice from the same state gives identical frames, and the state is unchanged. | Executable: `-k c10` | PASSED. The state here is a *mutable* dataclass with a mutable `set` of dots, so any change would show. It equals its deep copy after two compositions, and the two frames are equal. Altering a returned frame does not alter the next one. | n/a: new module |
| **WI-10/A1** | A maze wider than 19 squares or taller than 29 is refused with `ValueError` rather than drawn over the margin or the status line. A shorter maze leaves the rows below it blank. | Executable: `-k a1` | 4 PASSED. Mazes of 20 × 29, 19 × 30 and 20 × 30 each raise `the frame holds a maze of up to 19 x 29 squares, not W x H`. A 5 × 3 maze draws its three rows exactly (`╔═══════╗`, `║▐█▌▪▗█▖║`, `╚═══════╝`), rows 3 to 28 are all blank background, and row 29 is the status line. | n/a: new module |
| **WI-10/A2** | The composer draws the domain's own `GameState`, as WI-7's `new_game` makes it, exactly as it draws a stand-in carrying the same attribute values, with the player where the state puts it. | Executable: `-k domains_game_state` | PASSED over 20 generated mazes. `compose(new_game(maze)) == compose(stand_in)`, and the player's centre cell is `█` in the player role at `game.player`. | n/a: the seam is new (neither module existed on the base) |

Suite at the head: `.venv/bin/python -m pytest -q` gives **408 passed, 1 skipped**. `.venv/bin/python -m tools.layer_check` passes. The composer imports only `presentation.roles`, `presentation.status_line` and `presentation.wall_glyphs`.

## Diff map

```
terminal_game/presentation/frame_composer.py:1-31   docstring (layout, draw order, blank roles, what it reads) -> WI-10/C1-C10
terminal_game/presentation/frame_composer.py:33-54  imports and constants -> WI-10/C2, C3 (sizes), C5 (sprites), C4 (dot)
terminal_game/presentation/frame_composer.py:57-72  _maze_row -> WI-10/C3, C4, C9
terminal_game/presentation/frame_composer.py:75-81  _draw_sprite -> WI-10/C5, C6, C7, C8 (and C2: nothing drawn on row 29)
terminal_game/presentation/frame_composer.py:84-89  compose: size check -> WI-10/A1
terminal_game/presentation/frame_composer.py:90-95  compose: maze rows, player then ghost, status row -> WI-10/C1, C2, C6, C10, A2; A1 (blank rows below a short maze)
tests/test_frame_composer.py (new)                  -> evidence for C1-C10, A1, A2
evidence/WI-10/compose_probe.py (new)               -> evidence for C1, C3, C5-C8
docs/prs/PR-WI-10-frame-composer.md                 -> this brief
docs/progress/r8-wi-10-frame-composer.md            -> progress log
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
