# COMPLETION — M3 · Dev B · WI-12, the final gate

**Branch** `wi-12-final-gate`, cut from `origin/main` at `bb651e0`.
**Gated build** everything merged: WI-1 … WI-10, plus WI-10a.
**WI-11 is held open** and has not been run — see §5.

---

## 1. The gate

### The suite, at the pinned command (plan §2.2), from the repo root

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 749 tests in 12.673s

OK (skipped=2)
```

**The two skips are not incidental and belong in the record.** They are
`tests/test_launch_smoke.py::LaunchSmokeTest`, skipped with *"no controlling
tty: nobody is watching this screen"*. That is the suite's only live-window
test, and it is skipped in **every agent session** by design — a test that opens
windows should run only when a person is there. So the pinned suite, run by an
agent, never opens a window and never observes a real one. The live evidence
comes from `./verify`, below, which runs `./launch-smoke` as the separate
program it is.

### `./verify` — WI-10's harness, verbatim

```
$ ./verify
[1/3] the test suite ... ok (12.5s)
[2/3] the launch smoke ... ok (10.1s)
[3/3] the scripted play-through ... ok (0.1s)

========================================================================
VERIFICATION PASSED -- 3 of 3 stages, 22.6s
  ok   the test suite -- Ran 749 tests in 12.186s; OK (skipped=2)
  ok   the launch smoke -- run 1: PASS in 9.6s
  ok   the scripted play-through -- 3 scripted games, each ending on the recorded picture
========================================================================
This is the half of 'right' a machine can check. The other half is
docs/findings/WI-10-human-checks.md, and it needs a person.
```

### `./verify --only corner` — the opt-in fourth stage, also run

Run deliberately, because plan §12's risk table names the bottom-right cell as
a failure that surfaces late and only in front of the user.

```
$ ./verify --only corner --verbose
[1/1] the bottom-right cell in a real window ... ok (3.1s)
    visible Terminal windows before: [367, 2486]
    game window id (from the supervisor): 4660
    play said: game window 4660 at (-868, 106) (reference (-898, 76) from front)
    the window reported (30, 40) to the OS after 0.00s, and (30, 40) to curses
    addstr at the corner: addwstr() returned ERR
    insstr at the corner: no error
    paint: no error
    the screen read back as the picture that went in: True
    visible Terminal windows after:  [367, 2486]

========================================================================
VERIFICATION PASSED -- 1 of 1 stages, 3.2s
  ok   the bottom-right cell in a real window -- addstr raises at the corner, insstr does not, and the whole picture reached the screen intact
========================================================================
```

**This stage is load-bearing for the traceability below**, because it is the
only place in the whole project where a **real** Terminal window was measured at
`(30, 40)` by both the OS and curses. See WIN-2 in §3.

### Window hygiene (plan §2.6)

Two stages open a real window on the user's desktop. A census was taken either
side of each.

| | visible | all |
|---|---|---|
| before the smoke | `367, 2486` | `367, 2486, 2420, 2440` |
| after the smoke | `367, 2486` | `367, 2486, 2420, 2440, **4656**` |
| before the corner | `367, 2486` | `367, 2486, 2420, 2440, 4656` |
| after the corner | `367, 2486` | `367, 2486, 2420, 2440, **4660**` |

**The visible list is identical at every one of the four points.** The
all-windows list grows by the window each stage opened and then closed, which is
exactly what `docs/findings/WI-10a-census-output-shape.md` records: a closed
window never leaves `id of every window`, it only goes invisible. **Nothing that
was on the user's screen before this run is missing from it, and nothing was
left behind.**

---

## 2. How this traceability was built, and what that is worth

**A requirement code appearing in a test file is a claim, not evidence.** Every
one of the 49 lines below was built by finding the candidate tests, reading the
body of the assertion, and asking one question: *would this test fail if the
requirement were broken?*

That was worth doing. The project had already caught two tests that passed
vacuously — WI-7's GHOST-4 draft that would have passed against a *hunting*
ghost, and WI-10a's census test asserting against an empty list. **This audit
found three more, plus two requirements with clauses that nothing in the project
demonstrates.** They are in §4, and they are the most valuable thing in this
document. The table is the routine part.

**Where a code rests on a human check, the line says so plainly and does not
name a test.** Five of the six human checks are **not run** and the sixth can
never be run by an agent; see `docs/findings/WI-12-human-check-results.md`.

---

## 3. The 49 requirement codes

**Legend.** **T** — demonstrated by a test. **T+H** — a test carries part of
the requirement, a human check carries the rest, and the line says which part is
which. **H** — a human check alone; no test demonstrates it. **T+gap** — a test
carries part and **nothing demonstrates the rest**.

### 1. The game

| Code | How | What actually demonstrates it |
|---|---|---|
| **GAME-1** | **T** | `test_scripted_game.py::AGamePlayedToAWinTest` and `RunGameStartsARealGameTest::test_a_game_it_starts_has_a_dot_on_every_corridor_but_the_player_s` assert off the picture `run_game` itself painted (>100 dots, one player glyph, one ghost glyph); `test_curses_pty.py::ScriptedGameThroughRealCursesTest::test_the_arrow_keys_moved_the_player_through_real_ncurses` and `::test_the_dots_along_the_way_were_eaten` do it through real ncurses. `test_model.py::TestGameState::test_the_state_carries_a_player_a_ghost_dots_and_a_maze` pins the shape. |
| **GAME-2** | **T** | `test_rules_player.py::HowAGameEnds::test_the_game_is_won_by_eating_every_dot_and_lost_by_meeting_the_ghost` reaches both outcomes from one board by two routes. The negative control — two dots left still gives PLAYING — is what stops a broken `dots == anything` check from passing. |
| **GAME-3** | **T** | `test_model.py::TestGameState::test_game_3_holds_by_there_being_nothing_there`. **Checked specifically:** `GAME_STATE_FIELDS` (`model.py:270`) is `tuple(f.name for f in fields(GameState))` — *derived*, not a hand-written copy — so adding a `lives` or `paused` field really does fail it. `test_rules_start.py::...::test_a_fresh_state_carries_exactly_the_seven_fields_and_no_eighth` adds a `hasattr` sweep over the six banned names. |

### 2. The window

| Code | How | What actually demonstrates it |
|---|---|---|
| **WIN-1** | **T+H** | *Does not disturb anything else* — **T, and strongly**: `test_window_failure_paths.py::NoPathEverTouchesAWindowWeDidNotOpen` (6 tests) pins that no path across 14 failure routes addresses a window we did not create, and `::test_the_checker_itself_can_fail` proves the checker rejects the four dangerous phrasings. *Opens a window of its own* — the unit tests cannot show this (their fake returns a distinct id by construction); it is shown by **`./verify` stage 2 on a real window**, and in the census above. The suite's own live test is skipped without a tty. |
| **WIN-2** | **T+H** | *40 × 30* — **T**: `test_window_script.py::SettingsTest::test_the_tab_is_set_to_forty_by_thirty` pins the literal `40`/`30` in the AppleScript, `test_executables.py::ChildBehaviourTest::test_what_the_child_paints_is_the_size_of_the_window` asserts the child's real stdout is exactly 30 rows of 40 columns — and **`./verify --only corner` measured a real window reporting `(30, 40)` to the OS *and* to curses**. *Menlo 18 on black* — **T** on the script text (`::test_the_tab_is_menlo_eighteen_on_black`). *"Large enough to read comfortably"* — **H4, not run.** ⚠️ See §4.1: one test that claims WIN-2 cannot fail. |
| **WIN-3** | **H** | **No test demonstrates this requirement.** Nothing in the suite ever reads a real window's title. What the tests pin are the *ingredients* of the recipe — the executable on disk is named exactly `Terminal Game` (`test_executables.py::NamesTest`), the child's first write clears the directory prefix (`::ChildBehaviourTest::test_the_childs_first_write_clears_the_directory_prefix`), all five scriptable title components are set false (`test_window_script.py::SettingsTest`). The smoke-script test asserts against a fake that was *told* the answer. **The requirement itself is human check H3, not run.** |
| **WIN-4** | **T+H** | *The arithmetic* — **T, and very strongly**: `test_window_geometry.py` pins the +30/+30 offset, the clamp back on-screen, the multi-display choice and the tty→front→fixed fallback chain (20 tests) on measured real-world coordinates; `::test_the_naive_offset_from_the_bottom_right_would_not_fit` is an explicit guard that the clamp test is testing the clamp; `test_check_window_placement.py::TheVerdict::test_the_offset_it_checks_against_is_the_launchers_own_constant` stops the checker carrying its own copy of `(30, 30)`. `./verify --corner` observed `+30/+30` on a real negative-x display. *"Below and right of whatever window the player was last looking at"* — **H1, and no agent can ever run it.** The corner stage measured from the *front* window, the fallback, precisely because an agent has no tty. |
| **WIN-5** | **T+H** | *The close path* — **T**: `test_window_supervisor.py::SupervisorTest::test_the_supervisor_waits_for_the_game_to_end_before_closing`, `::test_the_window_that_is_closed_is_the_one_that_was_created`, `::WaitAndCloseTest` (6), and `test_window_failure_paths.py::...::test_the_game_window_itself_is_gone_once_the_game_has_ended`, where the fake's census genuinely gains the window on open and loses it on close. **But the requirement as written is not what is tested** — `run_loop` returns only on `q` (`loop.py:89, 144-145`), so the window closes when the player quits a finished game, not "as soon as the game ends". That is **open question A1**, not a ruling. *The destructive half* — **H2, not run.** |

### 3. What is on the screen

| Code | How | What actually demonstrates it |
|---|---|---|
| **SCRN-1** | **T** | `test_view.py::TestTheGoldenFixture::test_the_first_twenty_nine_rows_are_the_mock_up_verbatim` and `::test_the_bottom_row_is_the_status_line`. **The fixture is not regenerated from the code**: `tests/fixtures/spec_maze.txt` is byte-identical to the mock-up in `FUNCTIONAL_REQUIREMENTS.md` §3, and `test_the_two_fixtures_do_not_drift_apart` pins the derived picture to it. That guard is load-bearing and correct. |
| **SCRN-2** | **T** | `test_view.py::TestNothingCursesShapedCrossesTheSeam::test_every_cell_is_one_character_and_a_plain_string_style` over 60 generated frames; `::test_every_style_used_is_one_the_theme_declares` asserts set **equality**, not subset — the anti-vacuity guard is present. |
| **SCRN-3** | **T+H** | *The joining* — **T**: `test_theme.py::TestTheWallGlyphTableAgainstTheSpecification::test_all_sixteen_masks_match_the_mock_up`. **All 16 masks really are exercised** — the fixture yields masks 0–14 (counts 2 … 118, no ambiguity), mask 15 is pinned separately to `╬`, and the loop runs over `theme.ALL_MASKS` so a missing mask would `KeyError` rather than silently skip. `test_view.py::TestASmallHandWrittenBoard::test_a_lone_wall_square_is_a_block` covers the lone square. *"Blue"* — **no test asserts the colour** (§4.3); **H6, not run.** |
| **SCRN-4** | **T+H** | *One to a corridor square, and dim* — **T**: `test_view.py::TestTheLayersAndTheirStyles::test_every_dot_is_drawn_once_in_the_dot_style` asserts the dot-styled cells equal `state.dots` minus the two entity squares (262 real dots, not an empty collection); `test_theme.py::TestTheStyleTable::test_the_dots_are_dim_and_the_player_is_bright` pins `dim`. *"Gold"* — **no test asserts the colour** (§4.3); **H6, not run.** |
| **SCRN-5** | **T+H** | *Told apart by colour and by outline* — **T**: `test_theme.py::TestTheStyleTable::test_the_player_and_the_ghost_differ_in_colour_and_in_outline` asserts the two colour indices differ *and* the outer glyphs differ; `test_view.py::TestTheEntitiesStayOnTheScreen::test_the_player_is_three_characters_and_the_ghost_a_different_three` pins the literal `▐█▌` / `▗█▖`. *"Bright yellow" and "pink" specifically, and "at a glance"* — **no test asserts the hues** (§4.3); **H6, not run.** |
| **SCRN-6** | **H** | **No test demonstrates this requirement.** The only candidate, `test_view.py::TestTheLayersAndTheirStyles::test_the_status_line_is_cyan_and_the_only_thing_on_its_row`, is *named* "is_cyan" but asserts only that the row carries `STYLE_STATUS` and nothing else does. **Nothing anywhere asserts that `STYLE_STATUS` is cyan** — §4.3. The requirement's entire content is the colour, so it rests on a person looking at the screen. ⚠️ **And plan §8 assigns no human check to SCRN-6.** It is covered in practice only because the WI-10 pack's check 6 lists *"a status line that is not cyan"* among its failures. See §4.6. |
| **SCRN-7** | **T+gap+H** | *Redrawn as things move* — **T**: `test_loop.py::PaintingTest::test_a_picture_is_painted_after_a_player_move`, `::test_a_picture_is_painted_after_a_ghost_move`, `::test_the_picture_painted_is_of_the_state_as_it_now_stands` assert the **content** of the painted frames, not that paint was called. *"Without flicker"* — **no test; H5, not run.** *"The text cursor is never visible"* — **nothing demonstrates it**; the test that claims it cannot fail (§4.2). |

### 4. The maze

| Code | How | What actually demonstrates it |
|---|---|---|
| **MAZE-1** | **T** | `test_maze.py::TestGeneratedMazeInvariants::test_every_maze_is_twenty_nine_by_nineteen` over 1000 seeds; `test_view.py::TestTheGeometry::test_columns_thirty_seven_to_thirty_nine_are_always_blank` over 60 seeds × 30 rows × 3 columns. |
| **MAZE-2** | **T** | `::test_no_maze_has_a_two_by_two_block_of_corridor` — 504 blocks scanned per maze, 1000 seeds — with `TestInvariantHelpers::test_a_two_by_two_block_is_reported` proving the helper detects a planted one. Honest caveat: the property holds by construction (`_paint` walls every `(even, even)`), so this is a regression guard rather than a discovery test. |
| **MAZE-3** | **T** | `::test_every_maze_has_a_solid_wall_border`, 1000 seeds, with `::test_a_gap_in_the_border_is_reported` as the guard-on-the-guard. Indices checked in range, so `is_wall`-off-grid cannot make it pass vacuously. |
| **MAZE-4** | **T** | `test_maze.py::TestRandomness` — 200 seeds give 200 **distinct** grids, the same seed repeats identically, and `test_scripted_game.py::RunGameStartsARealGameTest::test_two_games_in_a_row_are_not_the_same_game` shows it through the real entry point. ⚠️ Naming defect, §4.5. |
| **MAZE-5** | **T** | `::test_no_corridor_square_has_fewer_than_two_ways_on`, 1000 seeds. Not the empty-collection trap: `::test_a_maze_is_mostly_wall_but_substantially_open` pins 251–300 corridors per maze, so `dead_ends()` is never scanning an empty set. |
| **MAZE-6** | **T** | `::test_every_corridor_square_is_reachable_from_every_other`, 1000 seeds, with an explicit `assertTrue(corridors)` guard and three helper tests proving the flood fill reports pockets. |

### 5. Starting a game

| Code | How | What actually demonstrates it |
|---|---|---|
| **START-1** | **T** | `test_rules_start.py::PlayerPlacementTests::test_no_corridor_square_is_nearer_the_middle_than_the_players` — a **recount** over all 551 cells on 200 seeds, longhand, never a recomputation; `::test_player_ties_really_do_occur_on_the_generated_board` stops the tie-break clause being dead. |
| **START-2** | **T+gap** | *Furthest corridor square, ties by lowest `(row, column)`, measured across the grid and not along the corridors* — **T**: the 200-seed recount plus `::test_the_ghost_is_measured_across_the_grid_and_not_along_the_corridors`, which genuinely rules out path distance. **The metric itself is not pinned.** §4.4: I measured that on all 200 sweep seeds, squared Euclidean, Manhattan and Chebyshev choose the *identical* square. **Assumption A2 is open and the suite cannot tell two of its three candidate answers apart.** |
| **START-3** | **T** | `::DotTests::test_a_square_holds_a_dot_exactly_when_it_is_corridor_and_not_the_player` — a per-cell biconditional recounted over every square on 200 seeds — plus `::test_dot_count_is_the_recounted_corridor_count_less_one` and `::test_the_ghosts_square_does_hold_a_dot`. |
| **START-4** | **T** | `::ScoreAndOutcomeTests::test_the_score_starts_at_zero` over 200 seeds. `GameState.score` has **no dataclass default**, so it cannot be zero by omission. |
| **START-5** | **T** | `test_loop.py::PaintBeforeTheFirstReadTest::test_a_picture_is_painted_before_the_first_key_is_read` pins a recorded `["paint", "read"]` order; `test_scripted_game.py::RunGameStartsARealGameTest::test_it_paints_a_picture_before_it_is_asked_for_a_key` does it through the real entry point; `test_loop.py::GhostClockTest::test_a_run_with_no_key_presses_still_ticks_once_per_tick` covers "the ghost is already moving". |

### 6. Controls

| Code | How | What actually demonstrates it |
|---|---|---|
| **CTRL-1** | **T** | `test_controls.py::ArrowKeysTest` (4 tests, including `::test_the_four_arrows_map_to_four_different_directions`, which kills the all-map-to-UP degenerate) plus `test_rules_player.py::TheMoveItself::test_each_of_the_four_directions_moves_the_player_that_one_square`, and real terminfo escape bytes through real ncurses in `test_curses_pty.py`. |
| **CTRL-2** | **T** | `test_loop.py::ArrowKeyTest::test_holding_a_direction_is_not_required_and_is_not_remembered` — one press then 100 key-less turns leaves the player on the adjacent square; `::test_two_presses_are_two_transitions` pins one transition per press. |
| **CTRL-3** | **T** | `test_rules_player.py::APressTowardsAWall` asserts **identity** (`assertIs`), not equality, so a rebuilt-but-equal state fails it; `::test_a_wall_press_between_two_real_moves_loses_nothing` shows the score survives. |
| **CTRL-4** | **T** | `test_controls.py::QuitKeyTest` (both cases) and `test_loop.py::QuittingTest::test_quitting_does_not_apply_a_transition_first`. The *"at any point"* clause is pinned by 21 reads against an already-CAUGHT game that still quits on the final `q`. The fake screen raises on a read past its script, so the read counts are consequences, not stub counters. |
| **CTRL-5** | **T+gap** | *No other key does anything* — **T**: `test_controls.py::EveryOtherKeyTest::test_the_whole_of_the_key_space_holds_no_surprises` sweeps key codes −1 … 1023 and pins that exactly six mean anything; `test_loop.py::OtherKeysTest` (3) asserts the consequences. *"Nothing typed is echoed into the maze"* — **nothing demonstrates it, anywhere.** §4.4. |

### 7. The ghost

| Code | How | What actually demonstrates it |
|---|---|---|
| **GHOST-1** | **T** | `test_ticker.py::DriftTest` (5) pins the deadline to the ideal 1/7 s grid across 100–120 deliberately late ticks and contrasts it with the `now + tick` form (exactly 0.5 s apart by the hundredth); `test_loop.py::GhostClockTest::test_the_deadline_does_not_drift_over_a_hundred_ticks` drives the **real** loop with a fake clock 5 ms late 100 times. *"Whether or not the player is moving"* — `::test_the_ghost_moves_while_the_player_stands_still`. Honest split: the *real-clock* rate (6.99990 / 7.00078 / 6.99999 moves per second) is a recorded measurement in `docs/findings/`, not an automated test — the suite pins the arithmetic and the constant. |
| **GHOST-2** | **T** | `test_rules_ghost.py::TestGhost2StraightOn` (5) uses literal expected squares and headings over a 6-tick run with the rng replaced by a `Forbidden` double that fails on any draw. The generated-maze companion's `if maze.is_open(...)` is **not** a zero-execution branch: 2748 of 3600 ticks enter it. |
| **GHOST-3** | **T** | **Not the empty-set hazard.** `::TestGhost3TheTurnAtAJunction` uses a hand-built T entered deterministically from `(1,2)` facing into the wall, so every one of the 200 seeds is a real fork; `::test_both_arms_are_chosen_at_least_once_over_many_seeds` asserts set **equality** `{(1,1),(1,3)}`, with no empty-set escape. `::TestGhost3ReversesOnlyWhenThereIsNoChoice` (4) pins the last clause on the only board shape that can reach it, and `::TestTheHandWrittenBoardsAreWhatTheySay` proves the boards are the shapes they claim. |
| **GHOST-4** | **T** | **The WI-7 fix genuinely took, and I verified the guard myself** (`test_rules_ghost.py:566-589`). Three 200-tick runs from the same seed with the player in three places must match square-for-square and heading-for-heading; `::test_that_comparison_is_not_vacuous` then asserts the run is 200 ticks long, visits >8 squares, takes >2 headings, never ends — **and that seeds 6, 7 and 8 each give a different path from seed 5**, with a failure message that spells out why that matters. Narrow blind spot recorded in §4.7. |

### 8. Dots and score

| Code | How | What actually demonstrates it |
|---|---|---|
| **SCORE-1** | **T** | `test_rules_player.py::DotsAndTheScore::test_the_eaten_dot_is_gone_for_the_rest_of_the_game` walks the player away and back, so the removal is shown to persist in the *state*, not just in one frame; `::test_the_other_dots_are_left_exactly_where_they_were` pins the rest as a literal set. |
| **SCORE-2** | **T** | `::test_moving_onto_a_dot_eats_it_and_scores_exactly_one` (0 → 1, so the expected value never coincides with the unchanged one) and `::test_the_score_is_the_count_of_dots_eaten_over_a_whole_lap` (8 dots, 7 points, the skipped one named). |
| **SCORE-3** | **T** | `::test_moving_back_onto_an_eaten_square_adds_nothing` drives the score to **1 first** and then asserts it is still 1 — deliberately avoiding the classic "expected value coincides with the initial zero" trap. |
| **SCORE-4** | **T** | `test_rules_ghost.py::TestScore4TheGhostLeavesTheDotsAlone` (6) asserts the dot set square-for-square after the ghost stands on a dotted cell and over 200-tick runs, with non-zero starting scores (3, 9, 250) carried across, and `assertGreater(len(expected), 100)` guarding against an empty-set comparison. |
| **SCORE-5** | **T** | `test_rules_player.py::DotsAndTheScore::test_the_score_never_goes_down_at_any_step_of_a_scripted_run` walks an 18-step run asserting each step ≥ its predecessor **and** pinning the anchors 0 / 7 / 7 — so a score that never changes cannot satisfy the loop. The *shown* half reads the score straight off the rendered status row for seven values. |

### 9. How a game ends

| Code | How | What actually demonstrates it |
|---|---|---|
| **END-1** | **T** | Both directions: `test_rules_player.py::HowAGameEnds::test_walking_onto_the_ghosts_square_loses_the_game` and `test_rules_ghost.py::TestEnd1TheGhostWalksIntoThePlayer` (5). Each has a near-miss companion — the player one square off the ghost's line, the player on the square the ghost *left* — so a row-only or column-only comparison fails; the player-half board deliberately leaves a dot so END-2 cannot be what produced the ending. |
| **END-2** | **T** | `::test_eating_the_last_dot_on_an_empty_square_wins_the_game` with `::test_the_last_dot_is_only_the_last_when_the_board_is_really_empty` as the separator between "wins on the last dot" and "wins on any dot". |
| **END-3** | **T** | **The plan's single most fragile requirement, and it is properly pinned — I read the assertion myself** (`test_rules_player.py:628-657`). `EndThreeTheOrderOfTwoBranches::test_END_3_eating_the_last_dot_on_the_ghosts_square_is_a_loss_not_a_win` asserts the pre-move position in literal coordinates (one dot, on the ghost's square), then after the move asserts **`dots == frozenset()` and `score == 1` and `player == ghost == (1,2)`** — so the winning condition demonstrably holds — **and then that the outcome is `CAUGHT`**. The companion `::test_the_same_last_dot_one_square_away_from_the_ghost_is_a_win` moves only the ghost and gets `CLEARED`, so the assertion is about the ghost's square and not about last dots generally. This is **not** the weak-position case the plan feared. |
| **END-4** | **T** | `test_view.py::TestTheDrawOrder::test_the_ghost_is_drawn_over_the_player_on_the_same_cell` asserts all three picture columns equal `GHOST_GLYPHS`, explicitly `assertNotEqual(..., PLAYER_GLYPHS)`, and all three styles equal `STYLE_GHOST` — so a same-glyph/different-style regression is caught too. |
| **END-5** | **T** | The comparison is **stronger than deep equality** — `assertIs` on the state object — and it is not trivially unchanged: `test_rules_player.py::AfterTheGameHasEnded` first asserts the board has an open way out ("this board has no open way out, so the test would pass vacuously"), and `test_rules_ghost.py::TestEnd5AFinishedGameDoesNotMove::test_the_guard_is_the_outcome_and_not_an_empty_dot_set` proves *which* guard is doing the work. `test_scripted_game.py::NothingHappensAfterTheEndingTest` first asserts `len(after) > 8` so its loop is not over an empty list. **Not cited:** `test_loop.py::EndedGameTest` — that tests the loop delegating to a fake which implements the guard itself, and is correct for what it claims but is not END-5 evidence. |
| **END-6** | **T** | Both halves. *An ending does not return*: 20 keys and ticks against an already-CAUGHT game asserting `screen.reads == 21`, where the fake raises on a read past the script, so an early return fails loudly. *`q` does return*: the same **finished** game returns on its trailing `q`, plus both letter cases and the real-ncurses run. |

### 10. The status line

| Code | How | What actually demonstrates it |
|---|---|---|
| **STAT-1** | **T** | `test_view.py::TestTheLayersAndTheirStyles::test_the_status_line_is_cyan_and_the_only_thing_on_its_row` walks **all 40 columns** of row 29: every column past the text is `" "` with `STYLE_DEFAULT`, every column inside it `STYLE_STATUS`. "And nothing else" is pinned positionally, not by `rstrip()`. |
| **STAT-2** | **T** | Exact equality on the whole row with the score varied (0, 1, 3, 41), so the template is not merely reproduced at one value. Asserted literally — delimiters `«»`, nothing trimmed: `theme.status_text(PLAYING, 0)` == «`score 0    arrows, q quits`»; the rendered row == «` score 0    arrows, q quits`» (one leading space, then `ljust(40)`). **Rests on assumption A3, which is open** — but the tests pin it rather than dodge it. |
| **STAT-3** | **T** | `theme.status_text(CAUGHT, 37)` == «`CAUGHT  score 37   q quits`»; `theme.status_text(CLEARED, 274)` == «`CLEARED  score 274  q quits`»; rendered rows «` CAUGHT  score 37   q quits`» and «` CLEARED  score 274  q quits`». All three match `FUNCTIONAL_REQUIREMENTS.md` byte for byte. The spec's own two examples are internally inconsistent, and the code documents that as **A3** at `theme.py:285-301` rather than silently normalising it. **A3 is open.** |

### The count

| | Codes |
|---|---|
| **Demonstrated by tests alone** | **37** |
| **Test carries part, a human check carries the rest** | **8** — WIN-1, WIN-2, WIN-4, WIN-5, SCRN-3, SCRN-4, SCRN-5, SCRN-7 |
| **Human check alone — no test demonstrates the requirement** | **2** — WIN-3, SCRN-6 |
| **Test carries part, and nothing demonstrates the rest** | **2** — START-2 (the metric), CTRL-5 (the echo clause) |
| **Total** | **49 of 49** |

**45 of 49 have at least one genuine test.** **2 rest on a human check alone.**
**2 have a clause with neither a test nor a check assigned to it.** And every
human check those lines depend on is **not run**.

---

## 4. What does not hold up

These are the reason this document took longer than the table. Each was
confirmed by reading the assertion, and the first four by my own inspection on
top of the sweep that found them.

### 4.1 A test that claims WIN-2 cannot fail

`tests/test_curses_pty.py:286` —
`RealCursesTest::test_curses_sees_the_forty_by_thirty_window`:

```python
self.assertEqual([LINES, COLUMNS], RESULT["size"])
```

`RESULT["size"]` is what curses reported on a pty **that this same test sized**,
at line 233 via `TIOCSWINSZ` and lines 237–238 via `$LINES`/`$COLUMNS`, from the
module-level `LINES = 30, COLUMNS = 40` at lines 36–37. It imports neither
`window.COLUMNS/ROWS` nor `model.SCREEN_COLS/ROWS`. **No change anywhere in the
product can make it fail.** It proves curses reads the size it was given, which
is a fact about curses.

The module comment at line 35 — *"40 columns, 30 rows — the window the game
really runs in (WIN-2)"* — is a claim. **WIN-2 is not credited to this test
above.** The rest of that class (the bottom-right-corner hazard) is genuine and
valuable. And WIN-2's size clause *is* demonstrated, by `./verify --corner` on a
real window.

### 4.2 A test that claims SCRN-7's cursor clause cannot fail — and nothing else covers it

`tests/test_curses_pty.py:312` — `RealCursesTest::test_the_cursor_can_be_hidden`:

```python
self.assertIsInstance(RESULT["curs_set"], int)
```

`RESULT["curs_set"]` is set at line 88 by the **probe script's own**
`curses.curs_set(0)`. It tests that this terminal can hide a cursor, not that
the game hides it. `termgame/screen.py:242` is where `_hide_cursor()` implements
SCRN-7's *"the text cursor is never visible"*, and **nothing asserts it**. I
checked every `curs_set` reference in `tests/`: there are two, the probe's own
and a literal in a fake result dictionary at `test_verify.py:654`.

**This one is worse than 4.1**, because 4.1 mislabels a requirement that is
covered elsewhere and this one leaves a clause covered by nothing.

### 4.3 No test in the suite asserts any colour

Verified at `tests/test_theme.py:276-286`. The suite asserts that the styles'
colours are **distinct from each other**, that each is an `int` in `0..255`, and
that the player's differs from the ghost's. The colour **values** —
`termgame/theme.py:202-206`, `33` for blue, `178` for gold, `51` for cyan —
appear **nowhere in `tests/`**.

So the words *blue* (SCRN-3), *gold* (SCRN-4), *bright yellow* and *pink*
(SCRN-5) and *cyan* (SCRN-6) are undemonstrated. For SCRN-3, SCRN-4 and SCRN-5
that is a missing clause on a requirement whose other clauses are well covered.
**For SCRN-6 it is the whole requirement** — "The status line is written in
cyan" has nothing but its own name in a test title.

### 4.4 Two requirement clauses that nothing in the project demonstrates

**START-2's metric.** I measured this myself, by computation, without changing
anything: over the 200 seeds the START-2 sweep uses, **squared Euclidean,
Manhattan and Chebyshev pick the identical ghost square on all 200**. The
exhaustive recount that plan §11 offers as START-2's evidence is therefore
metric-blind. The sweep that found it measured the consequence directly:
changing `starting_ghost` to Manhattan passes all 36 tests; Chebyshev fails
exactly one hand-written-board test.

**Why this matters more than it looks.** A2 is one of the three open questions,
and plan §9 prices it at *"one expression and one test"*. But **if the user
answers "Manhattan", the code would change and the suite would stay green either
way** — nobody would be able to tell whether WI-11's change had taken. The fix
is a hand-written board on which the three metrics disagree.

**CTRL-5's echo clause.** *"Nothing typed is echoed into the maze"* is asserted
nowhere — not as a consequence, and not even as a recorded call. Verified
myself: **`grep -rni "echo" tests/` matches nothing at all**; the string does not
occur anywhere in the 10,612-line suite. `curses.noecho()` sits at
`termgame/screen.py:224` carrying a comment that names CTRL-5.

### 4.5 Two smaller things

- **A name that lies.** `tests/test_maze.py:152`,
  `test_a_thousand_seeds_produce_hundreds_of_distinct_mazes`, loops `range(200)`
  at line 156. The assertion (200 distinct out of 200) is strong, so it is not
  vacuous — only the name is wrong, and it is the kind of name a later reader
  trusts. (The file docstring's "1000 seeds" claim *is* honest: `SEEDS = 1000`.)
- **A tautology.** `tests/test_window_supervisor.py:112`,
  `assertEqual("open", kinds[kinds.index("open")])`, cannot fail. The four
  `assertLess` ordering assertions after it carry that test.

### 4.6 A third vacuous assertion, in a test that is otherwise fine

`test_curses_pty.py::ScriptedGameThroughRealCursesTest::test_the_unmapped_key_did_not_quit_and_did_not_move_anything`
— the *"did not quit"* half cannot fail. The unmapped `z` is the
**second-to-last** keystroke, so if `z` quit, the loop would return at `z`
instead of at `q` and every recorded field would be byte-identical. The mapping
half is genuinely covered by `test_controls.py` and `test_loop.py`, so this is a
hollow assertion rather than a hole. Moving the `z` earlier in `KEYSTROKES`
would fix it.

### 4.7 A narrow blind spot in GHOST-4, recorded rather than raised

All three CIRCUIT player positions sit on row 7, so a ghost that read **only**
the player's row would survive those two tests. It is still killed by
`::test_three_player_positions_on_a_real_generated_maze`, whose players are
scattered across a real maze, and by the seed-change guard. **Not a defect** —
worth knowing if anyone edits those boards.

---

## 5. Still unverified — what I could not determine

Listed plainly. Plan §5 says *"I could not determine this without the user"* is
a good answer, and most of these are that answer.

### The three open questions — **none of these is settled**

| | Question | Which way the code currently behaves | Status |
|---|---|---|---|
| **A1** | Does **WIN-5** mean the window vanishes on the final frame, or when the player presses `q`? | **On `q`.** `run_loop` returns only on `q` (`loop.py:89, 144-145`); the last picture stays up, the supervisor then closes the window. The tests carrying WIN-5 say so in their own comments. | **OPEN. With the user, unanswered.** Plan §10.4 records that if the answer is "on the final frame", END-5 and END-6 need reinterpreting too and that needs a *second* answer before anything is implemented. Human check **H2** describes the current behaviour, so if A1 flips, H2 must be re-run. |
| **A2** | What does **START-2**'s *"measured across the grid"* mean? | **Squared Euclidean**, ties by lowest `(row, column)` — `rules.py:165-173`, which names itself as the one expression A2 would change. | **OPEN. With the user, unanswered.** And see §4.4: **the suite cannot tell squared Euclidean from Manhattan**, so this answer, whichever way it goes, needs a test built alongside it. |
| **A3** | What is the exact **status-line** spacing? | **All three strings verbatim, each indented by one column** — `theme.STATUS_TEMPLATES` and `STATUS_INDENT = 1`, `theme.py:285-301`, which records A3 as an assumption and not a ruling. | **OPEN. With the user, unanswered.** STAT-2 and STAT-3 are pinned character-for-character to this reading, so a different answer fails 6–16 tests — which is the good case: the change would be visible. |

**WI-11, which exists only to apply these three answers, is held open. It has
not been run and has not been closed.** Plan §6 round 6 says WI-11 is dispatched
first if it is not a no-op; that decision cannot be made until the answers
arrive.

### The six human checks — **0 of 6 run**

Every one is outstanding. `docs/findings/WI-12-human-check-results.md` holds a
line for each with an empty verdict.

- **H1 (WIN-4)** — *cannot ever be run by an agent.* No controlling tty means no
  window the game was launched from, so there is no reference for the offset.
  The user runs `./check-window-placement`.
- **H2 (WIN-5)**, **H3 (WIN-3)**, **H4 (WIN-2)**, **H5 (SCRN-7)**,
  **H6 (SCRN-3, SCRN-5)** — not run; the user was not reachable from this
  session.

Plan §13's definition of done, item 4 — *"All six human checks have been run by
the user and their answers recorded verbatim"* — **is not met.**

### Things I could not determine

1. **Whether the title bar actually reads *Terminal Game*.** Nothing in the
   project has ever read a real window's title. WIN-3 rests entirely on H3.
2. **Whether 18 pt Menlo is comfortable, whether anything flickers, and whether
   yellow and pink are distinguishable at a glance.** Judgements about a screen.
3. **Whether the status line is cyan, the walls blue, the dots gold.** §4.3 —
   no test asserts a colour, and plan §8 assigns no human check to SCRN-6 at
   all. It is covered only incidentally, by the WI-10 pack's check 6 listing
   *"a status line that is not cyan"* among its failures. **That gap between
   plan §8 and the pack needs the technical lead's ruling**, not mine.
4. **Whether the cursor is hidden in a real game.** §4.2 — the only test that
   claims it cannot fail. The pty scripted game does enter the real `session()`,
   so an assertion is cheap to add; I did not add it, because adding a test to
   a work item whose brief is to *report* on the suite is a change the technical
   lead should authorise.
5. **Whether anything typed is echoed into the maze.** §4.4 — nothing
   demonstrates it. The pty probe already drains the master into a `drained`
   list and throws it away; asserting that `b"z"` never appears in it is close
   to free.
6. **Whether the known screen-layout fault recurs.** `could not read the screen
   layout` was seen once by WI-10 and has never been reproduced on demand. It
   did not appear in either of this run's two real-window stages. A second
   sighting would be worth a great deal; absence of one proves nothing.
7. **Whether WIN-3's title recipe survives another macOS version.** It was
   measured on macOS 26.6.2 only, and depends on Terminal's per-profile title
   settings.

### Contradictions found in the plan or the architecture

1. **`ARCHITECTURE.md:642` claims CTRL-5's echo half is *"measured: `noecho` set
   in `Screen.__enter__`"*.** It is wrong twice over: **`Screen.__enter__` does
   not exist** — `termgame/screen.py` uses a `session()` context manager — and
   nothing is measured, since no test in the suite contains the string "echo".
   `IMPLEMENTATION_PLAN.md:1151`'s *"echo is off"* inherits the same claim.
2. **`IMPLEMENTATION_PLAN.md` §11 credits START-2 to an *"exhaustive recount"*.**
   The recount is real and it is exhaustive, but §4.4 shows it is blind to the
   very thing assumption A2 is about.
3. **`IMPLEMENTATION_PLAN.md` §11 credits SCRN-6 to *"unit on the status-line
   style"*.** There is such a unit test and it is sound about the *style*; the
   requirement is about the *colour*, and nothing asserts it. §8 then assigns
   SCRN-6 no human check either.
4. **`IMPLEMENTATION_PLAN.md` §11 credits SCRN-7's cursor clause to *"cursor
   hidden"*.** §4.2 — the test that claims it cannot fail.

---

## 6. Deviations needing a ruling

1. **The brief says "walk the user through all six human checks and record their
   answers, verbatim". I could not.** The user is not reachable from this
   session. I delivered the answer sheet with a line for each of H1–H6 and every
   verdict visibly empty, which is the achievable part. The brief's *"done
   when"* is met on its literal terms; the checks themselves are outstanding.
2. **I ran `./verify --only corner` as well as the default three stages.** The
   brief asks for "the verification command"; `--corner` is opt-in and opens a
   real window. I judged it worth running because plan §12 names the
   bottom-right cell as a failure that surfaces late and only in front of the
   user, and because it turned out to be the only real-window evidence for
   WIN-2's size. Censuses were taken either side and reconcile. **If the lead
   would rather agents did not run `--corner`, say so and I will record it as a
   rule.**
3. **Two of the five audit sweeps ran mutation checks on their own initiative**,
   in throwaway copies under the scratchpad; the worktree was verified unchanged
   and nothing was committed from them. **Plan §2.7 forbids mutation sweeps and
   I did not ask for them.** I am reporting the fact rather than adopting the
   practice: no `MUTATE` line appears in the progress log, my report's section 5
   reads `not applicable — not part of this workflow`, and where I have quoted
   such a result above I have said so and have separately confirmed the finding
   by reading or by measurement.
4. **I added no tests and fixed nothing.** Four of the findings in §4 are cheap
   to fix and I have said where. **This work item's brief is to report on the
   suite, not to change it**, and a gate that edits what it is gating is not a
   gate. Each fix is the lead's to dispatch.

---

## 7. Suite state, per branch

| Branch | Command | Result |
|---|---|---|
| `wi-12-final-gate` | `/usr/bin/python3 -m unittest discover -s tests` | `Ran 749 tests in 12.673s` · `OK (skipped=2)` |

This work item adds no code and no tests, so the branch's counts are `main`'s
counts. The two skips are `tests/test_launch_smoke.py::LaunchSmokeTest`, skipped
for want of a controlling tty.

## 8. Mutation checks

`not applicable — not part of this workflow`
