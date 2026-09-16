# Terminal Game — every requirement, and what pins it

> ## ⚠ THIS IS THE FIRST OF TWO LANDINGS, AND IT IS DELIBERATELY INCOMPLETE
>
> Every one of the 49 requirement codes has a row below, so nothing is
> missing — but **three rows are knowingly unfinished**, because the work
> items that close them have not landed:
>
> | Row | What is missing | Closed by |
> | --- | --- | --- |
> | **GAME-1** | the assembled game, played from one command | **WI-18** |
> | **START-5** | *"the moment the **window** opens"* — the session half is pinned, the window half is not | **WI-18** |
> | **A1, A4, A10** against WIN-3, WIN-2 and SCRN-3 | the three answers only a person can give | **WI-21** |
>
> **A second landing completes this same file in place.** There is one
> traceability document, not two; when this notice is gone, the sweep is
> finished. Until then, do not read an unfinished row as a covered one.

**Swept by:** DEV-C, run 6.
**Against:** `main` with M0–M3 landed, plus WI-19 (the scripted game).
Not yet landed: **WI-18**, **WI-21**, **WI-22**.
**Covers:** all 49 requirement codes in `docs/FUNCTIONAL_REQUIREMENTS.md`.
**Checked automatically by:** `tests/test_spec_sweep.py`, which fails if a
code is missing from this document, appears twice, or is not in the
specification — and which also checks that every test and every document
this file names actually exists.

**Read by a fresh pair of eyes, on purpose.** Amendment 4 kept this item out
of DEV-A's lane because *a sweep is worth least when the author checks their
own coverage*. So the question asked of every row was not "is there a test
somewhere near this" but **"which named test fails if this requirement stops
being true?"** Where the answer is "none", the row says so.

---

## What the columns mean

**Pinned** — a named test asserts the *consequence* the requirement
describes. If the requirement stops being true, that test goes red.

**Pinned, caveated** — pinned as far as a machine can, under a named
assumption that a person has not yet confirmed. The assumption is named.

**Needs a human** — no test can settle it. A named check must look at it.

**Not yet** — the work item that would pin it has not landed. WI-18, WI-19,
WI-21 and WI-22 are still ahead, so some rows are honestly incomplete and
say which item closes them. **These are findings, not ticks.**

**Observed** — additionally seen happening on a real screen, in a named
finding. Amendment 2's *"proved by a double is not proved"* stands for
positive behaviours, and four rows here have that stronger evidence. It is
marked where it exists because it is worth more than a test.

### How to read a citation

Test citations are `file::Class` or `file::Class::method`, relative to the
repository root. Document citations are a backticked path under `docs/`.

**A backtick is a claim that the thing exists**, and
`tests/test_spec_sweep.py` enforces it: every cited file, class and method
is checked, every cited method must be named `test_*`, and every cited
document must be on disk. So a test renamed out from under this document
fails the suite rather than quietly turning a row into a lie. A file that
does not exist yet — the WI-21 answers, below — is named in plain text
instead.

### What a negative can and cannot be

Amendment 6 settled this and the sweep follows it: **a negative about the
user's environment cannot be established by running the thing that might
cause it.** Two honest routes, and no third — make the route structurally
**absent** and show the absence, or **ask the person**. An absence covers
every run on every machine; an observation covers one run on one. Where a
row below rests on a negative, it says which of the two it rests on.

---

## 1. The game

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| GAME-1 | WI-6, WI-18 | `tests/test_game_state.py::GameStateTests::test_a_state_carries_the_maze_the_dots_the_actors_and_the_score` — one maze, one dot field, one player square, one ghost square, and no way to have two of anything. Dots on the corridors: `tests/test_opening_position.py::OpeningPositionTests::test_there_is_a_dot_on_every_corridor_square_but_the_players`. A whole game really played: `tests/test_scripted_game.py::AWholeSeededGame::test_the_game_is_won` | **Pinned** for the furniture, and now for a whole game played headless. **Not yet** for the game assembled behind a window and run from one command — **WI-18** |
| GAME-2 | WI-11 | `tests/test_turn_resolver.py::WinningTests::test_eating_the_last_dot_wins_the_game` and `tests/test_turn_resolver.py::CollisionTests::test_walking_into_the_ghost_loses_the_game`; both endings again in a whole game — `tests/test_scripted_game.py::TheWinPath::test_playing_the_script_clears_the_maze` and `tests/test_scripted_game.py::TheLossPath::test_the_player_walking_into_the_ghost_loses_the_game` | **Pinned** |
| GAME-3 | WI-15 | `tests/test_session.py::ThreeStatesAndNoMore::test_there_are_exactly_three_phases` and `tests/test_session.py::ThreeStatesAndNoMore::test_there_is_no_restart_edge` | **Pinned** |

**GAME-1 is one of the two codes no test names anywhere in the suite** (the
other is SCRN-1). Both turned out to be pinned by tests that do not cite
them, which is why a sweep reads the tests rather than grepping for codes.

---

## 2. The window

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| WIN-1 | WI-3 | `tests/test_window_owner.py::TheWindowItAsksForTest::test_opening_twice_creates_one_window` | **Pinned** |
| WIN-2 | WI-2, WI-3 | 40 × 30 from the metrics: `tests/test_grid_surface.py::HowManyPixelsFortyByThirtyNeeds::test_the_measured_metrics_give_a_four_hundred_by_five_seventy_window`. Black: `tests/test_window_owner.py::TheWindowItAsksForTest::test_it_is_black_and_cannot_be_resized` | **Pinned, caveated — A4.** *"Large enough to read comfortably"* is one font-size constant and no test can judge it. `docs/findings/WI-2-cell-metrics.md` gives the ladder |
| WIN-3 | WI-3 | `tests/test_window_owner.py::TheWindowItAsksForTest::test_it_is_titled_terminal_game`. **Observed** on 8 real windows, title read back `Terminal Game` every time — `docs/findings/WI-16-the-look.md` | **Pinned, caveated — A1.** The test pins what we *ask* for, and the observation is the toolkit reading back its own string. Neither is a person seeing a titlebar. **Needs a human: WI-21** |
| WIN-4 | WI-14 | `tests/test_anchor.py::GivenAnAnchorTheWindowGoesBelowAndToTheRight`, `tests/test_anchor.py::AWindowPastTheEdgeIsBroughtBack` and `tests/test_anchor.py::APointOnASecondDisplayIsNotAPointWeCanUse` | **Pinned, caveated — A2 revised** (amendment 6, approved: anchor on the pointer, which is what the game can see without asking). See C-7 below |
| WIN-5 | WI-15, WI-3 | `tests/test_window_owner.py::EndingTheSessionTest::test_the_windows_own_close_button_ends_the_session` and `tests/test_session.py::QuittingIsTheOnlyWayOut::test_reaching_ended_asks_to_be_shut_down_exactly_once` | **Pinned, caveated — A3.** WIN-5 contradicts END-5 and END-6 (C-2); what is pinned is A3's reading |

### WIN-4 rests on two things, and one of them is not the one A2 named

**Contradiction C-7, now in the plan.** A2 treated Accessibility permission
as the obstacle. There is a second one underneath it that **no permission
grant would clear**. Measured (`docs/findings/WI-14-anchor-query.md`): the
pointer reads `(-175, -448)` while `winfo_screenwidth/height` *and*
`winfo_vrootwidth/height` all report `1512 × 982` — the primary display
alone; `maxsize()` knows the desktop is `5120 × 2422` but gives no origin.
The pointer is on a second display whose rectangle Tk 8.5 will not give.

**So WIN-4 is satisfied today only by its fallback, and display geometry is
the reason, not permission.** If the user granted Accessibility tomorrow the
window would land in exactly the same place. Section 13 now warns them of
that before they look, which matters: without it the question would invite
them to grant a permission for nothing.

**Did the query ask the user for anything? No, on two separate grounds.**
The privileged route is **structurally absent** from the code — not guarded,
absent — which covers every run on every machine. And **proof by timing**:
the query returned in 115.0 ms and 118.6 ms, and a permission dialog blocks
its caller until a person answers, so those calls waited for nobody. The
absence carries the general claim; the timing corroborates those two runs.
**Neither was obtained by running something that might prompt and watching.**

---

## 3. What is on the screen

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| SCRN-1 | WI-12, WI-13 | `tests/test_frame.py::RenderingTheSpecimenPicture::test_the_whole_picture_renders_character_for_character`; row 29 is the status line's and only the status line's — `tests/test_frame_composer.py::RowTwentyNineIsNotThisItems::test_nothing_the_composer_draws_reaches_row_twenty_nine` and `tests/test_status_line.py::TheRowAsAValue::test_the_status_row_is_the_bottom_row` | **Pinned** |
| SCRN-2 | WI-10 | `tests/test_house_rules.py::ThisRepositoryObeysTheRules::test_rule_3_nothing_draws_an_image`, backed by `tests/test_grid_surface.py::TheRuleThatThereAreNoImages` which shows the recording canvas would notice one. **Observed**: canvas item kinds were `["text"]` on all 8 real windows — `docs/findings/WI-16-the-look.md` | **Pinned and observed, caveated — caution C5.** Under candidate 2 this is a *rule* we enforce, not a property of the medium, which is exactly why the observation is worth having |
| SCRN-3 | WI-8 | `tests/test_wall_glyphs.py::TheSixteenCombinations` — all sixteen, each named; `tests/test_wall_glyphs.py::TheSpecimenPicture::test_the_resolver_reproduces_the_specimen_s_walls_exactly` | **Pinned** for *which characters*. **Needs a human — A10** for *whether the strokes meet*. This sweep does not close it; see below |
| SCRN-4 | WI-12 | `tests/test_frame_composer.py::TheDots::test_a_corridor_square_with_a_dot_shows_the_dot` and `tests/test_frame_composer.py::TheDots::test_the_dot_is_dim_gold` | **Pinned** |
| SCRN-5 | WI-12 | `tests/test_frame_composer.py::TheActorsAreThreeColumnMotifs::test_the_two_motifs_differ_in_shape_as_well_as_colour` and `tests/test_the_look.py::TheColoursReachTheSurfaceUnchanged::test_the_five_visible_colours_are_all_different_on_the_surface` | **Pinned** |
| SCRN-6 | WI-13 | `tests/test_status_line.py::TheRowAsAValue::test_the_named_status_colour_is_the_one_the_requirements_name` | **Pinned** |
| SCRN-7 | WI-2, WI-18 | No caret: `tests/test_window_manners.py::NoTextCaretCanExistTest::test_no_module_constructs_a_widget_that_has_a_caret`. No flicker, structurally: `tests/test_grid_surface.py::RepaintingIsADifference::test_repainting_an_unchanged_frame_costs_no_drawing_at_all` and `tests/test_grid_surface.py::RepaintingIsADifference::test_a_move_costs_five_cells_and_not_the_whole_twelve_hundred` | **Pinned** for the caret and for *there is no clear-then-redraw*. **Needs a human** for *does it flicker*, and `docs/findings/WI-16-the-look.md` is where that was looked at |

### SCRN-3: assumption A10, and this sweep explicitly does not close it

**Whether the strokes of adjacent double-line glyphs actually meet on screen
is not established, and is recorded nowhere as established.**

The spacing is settled by measurement — all 113 glyphs the picture uses share
one advance in Menlo at 14, 16, 18 and 20pt, with a control showing glyphs
Menlo lacks fall back to visibly different advances
(`docs/findings/WI-2-cell-metrics.md`). So the characters line up. **Equal
advance proves the cells line up; it does not prove the strokes touch.**
Whether the ink joins is about glyph shapes, not metrics.

Amendment 6 made this **assumption A10** and the user's fifth question,
noting that four developers had each declined to convert the measurement
into an answer. **This sweep is the fifth reader to decline, and does so
deliberately** — a traceability document turning an open question into a
tick is the exact failure this item exists to prevent.

**And a sting the sweep must carry forward:** the specimen picture in the
requirements **contains no crossing glyph at all** — measured over the whole
picture in `docs/findings/WI-8-glyph-census.md`, which found 15 of the 16
neighbour combinations there and not the crossing. So checking SCRN-3
against the specimen, or against a game screen, may never put a crossing in
front of anybody. **WI-16's joinery view is the only thing on this project
that has ever rendered one**, and it is what the question should be asked
against. Crossings are not rare in play: 61 of them across the 200 shared
seeds, in 55 of those mazes.

---

## 4. The maze

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| MAZE-1 | WI-5, WI-12 | `tests/test_maze_generator.py::GeneratedMazeTests::test_the_grid_is_nineteen_across_and_twenty_nine_deep`; the 37 columns and the 3-column margin: `tests/test_frame_composer.py::WhereASquareIsDrawn::test_nineteen_squares_fill_exactly_the_thirty_seven_columns` and `tests/test_frame_composer.py::TheRightHandMargin::test_every_maze_row_is_forty_cells_with_three_blank_at_the_end` | **Pinned.** Contradiction C-1 resolved as 37 + 3 |
| MAZE-2 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_corridors_run_only_north_south_and_east_west` and `tests/test_maze_generator.py::GeneratedMazeTests::test_no_corridor_is_two_squares_wide` | **Pinned**, over 200 seeds |
| MAZE-3 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_the_border_ring_is_solid_on_all_four_sides` | **Pinned**, over 200 seeds |
| MAZE-4 | WI-5 | `tests/test_maze_generator.py::RandomnessTests::test_two_hundred_different_seeds_give_two_hundred_different_mazes` and `tests/test_maze_generator.py::RandomnessTests::test_the_generator_never_reaches_for_the_global_random_source`; reproducibility across hash seeds by `tests/test_scripted_game.py::TheGameReplaysIdentically::test_a_seeded_game_is_the_same_under_a_different_hash_seed` | **Pinned** |
| MAZE-5 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_no_corridor_square_has_fewer_than_two_corridor_neighbours` | **Pinned**, over 200 seeds — caution C4's first half |
| MAZE-6 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_a_flood_fill_from_any_corridor_square_reaches_every_other` | **Pinned**, over 200 seeds — caution C4's second half |

---

## 5. Starting a game

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| START-1 | WI-6 | `tests/test_opening_position.py::PlayerStartTests::test_no_corridor_square_is_nearer_the_middle_than_the_players` | **Pinned** |
| START-2 | WI-6 | `tests/test_opening_position.py::GhostStartTests::test_the_ghost_starts_furthest_across_the_grid_not_along_the_corridors` and `tests/test_opening_position.py::GhostStartTests::test_no_corridor_square_is_further_from_the_player_than_the_ghosts` | **Pinned.** *Across the grid*, not along the corridors — the test is named for the distinction |
| START-3 | WI-6 | `tests/test_opening_position.py::OpeningPositionTests::test_there_is_a_dot_on_every_corridor_square_but_the_players` | **Pinned** |
| START-4 | WI-6 | `tests/test_opening_position.py::OpeningPositionTests::test_the_score_starts_at_zero_and_no_ending_has_happened` | **Pinned** |
| START-5 | WI-15, WI-18 | `tests/test_session.py::TheGameIsUnderWayWhenTheWindowOpens::test_the_ghost_moves_without_any_key_being_pressed` and `tests/test_session.py::TheGameIsUnderWayWhenTheWindowOpens::test_starting_composes_the_first_picture` | **Pinned** for the session. *The moment the **window** opens* is **not yet** — WI-18 |

---

## 6. Controls

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| CTRL-1 | WI-9, WI-11 | `tests/test_input_translator.py::TheFourArrowKeys` and `tests/test_turn_resolver.py::MovingTests::test_each_arrow_moves_the_player_one_square_that_way` | **Pinned** |
| CTRL-2 | WI-11 | `tests/test_turn_resolver.py::MovingTests::test_each_arrow_moves_the_player_one_square_that_way`; nothing but an intent can move the player, and `tests/test_session.py::OnceDecidedNothingMoves::test_a_tick_in_decided_moves_nothing` shows a tick does not | **Pinned** |
| CTRL-3 | WI-11 | `tests/test_turn_resolver.py::MovingIntoAWallTests::test_a_press_towards_a_wall_does_nothing_at_all`. **Observed**: a real `Left` into a wall on a real screen left the player at (9,12) — `docs/findings/WI-17-real-window-manners.md` | **Pinned and observed.** The four squares walked on screen are exactly what the pure Domain predicts for that seed, so the whole WI-9 → WI-15 → WI-11 chain agrees with itself through a real event loop |
| CTRL-4 | WI-9, WI-15 | `tests/test_input_translator.py::TheQuitKey` (both cases) and `tests/test_session.py::QuittingIsTheOnlyWayOut::test_quitting_a_finished_game_reaches_ended`. **Observed**: a real `q` ended a real session at 1.483 s — `docs/findings/WI-17-real-window-manners.md`, and earlier in `docs/findings/WI-4-first-window.md` | **Pinned and observed.** Worth the observation: WI-3's tests passed and its probe passed and **neither ever pressed a key**, and the game would have been unquittable |
| CTRL-5 | WI-9, WI-17 | `tests/test_input_translator.py::EveryOtherKeyIsDiscarded`, `tests/test_input_translator.py::NothingIsEchoedAnywhere` and `tests/test_window_manners.py::AKeyReachingTheSessionTest::test_an_unmapped_key_asks_the_session_for_nothing_at_all` | **Pinned** |

---

## 7. The ghost

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| GHOST-1 | WI-3, WI-15 | `tests/test_cadence.py::GhostCadenceTest::test_the_cadence_is_seven_ticks_a_second` and `tests/test_window_owner.py::TheTickReachingTheCollaboratorTest` | **Pinned** |
| GHOST-2 | WI-7 | `tests/test_ghost.py::CarryingStraightOn::test_at_a_crossroads_it_still_goes_straight_rather_than_choosing` | **Pinned.** The crossroads case is the one that matters: a junction is not a reason to choose |
| GHOST-3 | WI-7 | `tests/test_ghost.py::ChoosingWhereItCannotCarryOn::test_at_a_tee_it_never_goes_back_the_way_it_came`, `tests/test_ghost.py::ChoosingWhereItCannotCarryOn::test_over_many_draws_the_two_arms_come_up_about_equally`, `tests/test_ghost.py::TurningBackOnlyAsALastResort::test_in_a_dead_end_it_reverses` | **Pinned** |
| GHOST-4 | WI-7 | `tests/test_ghost.py::TheGhostTakesNoNoticeOfThePlayer::test_the_signature_carries_no_player` | **Pinned**, and structurally: the player is *absent* from the signature, not unused |

---

## 8. Dots and score

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| SCORE-1 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_moving_onto_a_dotted_square_eats_it_and_scores_exactly_one`, with permanence from `tests/test_dot_field.py` | **Pinned** |
| SCORE-2 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_each_dot_eaten_adds_one_so_the_score_is_the_dots_taken` | **Pinned** |
| SCORE-3 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_moving_onto_a_square_whose_dot_has_gone_scores_nothing` | **Pinned** |
| SCORE-4 | WI-7, WI-12 | `tests/test_turn_resolver.py::TheGhostsTurnTests::test_the_ghost_neither_eats_a_dot_nor_scores_a_point` and `tests/test_frame_composer.py::TheDots::test_a_dot_under_the_ghost_is_still_in_the_dot_field_afterwards` | **Pinned** on both halves — the rule *and* the drawing |
| SCORE-5 | WI-6, WI-13 | `tests/test_game_state.py::ScoreTests::test_every_operation_a_score_offers_leaves_it_no_smaller`; shown in the line by `tests/test_status_line.py::TheEndingIsChosenByTheOutcome::test_the_same_score_reads_three_different_ways` | **Pinned.** *Never goes down* is pinned structurally: the type offers no operation that could lower it |

---

## 9. How a game ends

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| END-1 | WI-11 | `tests/test_turn_resolver.py::CollisionTests::test_walking_into_the_ghost_loses_the_game` **and** `tests/test_turn_resolver.py::CollisionTests::test_the_ghost_walking_into_the_player_loses_the_game` — the requirement says *whether the player walked into the ghost or the ghost walked into the player*, and there is a test for each | **Pinned** |
| END-2 | WI-11 | `tests/test_turn_resolver.py::WinningTests::test_eating_the_last_dot_wins_the_game` | **Pinned** |
| END-3 | WI-11 | `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_eating_the_last_dot_on_the_ghosts_square_is_a_loss`, with `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_the_winning_condition_really_did_hold_in_that_same_turn` showing the case is not vacuous. And again in a whole game: `tests/test_scripted_game.py::EndThreeInAWholeGame::test_the_last_dot_on_the_ghosts_square_is_caught_and_not_cleared`, with `tests/test_scripted_game.py::EndThreeInAWholeGame::test_the_dot_field_really_did_empty_on_that_same_turn` | **Pinned directly and twice**, at the resolver and in a whole game, which is the strongest ordinary coverage the plan said was available. The non-vacuity tests are the ones that matter: without them the precedence test could pass because the win condition never held. **A8** governs whether the dot still scores; `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_the_dot_is_still_eaten_and_still_scores_on_the_losing_turn` pins the reading we took |
| END-4 | WI-12 | `tests/test_frame_composer.py::TheDrawOrder::test_the_final_picture_of_a_loss_shows_the_ghost_over_the_player` and `tests/test_scripted_game.py::TheLossPath::test_the_final_picture_shows_the_ghost_and_not_the_player` | **Pinned** |
| END-5 | WI-15 | `tests/test_session.py::OnceDecidedNothingMoves::test_the_picture_the_player_is_looking_at_does_not_change`, with the ghost and the arrows pinned separately in the same class; in a whole game, `tests/test_scripted_game.py::TheWinPath::test_the_last_picture_stays_on_screen` | **Pinned, caveated — A3** (C-2) |
| END-6 | WI-15 | `tests/test_session.py::QuittingIsTheOnlyWayOut::test_quitting_a_finished_game_reaches_ended` and `tests/test_session.py::OnceDecidedNothingMoves::test_an_arrow_in_decided_changes_nothing` — `q` works and nothing else does; in a whole game, `tests/test_scripted_game.py::TheWinPath::test_q_is_the_only_way_out_and_it_works` | **Pinned, caveated — A3** |

---

## 10. The status line

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| STAT-1 | WI-13 | `tests/test_status_line.py::TheRowAsAValue::test_the_status_row_is_the_bottom_row`, and *nothing else on it ever* from `tests/test_frame_composer.py::RowTwentyNineIsNotThisItems::test_the_composer_contains_no_status_line_literal` | **Pinned** |
| STAT-2 | WI-13 | `tests/test_status_line.py::TheThreeLiterals::test_playing_at_score_zero_is_the_stat_2_literal` | **Pinned, caveated — A7** (C-3: the literal disagrees with the specimen picture by one leading space; the literal is normative) |
| STAT-3 | WI-13 | `tests/test_status_line.py::TheThreeLiterals::test_a_loss_at_score_thirty_seven_is_the_stat_3_loss_literal` and `tests/test_status_line.py::TheThreeLiterals::test_a_win_at_score_two_hundred_and_seventy_four_is_the_stat_3_win_literal`. What a *real* won game shows: `tests/test_scripted_game.py::AWholeSeededGame::test_the_status_line_reads_cleared_with_the_score_it_reached` | **Pinned as formatting, caveated — A7 and A9** |

### A9 is honoured, and it was checked rather than assumed

**A whole game is worth 259–271 points, so `CLEARED  score 274` is a
formatting exemplar and not a score any game reached.** Every use of 274 in
the tree was inspected: it appears in `tests/test_status_line.py` (as an
input to the formatter, with a comment saying in as many words that it is not
reachable), in `terminal_game/presentation/status_line.py`'s docstring
saying the same, in `tests/test_frame_composer.py` as a status row to place,
and in `tests/test_game_state.py` as one of several point values.

**Nothing anywhere asserts 274 as an achieved score**, and no row of this
sweep claims it. WI-19 went further and pinned the negative:
`tests/test_scripted_game.py::AWholeSeededGame::test_the_score_is_not_the_number_in_the_specifications_example`
and `tests/test_scripted_game.py::AWholeSeededGame::test_the_score_is_in_the_band_a_whole_game_is_worth`.

---

## 11. The count

| | |
| --- | --- |
| Codes in `docs/FUNCTIONAL_REQUIREMENTS.md` | **49** |
| Rows in this sweep | **49**, each code once — checked by `tests/test_spec_sweep.py` |
| Pinned outright | **35** |
| Pinned but caveated by a named assumption | **8** — WIN-2 (A4), WIN-3 (A1), WIN-4 (A2 revised), WIN-5 (A3), SCRN-2 (C5), END-5 (A3), END-6 (A3), STAT-2 (A7) |
| Pinned as formatting only | **1** — STAT-3 (A7, A9) |
| Pinned in part, with a half still needing a human | **2** — SCRN-3 (A10, do the strokes meet), SCRN-7 (does it flicker) |
| Pinned in part, with a half awaiting a work item | **2** — GAME-1 and START-5, both awaiting **WI-18** |
| Additionally **observed on a real screen** | **4** — WIN-3, SCRN-2, CTRL-3, and CTRL-4's real `q` |
| **With no test and no named human check at all** | **0** |

35 + 8 + 1 + 2 + 2 = 48; WIN-3 is counted once although it is both caveated
and needs a human, so the caveated column carries it. The "observed" count
overlaps the others and is not part of that sum.

---

## 12. Findings — the things this sweep turned up

**1. Two requirement codes are named nowhere in the suite: GAME-1 and
SCRN-1.** Both are in fact pinned, by tests that do not cite them. No action
is needed on the code; it is recorded because it shows why a sweep has to
read the tests rather than grep for codes, and because anyone maintaining
those two requirements has no way to find their tests by searching.

**2. WIN-4's real obstacle is not A2.** The plan treats Accessibility
permission as the only thing between us and a real anchor. Measurement says
there is a second obstacle — multi-display geometry Tk 8.5 will not report —
that no permission grant would clear. `docs/findings/WI-14-anchor-query.md`.

**3. Two requirements are half-pinned because WI-18 has not landed**:
GAME-1's assembly and START-5's *"the moment the window opens"*. Both are
expected and both close at WI-18. They are listed here rather than ticked.

**4. START-2 holds, and a player would still notice something.** The ghost
is always the furthest corridor square from the player, so START-2 is
pinned. But the furthest square is always a corner, all four corners are
always corridor, and the tie is broken deterministically — so **the ghost
always starts in the left-hand column, and 200 distinct mazes produced only
two distinct opening positions** (`docs/findings/WI-6-start-squares.md`).
Nothing in the specification is broken. It is recorded because a sweep that
only asked "is START-2 pinned?" would have missed it, and because it is the
kind of thing a player sees in three games.

**5. Nothing in the tree is a requirement ticked without evidence.** Every
one of the 49 rows names something. That is the answer to the question this
item exists to ask, and it is a better answer than I expected to be able to
give.

**6. Four rows have evidence stronger than a test**, because somebody ran
the real thing and wrote down what happened: WIN-3, SCRN-2, CTRL-3 and
CTRL-4. Every one of those came from a real-medium exercise that the plan
only started demanding after amendment 2, and **SCRN-2's is the one that
matters most** — under candidate 2 "no images" is a convention we enforce
rather than a property of the medium, so seeing `["text"]` and nothing else
on eight real windows is worth more than the guard that forbids anything
else.

---

## 13. What is open, and is not closed by this document

None of these is settled, and this sweep does not settle any of them.

| Open | Where it lands |
| --- | --- |
| **A1** — does the titlebar read exactly *Terminal Game* to a person? | WI-21, user's question 1 |
| **A2 revised** — the pointer as the anchor. **Approved** by the lead in amendment 6, and **still an assumption the user may overturn** | WI-14 alone; one constant |
| **A3** — WIN-5 against END-5 and END-6 | user's question 2; WI-15 alone |
| **A4** — is Menlo 16pt in a 400 × 570 window comfortable? | WI-21, user's question 3 |
| **A7** — the status-line literals against the specimen picture | decided here, flagged not re-opened; WI-13 alone |
| **A8** — does the dot under the player still score on the losing turn? | user's question 4; WI-11 alone |
| **A10** — do the blue walls' strokes actually meet? | user's question 5; ask it against **WI-16's joinery view**, not a game screen |
| **C-7** — WIN-4's second obstacle is display geometry, and no permission clears it | recorded; the user is warned before they look |
| **The ghost's start-corner tie-break** — the ghost always starts in the left-hand column, so 200 distinct mazes gave only **two** distinct opening positions | `docs/findings/WI-6-start-squares.md`. Nothing in the specification is broken; a player would notice. Confined to `ghost_start_square` |
| **A9** — 274 as a format, not a score | settled by measurement; honoured above, and no row claims it |

---

## 14. What the second landing must still do

This section, and the notice at the top of the file, are the two things the
second landing deletes.

- **Finish GAME-1 and START-5** once WI-18 lands: the game assembled behind
  a window and started from one command, and *"the moment the window
  opens"*.
- **Re-check every row against the wired game** rather than against the
  parts. A row that is true of a component and false of the assembly is the
  thing a second landing exists to catch.
- **Cite the WI-21 human answers** — docs/findings/WI-21-human-answers.md,
  named without backticks here because it does not exist yet — and carry
  **A1**, **A4** and **A10** from open to answered, or record them as still
  open, which is an outcome and not a failure.
- **Keep the four caveated rows the plan names** — WIN-2, WIN-4, WIN-5,
  SCRN-2 — with their assumption and their supporting finding.
- **Remove the incompleteness notice at the top**, and only then. While it
  is there a reader knows what they are holding; removing it early is the
  one way this document can mislead rather than merely be unhelpful.
