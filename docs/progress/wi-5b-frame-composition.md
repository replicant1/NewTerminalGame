# WI-5b — frame composition (DEV-B, iteration M2)

Local mode. No push, no `gh`, no merge into `main`.

**This branch is an integration of two unmerged branches.** Recorded here and in the PR summary
because the technical lead will merge those dependencies into `main` one at a time and needs to check
that the tree it ends up with is the one WI-5b was built and tested on.

| | |
| --- | --- |
| Base, branched from | `wi-5a-wall-glyphs` at `a93cbd6` |
| Merged into it | `wi-7-game-state` at `af4c6d9` |
| Merge commit | `bc21558` |
| **Resulting tree** | **`8dac164c2b291ac5b711023aaf72cfb60bbd5dff`** |
| Suite at that point | 352 passed, 0 failed, 0 skipped — 299 from WI-5a plus 53 from WI-7, landing exactly |

05:40:36Z  START   WI-5b, frame composition. SCRN-1, SCRN-2, SCRN-4, SCRN-5, SCRN-7, MAZE-1, END-4, SCORE-4.
05:40:50Z  READ    Plan §7 M2 and the WI-5b row, and its "tests must establish" list.
05:41:00Z  VERIFY  Integrated the two dependencies and ran the whole suite before writing a line of WI-5b: 352 passed, 0 failed, 0 skipped. The merge was measured clean with `git merge-tree` twice beforehand and it was.
05:41:20Z  RISK    **The plan expects WI-6 to have landed before WI-5b and it has not.** §7 M2: "WI-6 writes row 29 and WI-5b writes rows 0 to 28 of the same frame... WI-6 lands first (day 8) so WI-5b composes against a status row that already exists." WI-6 has not been dispatched. Proceeding on the plan's own division — I compose rows 0..28 and leave row 29 as a seam WI-6 fills — rather than writing a status line that is not mine.
05:41:40Z  DECIDE  what goes in the odd columns -> derive it from the specification's picture, the same way WI-5a derived the glyph table, rather than assume it.
05:41:50Z  VERIFY  Measured all 518 joiner positions in the picture. **Both squares wall -> `═`, 122 times, no exceptions. Otherwise blank, 396 times, with exactly 4 exceptions — and all four are the side columns of the two actor glyphs.** So the joiner rule is one line and the actors are drawn over it.
05:42:00Z  VERIFY  The even columns hold 262 dots, 2 full blocks and the wall glyphs. 262 + 2 = 264 corridor squares, so the picture is internally consistent with START-3 (no dot on the player's square) and SCORE-4 (the ghost's dot is still in the state, just covered).
05:42:10Z  VERIFY  Measured the actors rather than eyeballing them, and was wrong by a row when I eyeballed: the player is at square (10, **13**) drawn `▐█▌` (RIGHT HALF BLOCK, FULL BLOCK, LEFT HALF BLOCK) and the ghost at square (1, 27) drawn `▗█▖` (QUADRANT LOWER RIGHT, FULL BLOCK, QUADRANT LOWER LEFT). Both centred on column 2x, spanning 2x-1..2x+1.
05:42:15Z  NOTE    The ghost at square 1 spans columns 1..3, leaving column 0 — the border wall — intact. That is the measured form of the M0 ruling that a three-column glyph can never run off an edge, so `Frame.put` keeps raising and no clipping is added.
05:42:40Z  DRAFT   terminalgame/presentation/frame_builder.py — compose(state, status_line=None), draw_maze, draw_dots, draw_player, draw_ghost, draw_status_line, picture_rows, StatusLineTooWide.
05:42:55Z  VERIFY  **Composed the specification's own picture and compared it to the document: all 29 rows match character for character, 1 073 cells, 0 differing.** Built the maze from the picture, put the player at (10, 13) and the ghost at (1, 27), laid a dot on every corridor square but the player's — and the frame comes back identical to what a person drew before any of this code existed.
05:43:00Z  NOTE    Three of my own tests failed and all three were my error, not the code's. Two were a hand-written expected picture I got wrong — I had written `║` where the middle square of my small maze is SCRN-3's lone block `■`, which is the very case the specification labels "a lone wall square". Corrected by working the row through rather than pasting the output.
05:43:05Z  NOTE    The third was a real hole in **my own WI-5a guard**: PRESENTATION_MAY_IMPORT listed the domain and the port but not Presentation itself, so a layer could not import a sibling module. It could not show in WI-5a, which had one presentation module and nothing to import from. frame_builder imports the wall-glyph table and the rule failed on a case it should always have allowed. Widened to include terminalgame.presentation, with the reason written in place: the hole was in the guard, not in the code it guards.
05:43:19Z  TEST    402 passed, 0 failed, 0 skipped — `python3 -B -m unittest discover`, 8.1 s. 352 after the integration + 50 lands exactly.
