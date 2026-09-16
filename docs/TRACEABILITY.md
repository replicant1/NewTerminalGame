# Terminal Game — every requirement, and what pins it

**This document is complete.** All 49 requirement codes have a row, every row
names the evidence behind it, and no row is waiting on a work item. The
"deliberately incomplete" notice that stood here between the two landings has
been removed, which is the signal that the sweep is finished.

**Complete does not mean everything is settled.** Eight questions are open and
every one of them is recorded as open, with what a person has to do to close
it, in section 13. **A gap written down is a different thing from a gap nobody
noticed**, and telling the two apart is the whole purpose of this document.

**Swept by:** DEV-C, run 6, in two landings into this one file —
WI-20a created it, **WI-20b completed it in place**.
**Against:** `main` with **every work item of the run landed**: M0–M3, plus
WI-18 (the game assembled behind a window), WI-19 (a whole game played
headless), WI-21 (the questions for a human) and WI-22 (the state-to-frame
join).
**Covers:** all 49 requirement codes in `docs/FUNCTIONAL_REQUIREMENTS.md`.
**Checked automatically by:** `tests/test_spec_sweep.py`, which fails if a
code is missing from this document, appears twice, or is not in the
specification; if a test or document this file names does not exist; if a row
claims 274 as a score that was reached; if the CTRL-5 row is quietly ticked;
if a row claims test coverage for something only a person has seen work; or if
any of the open questions below stops being recorded as open.

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

**Pinned in part, and a human is needed for the rest** — half the requirement
is a consequence a test can assert and half of it is something only an eye can
judge. Both halves are named.

**Honoured in part, with a named gap** — one row is in this state and only one.
CTRL-5 is honoured for letters and **not** for modified arrows, deliberately,
under assumption A11. It does not carry a tick.

**Covered by observation, not by test** *(amendment 9)* — the suite is
forbidden from constructing a toolkit interpreter, so two functions in the
Shell cannot be reached by any test at all. The honest answer is not to pretend
otherwise but to label it: the observation is recorded in `docs/findings/` and
cited, and **no row claims test coverage for it.** Section 3a is where those two
functions are, declared rather than hidden by the developer who wrote them.

**Observed** — additionally seen happening on a real screen, in a named
finding. Amendment 2's *"proved by a double is not proved"* stands for
positive behaviours. **Seventeen rows now carry it**, against four at the first
landing, because WI-17, WI-18 and WI-21 put the assembled game on a screen.
It is marked where it exists because it is worth more than a test.

### How to read a citation

Test citations are `file::Class` or `file::Class::method`, relative to the
repository root. Document citations are a backticked path under `docs/`.

**A backtick is a claim that the thing exists**, and
`tests/test_spec_sweep.py` enforces it: every cited file, class and method
is checked, every cited method must be named `test_*`, and every cited
document must be on disk. So a test renamed out from under this document
fails the suite rather than quietly turning a row into a lie.

That mechanism did its job between the two landings, and it is worth recording
how. WI-20a cited a test by path; **WI-18 then moved it** — same class name,
same method name — from `tests/test_window_manners.py` into `tests/test_game.py`,
because the throwaway dispatch it covered had been replaced by the production
collaborator. The completeness check went red on the citation rather than on
the behaviour. DEV-A updated the one citation line and added WI-18 to the row,
**rather than keeping a duplicate test alive purely to satisfy a citation**,
which is the right way round. Nothing the sweep claims changed, and CTRL-5 is
still pinned by three tests.

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
| GAME-1 | WI-6, WI-18, WI-19 | The furniture: `tests/test_game_state.py::GameStateTests::test_a_state_carries_the_maze_the_dots_the_actors_and_the_score` — one maze, one dot field, one player square, one ghost square, and no way to have two of anything. Dots on the corridors: `tests/test_opening_position.py::OpeningPositionTests::test_there_is_a_dot_on_every_corridor_square_but_the_players`. A whole game really played: `tests/test_scripted_game.py::AWholeSeededGame::test_the_game_is_won`. **Assembled and run from one command:** `tests/test_game.py::TheEntryPointAssemblesTheRealThingTest::test_it_joins_a_real_session_over_a_real_maze` and `tests/test_game.py::TheSingleCommandTest::test_the_package_is_runnable_and_runs_the_wiring`. **Observed** on a real screen — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed.** The half WI-20a left open is closed: the game is assembled behind a window and started by `/usr/bin/python3 -m terminal_game` |
| GAME-2 | WI-11 | `tests/test_turn_resolver.py::WinningTests::test_eating_the_last_dot_wins_the_game` and `tests/test_turn_resolver.py::CollisionTests::test_walking_into_the_ghost_loses_the_game`; both endings again in a whole game — `tests/test_scripted_game.py::TheWinPath::test_playing_the_script_clears_the_maze` and `tests/test_scripted_game.py::TheLossPath::test_the_player_walking_into_the_ghost_loses_the_game` | **Pinned.** Headless only — see the finding below the table |
| GAME-3 | WI-15 | `tests/test_session.py::ThreeStatesAndNoMore::test_there_are_exactly_three_phases` and `tests/test_session.py::ThreeStatesAndNoMore::test_there_is_no_restart_edge` | **Pinned** |

**GAME-1 is one of the two codes no test names anywhere in the suite** (the
other is SCRN-1). Both turned out to be pinned by tests that do not cite
them, which is why a sweep reads the tests rather than grepping for codes.
See finding 1 in section 12: nothing needs fixing in the code, but anybody
maintaining those two cannot find their tests by searching.

### Nobody has played a whole game on a screen

**A game reaching either ending exists only headless, in the suite.** Every
on-screen run this project has made ended `UNDECIDED`:

| Where a whole game exists | Where it does not |
| --- | --- |
| `tests/test_scripted_game.py::AWholeSeededGame::test_the_game_is_won` — a seeded game played to a win, headless | `docs/findings/WI-18-the-game-on-screen.md` — **two dots eaten of 259–271**, ended by `q` |
| `tests/test_scripted_game.py::TheLossPath::test_the_player_walking_into_the_ghost_loses_the_game` | `docs/findings/WI-17-real-window-manners.md` — four squares walked, ended by `q` |

GAME-2 and END-1 to END-6 are pinned by those headless games and are not
diminished by this. What is missing is one person playing one game to an
ending, and **it is the last thing on the list in section 13** because it is
the only artefact no agent may run: the finished game is unbounded by design,
`q` is the only way out of it, and launched by an agent nobody is there to
press it.

---

## 2. The window

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| WIN-1 | WI-3, WI-18 | `tests/test_window_owner.py::TheWindowItAsksForTest::test_opening_twice_creates_one_window`; the assembly asks for the game's own window and not another — `tests/test_game.py::TheEntryPointAssemblesTheRealThingTest::test_the_window_it_will_ask_for_is_the_games_own`. **Observed** 30 times over the run, every one reaped | **Pinned and observed** |
| WIN-2 | WI-2, WI-3 | 40 × 30 from the metrics: `tests/test_grid_surface.py::HowManyPixelsFortyByThirtyNeeds::test_the_measured_metrics_give_a_four_hundred_by_five_seventy_window`. Black: `tests/test_window_owner.py::TheWindowItAsksForTest::test_it_is_black_and_cannot_be_resized`. **Observed**: 400 × 570 measured back off real windows in `docs/findings/WI-4-first-window.md`, `docs/findings/WI-17-real-window-manners.md` and `docs/findings/WI-18-the-game-on-screen.md` | **Pinned, caveated — A4.** *"Large enough to read comfortably"* is one font-size constant and no test can judge it. `docs/findings/WI-2-cell-metrics.md` gives the ladder — 14, 16, 18, 20pt and what each costs in pixels. **The function that takes the measurement has no test at all** — section 3a |
| WIN-3 | WI-3 | `tests/test_window_owner.py::TheWindowItAsksForTest::test_it_is_titled_terminal_game`. **Observed** on 8 windows in `docs/findings/WI-16-the-look.md`, 5 in `docs/findings/WI-17-real-window-manners.md`, 4 in `docs/findings/WI-18-the-game-on-screen.md` and 3 in `docs/findings/WI-3-tk-window-probe.md` — title read back `Terminal Game` every time | **Pinned, caveated — A1.** The test pins what we *ask* for, and the observation is the toolkit reading back its own string. Neither is a person seeing a titlebar. **Needs a human — and five developers in a row have declined to call the read-back an answer** |
| WIN-4 | WI-14 | `tests/test_anchor.py::GivenAnAnchorTheWindowGoesBelowAndToTheRight`, `tests/test_anchor.py::AWindowPastTheEdgeIsBroughtBack` and `tests/test_anchor.py::APointOnASecondDisplayIsNotAPointWeCanUse`. **Observed**: the window opened at the fallback `(120, 120)` on all four real runs, with the query reporting it saw nothing and did not fail — `docs/findings/WI-18-the-game-on-screen.md` | **Satisfied by its fallback, with a known cause — A2 revised and C-7.** Not a gap: the fixed position is certainly visible, which is what WIN-4 asks for. The anchor is the pointer, not a window (amendment 6, approved by the lead, **still the user's to overturn**), and the fallback is taken for a reason **no Accessibility grant would change** — see below |
| WIN-5 | WI-15, WI-3, WI-18 | `tests/test_window_owner.py::EndingTheSessionTest::test_the_windows_own_close_button_ends_the_session`, `tests/test_session.py::QuittingIsTheOnlyWayOut::test_reaching_ended_asks_to_be_shut_down_exactly_once`, and in the assembly `tests/test_game.py::EndingTheGameClosesTheWindowTest::test_q_ends_the_session_and_closes_the_window`. **Observed**: a real `q` ended a real assembled game at 1.488 s and the window was reaped — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned, caveated — A3.** WIN-5 contradicts END-5 and END-6 (C-2); what is pinned is A3's reading |

### WIN-4 rests on two things, and one of them is not the one A2 named

**Contradiction C-7.** A2 treated Accessibility permission as the obstacle.
There is a second one underneath it that **no permission grant would clear**.
Measured (`docs/findings/WI-14-anchor-query.md`): the pointer reads
`(-175, -448)` while `winfo_screenwidth/height` *and* `winfo_vrootwidth/height`
all report `1512 × 982` — the primary display alone; `maxsize()` knows the
desktop is `5120 × 2422` but gives no origin. The pointer is on a second
display whose rectangle Tk 8.5 will not give, so there is nothing to clamp it
into, and an unbounded anchor is correctly treated as nothing seen.

**So WIN-4 is satisfied today only by its fallback, and display geometry is
the reason, not permission.** If the user granted Accessibility tomorrow the
window would land in exactly the same place. WI-21's checklist prints that
warning **before** the placement question, which matters: without it the
behaviour reads as a bug and the obvious reaction is to grant a permission that
would change nothing. **If the user dislikes where it lands, the fix is a
better fallback position, not a permission.**

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
| SCRN-1 | WI-12, WI-13, WI-22 | `tests/test_frame.py::RenderingTheSpecimenPicture::test_the_whole_picture_renders_character_for_character`; row 29 is the status line's and only the status line's — `tests/test_frame_composer.py::RowTwentyNineIsNotThisItems::test_nothing_the_composer_draws_reaches_row_twenty_nine` and `tests/test_status_line.py::TheRowAsAValue::test_the_status_row_is_the_bottom_row`. **The two halves are now one statement** in `terminal_game/presentation/picture.py`, pinned by `tests/test_picture.py::TheSeamIsOneFunction::test_a_state_in_and_a_whole_frame_out`, and the production wiring goes through it — `tests/test_game.py::ThePictureTheSessionIsComposedWithTest::test_row_29_is_exactly_what_the_status_line_says_it_is` | **Pinned.** WI-22 closed the thing WI-20a could only describe: until then SCRN-1 was true of the running game as two statements that happened to agree |
| SCRN-2 | WI-10 | `tests/test_house_rules.py::ThisRepositoryObeysTheRules::test_rule_3_nothing_draws_an_image`, backed by `tests/test_grid_surface.py::TheRuleThatThereAreNoImages` which shows the recording canvas would notice one, and `tests/test_the_look.py::TheColoursReachTheSurfaceUnchanged::test_nothing_but_characters_is_ever_shown_to_the_person`. **Observed twice over, and the second time is the better one**: canvas item kinds were `["text"]` on all 8 windows of `docs/findings/WI-16-the-look.md`, and **706 items, every one of kind `text`, on a real generated maze in the assembled game** — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed, caveated — caution C5.** Under candidate 2 this is a *rule* we enforce, not a property of the medium, which is exactly why the observation is worth having |
| SCRN-3 | WI-8 | `tests/test_wall_glyphs.py::TheSixteenCombinations` — all sixteen, each named; `tests/test_wall_glyphs.py::TheSpecimenPicture::test_the_resolver_reproduces_the_specimen_s_walls_exactly`. The instrument for the human half exists: `tests/test_the_look.py::TheJoineryViewShowsEveryJunction::test_the_lattice_produces_every_glyph_wi_eight_can_draw` | **Pinned in part, and a human is needed for the rest — A10.** Pinned for *which characters*. Open for *whether the strokes meet*. **This sweep explicitly does not close it**; see below |
| SCRN-4 | WI-12 | `tests/test_frame_composer.py::TheDots::test_a_corridor_square_with_a_dot_shows_the_dot` and `tests/test_frame_composer.py::TheDots::test_the_dot_is_dim_gold` | **Pinned** |
| SCRN-5 | WI-12 | `tests/test_frame_composer.py::TheActorsAreThreeColumnMotifs::test_the_two_motifs_differ_in_shape_as_well_as_colour` and `tests/test_the_look.py::TheColoursReachTheSurfaceUnchanged::test_the_five_visible_colours_are_all_different_on_the_surface`; both motifs shown side by side for comparison in `tests/test_the_look.py::TheColourViewNamesWhatItShows::test_it_shows_both_actor_motifs_so_the_shapes_can_be_compared` | **Pinned in part, and a human is needed for the rest.** Pinned that the five colours are five **different values** and that the two motifs are **different shapes**. Open — declared in `docs/findings/WI-16-the-look.md` §4 — whether the two hues are **distinguishable to a person**, which is what *"can be told apart"* actually asks. The outline half is settled either way |
| SCRN-6 | WI-13 | `tests/test_status_line.py::TheRowAsAValue::test_the_named_status_colour_is_the_one_the_requirements_name`, reaching the surface unchanged in `tests/test_the_look.py::TheColoursReachTheSurfaceUnchanged::test_the_status_row_reaches_the_surface_in_cyan` | **Pinned** |
| SCRN-7 | WI-2, WI-17 | No caret: `tests/test_window_manners.py::NoTextCaretCanExistTest::test_no_module_constructs_a_widget_that_has_a_caret` and `tests/test_window_manners.py::NoTextCaretCanExistTest::test_nothing_gives_a_canvas_text_item_an_insertion_cursor`. No flicker, structurally: `tests/test_grid_surface.py::RepaintingIsADifference::test_repainting_an_unchanged_frame_costs_no_drawing_at_all` and `tests/test_grid_surface.py::RepaintingIsADifference::test_a_move_costs_five_cells_and_not_the_whole_twelve_hundred`. **Observed** for the caret on a real canvas — widget classes `Tk` and `Canvas` and nothing else, `insertwidth` 0, `takefocus` 0, no focused text item — `docs/findings/WI-17-real-window-manners.md` | **Pinned in part, and a human is needed for the rest.** The caret half is pinned *and* observed. *Does it flicker* is open: the repaint costs a median 0.68 ms against a 143 ms tick budget and nothing is ever cleared (`docs/findings/WI-2-cell-metrics.md`), which says the work is 0.5 % of a tick, not that the window looks right |

### 3a. Two functions in the Shell have no automated test at all

**This is a hole, it is real, and it is labelled rather than hidden.** Under
amendment 9 the category is *covered by observation, not by test*, and the rule
that goes with it is absolute: **no row above claims test coverage for anything
in this section.**

| Function | What it does | Why no test can reach it |
| --- | --- | --- |
| `tk_grid.measure_metrics` | measures one character cell before any window exists — WIN-2's 400 × 570 comes from it and nothing else | it constructs a Tk interpreter (withdrawn before it can be mapped, then destroyed) |
| `tk_grid.create_surface` | measures the font and builds a surface on a new canvas | it constructs a Tk interpreter and a canvas |

The suite is forbidden from constructing a toolkit interpreter — house rule 5,
guarded by `tests/test_house_rules.py::ThisRepositoryObeysTheRules::test_rule_5_the_suite_constructs_no_tk_interpreter`
and asserted again at the end of two other files. That rule is what keeps a
window off the user's desktop during a test run, and it was kept rather than
bent. **DEV-B declared the hole instead of quietly constructing an interpreter
in a test**, which would have broken the rule silently, and the technical lead
ruled that declaring it was right.

**What covers them instead**, recorded and citable:

- `docs/findings/WI-2-cell-metrics.md` — `measure_metrics` run against the real
  toolkit: Menlo at 16pt measures 10 × 19, giving 400 × 570, and the same code
  **refuses** three ways rather than substituting — the missing family, the
  substituted family, and `TkFixedFont`, which on this machine resolves to the
  **proportional** `.AppleSystemUIFont` with six different advances over our
  glyphs. A surface built on it would have looked reasonable in code and drawn a
  maze whose walls did not line up.
- `docs/findings/WI-4-first-window.md`, `docs/findings/WI-16-the-look.md`,
  `docs/findings/WI-17-real-window-manners.md`,
  `docs/findings/WI-18-the-game-on-screen.md` — the surface painting real
  pictures into real windows, 400 × 570 to the pixel with no window-manager
  rounding, across 30 windows.
- **The project window ledger: 30 windows opened, 30 reaped, no modal sheet ever
  raised**, across WI-3, WI-4, WI-16, WI-17, WI-18 and the anchor probe, each
  under the conductor's exclusive screen gate.

**An observation nobody wrote down is not coverage; a recorded one is a weaker
but honest kind.** That is exactly what this section is.

### SCRN-3: assumption A10, and this sweep explicitly does not close it

**Whether the strokes of adjacent double-line glyphs actually meet on screen
is not established, and is recorded nowhere as established.**

The spacing is settled by measurement — all 113 glyphs the picture uses share
one advance in Menlo at 14, 16, 18 and 20pt, with a control showing glyphs
Menlo lacks fall back to visibly different advances: 16 px for `中`, 21 px for
an emoji, 18 px for a private-use codepoint, against 10 px for every one of
ours (`docs/findings/WI-2-cell-metrics.md`). So the characters line up.
**Equal advance proves the cells line up; it does not prove the strokes
touch.** Whether the ink joins is about glyph shapes, not metrics.

Amendment 6 made this **assumption A10**. Four developers had each declined to
convert the measurement into an answer; WI-20a was the fifth to decline and
**this landing is the sixth**, deliberately — a traceability document turning
an open question into a tick is the exact failure this item exists to prevent.

**And a sting the sweep must carry forward:** the specimen picture in the
requirements **contains no crossing glyph at all** — measured over the whole
picture in `docs/findings/WI-8-glyph-census.md`, which found 15 of the 16
neighbour combinations there and not the crossing. So checking SCRN-3
against the specimen, or against a game screen, may never put a crossing in
front of anybody. **WI-16's joinery view is the only thing on this project
that has ever rendered one**, and it is what the question must be asked
against. Crossings are not rare in play: 61 of them across the 200 shared
seeds, in 55 of those mazes, with the first appearing on seed 1.

---

## 4. The maze

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| MAZE-1 | WI-5, WI-12 | `tests/test_maze_generator.py::GeneratedMazeTests::test_the_grid_is_nineteen_across_and_twenty_nine_deep`; the 37 columns and the 3-column margin: `tests/test_frame_composer.py::WhereASquareIsDrawn::test_nineteen_squares_fill_exactly_the_thirty_seven_columns` and `tests/test_frame_composer.py::TheRightHandMargin::test_every_maze_row_is_forty_cells_with_three_blank_at_the_end`; the specimen measured in `docs/findings/WI-5-specimen-grid-structure.md` | **Pinned.** Contradiction C-1 resolved as 37 + 3, against the architecture's prose arithmetic of 38 + 2 and in agreement with the architecture's own measurement |
| MAZE-2 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_corridors_run_only_north_south_and_east_west` and `tests/test_maze_generator.py::GeneratedMazeTests::test_no_corridor_is_two_squares_wide` | **Pinned**, over 200 seeds — and structural: a two-by-two block of corridor would need an even/even square, which is never carved |
| MAZE-3 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_the_border_ring_is_solid_on_all_four_sides` | **Pinned**, over 200 seeds |
| MAZE-4 | WI-5 | `tests/test_maze_generator.py::RandomnessTests::test_two_hundred_different_seeds_give_two_hundred_different_mazes` and `tests/test_maze_generator.py::RandomnessTests::test_the_generator_never_reaches_for_the_global_random_source`; reproducibility across hash seeds by `tests/test_scripted_game.py::TheGameReplaysIdentically::test_a_seeded_game_is_the_same_under_a_different_hash_seed` | **Pinned.** See finding 4 in section 12: 200 distinct mazes, and only **two** distinct opening positions |
| MAZE-5 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_no_corridor_square_has_fewer_than_two_corridor_neighbours` | **Pinned**, over 200 seeds — caution C4's first half |
| MAZE-6 | WI-5 | `tests/test_maze_generator.py::GeneratedMazeTests::test_a_flood_fill_from_any_corridor_square_reaches_every_other` | **Pinned**, over 200 seeds — caution C4's second half |

---

## 5. Starting a game

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| START-1 | WI-6 | `tests/test_opening_position.py::PlayerStartTests::test_no_corridor_square_is_nearer_the_middle_than_the_players` | **Pinned** |
| START-2 | WI-6 | `tests/test_opening_position.py::GhostStartTests::test_the_ghost_starts_furthest_across_the_grid_not_along_the_corridors` and `tests/test_opening_position.py::GhostStartTests::test_no_corridor_square_is_further_from_the_player_than_the_ghosts` | **Pinned.** *Across the grid*, not along the corridors — the test is named for the distinction. The tie-break is finding 4 |
| START-3 | WI-6 | `tests/test_opening_position.py::OpeningPositionTests::test_there_is_a_dot_on_every_corridor_square_but_the_players` | **Pinned** |
| START-4 | WI-6 | `tests/test_opening_position.py::OpeningPositionTests::test_the_score_starts_at_zero_and_no_ending_has_happened` | **Pinned** |
| START-5 | WI-15, WI-18 | The session half: `tests/test_session.py::TheGameIsUnderWayWhenTheWindowOpens::test_the_ghost_moves_without_any_key_being_pressed` and `tests/test_session.py::TheGameIsUnderWayWhenTheWindowOpens::test_starting_composes_the_first_picture`. **The window half, which WI-20a left open:** `tests/test_game.py::TheGameIsUnderWayBeforeTheLoopTest::test_the_first_frame_is_painted_before_the_event_loop_is_entered` and `tests/test_game.py::TheGameIsUnderWayBeforeTheLoopTest::test_the_ghost_is_ticking_by_the_time_the_loop_is_entered`. **Observed**: 8 frames painted in 1.188 s with nothing pressed — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed.** *The moment the **window** opens* is closed: the first picture is up before the event loop is entered, and the ghost's timer is on the scheduler by the time it is |

---

## 6. Controls

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| CTRL-1 | WI-9, WI-11, WI-18 | `tests/test_input_translator.py::TheFourArrowKeys` and `tests/test_turn_resolver.py::MovingTests::test_each_arrow_moves_the_player_one_square_that_way`; through the assembly, `tests/test_game.py::AKeyReachingTheSessionTest::test_each_arrow_reaches_the_session_as_a_move_in_its_direction`. **Observed**: four real arrows moved a real player through a real event loop — `docs/findings/WI-17-real-window-manners.md`, `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed** |
| CTRL-2 | WI-11 | `tests/test_turn_resolver.py::MovingTests::test_each_arrow_moves_the_player_one_square_that_way` and `tests/test_turn_resolver.py::MovingTests::test_the_player_never_moves_more_than_one_square_in_a_turn`; nothing but an intent can move the player, and `tests/test_session.py::OnceDecidedNothingMoves::test_a_tick_in_decided_moves_nothing` shows a tick does not | **Pinned** |
| CTRL-3 | WI-11 | `tests/test_turn_resolver.py::MovingIntoAWallTests::test_a_press_towards_a_wall_does_nothing_at_all`. **Observed**: a real `Left` into a wall on a real screen left the player at (9,12) — `docs/findings/WI-17-real-window-manners.md`, and again in the assembled game in `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed.** The four squares walked on screen are exactly what the pure Domain predicts for that seed, so the whole WI-9 → WI-15 → WI-11 chain agrees with itself through a real event loop |
| CTRL-4 | WI-9, WI-15, WI-18 | `tests/test_input_translator.py::TheQuitKey` (both cases) and `tests/test_session.py::QuittingIsTheOnlyWayOut::test_quitting_a_finished_game_reaches_ended`; through the assembly, `tests/test_game.py::AKeyReachingTheSessionTest::test_q_and_shifted_q_both_reach_the_session_as_a_quit`. **Observed**: a real `q` ended a real session at 1.483 s, and a real `q` ended the real assembled game at 1.488 s — `docs/findings/WI-17-real-window-manners.md`, `docs/findings/WI-18-the-game-on-screen.md`, and earlier in `docs/findings/WI-4-first-window.md` | **Pinned and observed.** Worth the observation: WI-3's tests passed and its probe passed and **neither ever pressed a key**, and the game would have been unquittable |
| CTRL-5 | WI-9, WI-17, WI-18 | **Letters:** `tests/test_input_translator.py::EveryOtherKeyIsDiscarded`, `tests/test_input_translator.py::NothingIsEchoedAnywhere`, `tests/test_game.py::AKeyReachingTheSessionTest::test_an_unmapped_key_asks_the_session_for_nothing_at_all`, and for the modified case specifically `tests/test_input_translator.py::TheQuitKey::test_a_control_modified_q_does_not_quit`. **Observed**: a real `z` did nothing, and stdout and stderr were empty across all nine real runs including the two deliberate failures — `docs/findings/WI-17-real-window-manners.md`, `docs/findings/WI-18-the-game-on-screen.md`. **Modified arrows: nothing pins them, because they are not honoured** | **Honoured for letters, and not for modified arrows — A11. This row does not carry a tick.** See below |

### CTRL-5: letters yes, modified arrows no

**Control-Up moves the player.** So do option-Up, shift-Up and command-Up.
CTRL-5 says *"no other key does anything"*, and on the strict reading a modified
arrow is another key, so **the requirement is not fully met and this row says
so rather than ticking.**

**It is deliberate, not accidental, and amendment 9 ruled it so.** The reason is
structural and one line long: the value that crosses the toolkit seam is

```
class KeyPress(NamedTuple):
    keysym: str
    char: str = ""
```

— **there is no modifier state on it.** So:

- A modified **letter** is correctly rejected. Plain `q` arrives as `("q", "q")`;
  control-Q arrives with a control character rather than `"q"`, and `translate`
  insists on the character as well as the keysym, so control-Q does not quit.
  `tests/test_input_translator.py::TheQuitKey::test_a_control_modified_q_does_not_quit`
  pins exactly that.
- A modified **arrow** cannot be told from a plain one, because an arrow types
  no character either way. Control-Up is therefore treated as Up.

**What closing it would cost:** the modifier state added to `KeyPress` in
`terminal_game/shell/toolkit.py` and read in
`terminal_game/presentation/input_translator.py` — WI-3's and WI-9's files,
both landed, both in lanes with no agent. It is a small change and it is not
this item's to make. It is question 8 in section 13.

**No test asserts that a modified arrow moves the player.** That is on purpose:
a test pinning a known gap would make the gap harder to close, and the
consequence is documented here instead.

---

## 7. The ghost

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| GHOST-1 | WI-3, WI-15, WI-18 | `tests/test_cadence.py::GhostCadenceTest::test_the_cadence_is_seven_ticks_a_second` and `tests/test_window_owner.py::TheTickReachingTheCollaboratorTest`; through the assembly, `tests/test_game.py::AKeyReachingTheSessionTest::test_a_tick_reaches_the_session_as_a_tick`. **Observed**: 144.2 ms between ticks, 6.93 a second, on real Tk — `docs/findings/WI-3-tk-window-probe.md`; and 8 frames in 1.188 s in the assembled game with nothing pressed — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed** |
| GHOST-2 | WI-7 | `tests/test_ghost.py::CarryingStraightOn::test_at_a_crossroads_it_still_goes_straight_rather_than_choosing` | **Pinned.** The crossroads case is the one that matters: a junction is not a reason to choose |
| GHOST-3 | WI-7 | `tests/test_ghost.py::ChoosingWhereItCannotCarryOn::test_at_a_tee_it_never_goes_back_the_way_it_came`, `tests/test_ghost.py::ChoosingWhereItCannotCarryOn::test_over_many_draws_the_two_arms_come_up_about_equally`, `tests/test_ghost.py::TurningBackOnlyAsALastResort::test_in_a_dead_end_it_reverses` | **Pinned** — and read the measurement rather than the wording. GHOST-3 reads like the common case and describes the rare one: **the ghost actually has a choice on about 4.79 ticks in 100** (`docs/findings/WI-7-ghost-roaming.md`, over 2,000 ticks on each of 30 generated mazes). Ninety-five ticks in a hundred its next move is forced, which is GHOST-2 working. It still roams — a mean 65.3 % of corridor squares visited, and on seed 0 it covered 237 of 264 in its **last** 400 ticks, so it is not falling into a cycle |
| GHOST-4 | WI-7 | `tests/test_ghost.py::TheGhostTakesNoNoticeOfThePlayer::test_the_signature_carries_no_player` | **Pinned**, and structurally: the player is *absent* from the signature, not unused |

---

## 8. Dots and score

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| SCORE-1 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_moving_onto_a_dotted_square_eats_it_and_scores_exactly_one`, with permanence from `tests/test_dot_field.py`. **Observed**: a real `Up` at a real window ate a real dot and the score read 1 — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed** |
| SCORE-2 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_each_dot_eaten_adds_one_so_the_score_is_the_dots_taken`; in a whole game, `tests/test_scripted_game.py::AWholeSeededGame::test_the_score_equals_the_number_of_dots_eaten`. **Observed**: two dots eaten at a real window, score 2 | **Pinned and observed** |
| SCORE-3 | WI-11 | `tests/test_turn_resolver.py::EatingTests::test_moving_onto_a_square_whose_dot_has_gone_scores_nothing`. **Observed**: a real `Down` back onto an already-eaten square left the score at 1 — `docs/findings/WI-18-the-game-on-screen.md` | **Pinned and observed** |
| SCORE-4 | WI-7, WI-12 | `tests/test_turn_resolver.py::TheGhostsTurnTests::test_the_ghost_neither_eats_a_dot_nor_scores_a_point` and `tests/test_frame_composer.py::TheDots::test_a_dot_under_the_ghost_is_still_in_the_dot_field_afterwards` | **Pinned** on both halves — the rule *and* the drawing |
| SCORE-5 | WI-6, WI-13 | `tests/test_game_state.py::ScoreTests::test_every_operation_a_score_offers_leaves_it_no_smaller`; shown in the line by `tests/test_status_line.py::TheEndingIsChosenByTheOutcome::test_the_same_score_reads_three_different_ways` | **Pinned.** *Never goes down* is pinned structurally: the type offers no operation that could lower it |

---

## 9. How a game ends

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| END-1 | WI-11 | `tests/test_turn_resolver.py::CollisionTests::test_walking_into_the_ghost_loses_the_game` **and** `tests/test_turn_resolver.py::CollisionTests::test_the_ghost_walking_into_the_player_loses_the_game` — the requirement says *whether the player walked into the ghost or the ghost walked into the player*, and there is a test for each; both again in a whole game in `tests/test_scripted_game.py::TheLossPath` | **Pinned** |
| END-2 | WI-11 | `tests/test_turn_resolver.py::WinningTests::test_eating_the_last_dot_wins_the_game`, with `tests/test_turn_resolver.py::WinningTests::test_eating_a_dot_that_is_not_the_last_wins_nothing` showing the case is not vacuous | **Pinned** |
| END-3 | WI-11, WI-19 | `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_eating_the_last_dot_on_the_ghosts_square_is_a_loss`, with `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_the_winning_condition_really_did_hold_in_that_same_turn` showing the case is not vacuous. And again in a whole game: `tests/test_scripted_game.py::EndThreeInAWholeGame::test_the_last_dot_on_the_ghosts_square_is_caught_and_not_cleared`, with `tests/test_scripted_game.py::EndThreeInAWholeGame::test_the_dot_field_really_did_empty_on_that_same_turn` | **Pinned directly and twice, caveated — A8.** The precedence is pinned at the resolver and in a whole game, which is the strongest ordinary coverage the plan said was available; the non-vacuity tests are the ones that matter, because without them the precedence test could pass while the win condition never held. **A8 governs whether the dot still scores**, the specification never says, and both readings satisfy END-3. `tests/test_turn_resolver.py::EndThreePrecedenceTests::test_the_dot_is_still_eaten_and_still_scores_on_the_losing_turn` and `tests/test_scripted_game.py::EndThreeInAWholeGame::test_the_dot_is_still_taken_and_still_scored_on_the_losing_turn` pin the reading we took, and it changes the last number the player ever sees |
| END-4 | WI-12, WI-19 | `tests/test_frame_composer.py::TheDrawOrder::test_the_final_picture_of_a_loss_shows_the_ghost_over_the_player` and `tests/test_scripted_game.py::TheLossPath::test_the_final_picture_shows_the_ghost_and_not_the_player` | **Pinned** |
| END-5 | WI-15 | `tests/test_session.py::OnceDecidedNothingMoves::test_the_picture_the_player_is_looking_at_does_not_change`, with the ghost and the arrows pinned separately in the same class; in a whole game, `tests/test_scripted_game.py::TheWinPath::test_the_last_picture_stays_on_screen` and `tests/test_scripted_game.py::TheWinPath::test_the_ghost_stops_once_the_game_is_won` | **Pinned, caveated — A3** (C-2) |
| END-6 | WI-15 | `tests/test_session.py::QuittingIsTheOnlyWayOut::test_quitting_a_finished_game_reaches_ended` and `tests/test_session.py::OnceDecidedNothingMoves::test_an_arrow_in_decided_changes_nothing` — `q` works and nothing else does; in a whole game, `tests/test_scripted_game.py::TheWinPath::test_q_is_the_only_way_out_and_it_works` and `tests/test_scripted_game.py::TheWinPath::test_further_keys_do_nothing_once_the_game_is_won` | **Pinned, caveated — A3.** No person has yet pressed `q` at a *finished* game, because no game has been played to an ending on a screen |

---

## 10. The status line

| Req | Item | What pins it | Status |
| --- | --- | --- | --- |
| STAT-1 | WI-13, WI-22 | `tests/test_status_line.py::TheRowAsAValue::test_the_status_row_is_the_bottom_row`, and *nothing else on it ever* from `tests/test_frame_composer.py::RowTwentyNineIsNotThisItems::test_the_composer_contains_no_status_line_literal`; in the assembled game, `tests/test_picture.py::TheBottomRowIsTheStatusLines::test_the_bottom_row_is_the_status_row_for_this_state` | **Pinned** |
| STAT-2 | WI-13 | `tests/test_status_line.py::TheThreeLiterals::test_playing_at_score_zero_is_the_stat_2_literal` | **Pinned, caveated — A7** (C-3: the literal disagrees with the specimen picture by exactly one leading space — 26 characters against 27, identical otherwise, measured in `docs/findings/WI-13-status-line-literals.md`; the literal is normative) |
| STAT-3 | WI-13, WI-19 | `tests/test_status_line.py::TheThreeLiterals::test_a_loss_at_score_thirty_seven_is_the_stat_3_loss_literal` and `tests/test_status_line.py::TheThreeLiterals::test_a_win_at_score_two_hundred_and_seventy_four_is_the_stat_3_win_literal`. What a *real* won game shows: `tests/test_scripted_game.py::AWholeSeededGame::test_the_status_line_reads_cleared_with_the_score_it_reached` | **Pinned as formatting, caveated — A7 and A9.** C-4: **no padding rule of any kind** reproduces both examples — they differ in three places at once, and `q quits` sits at column 19 on the loss line and 20 on the win line, so A7's per-ending templates are not the simplest reading but the only one |

### A9 is honoured, and it was checked rather than assumed

**A whole game is worth 259–271 points, mean 264.5, so `CLEARED  score 274` is
a formatting exemplar and not a score any game reached.** Every use of 274 in
the tree was inspected at the first landing and re-inspected at this one: it
appears in `tests/test_status_line.py` (as an input to the formatter, with a
comment saying in as many words that it is not reachable), in
`terminal_game/presentation/status_line.py`'s docstring saying the same, in
`tests/test_frame_composer.py` as a status row to place, and in
`tests/test_game_state.py` as one of several point values.

**Nothing anywhere asserts 274 as an achieved score**, and no row of this
sweep claims it. WI-19 went further and pinned the negative:
`tests/test_scripted_game.py::AWholeSeededGame::test_the_score_is_not_the_number_in_the_specifications_example`
and `tests/test_scripted_game.py::AWholeSeededGame::test_the_score_is_in_the_band_a_whole_game_is_worth`.
The band itself is measured in `docs/findings/WI-6-start-squares.md`: one dot
per corridor square less the player's own, over 200 generated mazes.

---

## 11. The count

| | |
| --- | --- |
| Codes in `docs/FUNCTIONAL_REQUIREMENTS.md` | **49** |
| Rows in this sweep | **49**, each code once — checked by `tests/test_spec_sweep.py` |
| Pinned outright | **35** |
| Pinned but caveated by a named assumption | **9** — WIN-2 (A4), WIN-3 (A1), WIN-4 (A2 revised, C-7), WIN-5 (A3), SCRN-2 (C5), END-3 (A8), END-5 (A3), END-6 (A3), STAT-2 (A7) |
| Pinned as formatting only | **1** — STAT-3 (A7, A9) |
| Pinned in part, with a half needing a human | **3** — SCRN-3 (A10, do the strokes meet), SCRN-5 (are the hues distinguishable), SCRN-7 (does it flicker) |
| **Honoured in part, with a named gap** | **1** — CTRL-5 (A11, modified arrows) |
| Awaiting a work item | **0** — every work item of the run has landed |
| Additionally **observed on a real screen** | **17** — GAME-1, WIN-1, WIN-2, WIN-3, WIN-4, WIN-5, SCRN-2, SCRN-7, START-5, CTRL-1, CTRL-3, CTRL-4, CTRL-5, GHOST-1, SCORE-1, SCORE-2, SCORE-3 |
| **With no test and no named human check at all** | **0** |

35 + 9 + 1 + 3 + 1 = **49**, with no row counted twice. WIN-3 is both caveated
and needs a human; it is counted once, in the caveated line, as it was at the
first landing. The "observed" count overlaps the others and is not part of the
sum.

**Two changes from the first landing's count, both of them corrections
upward in honesty rather than in coverage:**

- **END-3 moved from *Pinned* to *Pinned, caveated — A8*.** WI-20a named A8 in
  the row's prose but did not count the row as caveated. A8 is a live question
  for the user and it changes the last number the player ever sees, so it
  belongs in the count.
- **SCRN-5 moved from *Pinned* to *Pinned in part*.** `docs/findings/WI-16-the-look.md`
  §4 declared the distinguishability half open and WI-20a did not carry it. It
  is carried now.

---

## 12. Findings — the things this sweep turned up

**1. Two requirement codes are named nowhere in the suite: GAME-1 and
SCRN-1.** Both are in fact pinned, by tests that do not cite them. No action
is needed on the code; it is recorded because it shows why a sweep has to
read the tests rather than grep for codes, and because **anyone maintaining
those two requirements has no way to find their tests by searching.** If that
is worth fixing, it is two comments, in
`tests/test_game_state.py::GameStateTests` and `tests/test_frame.py::RenderingTheSpecimenPicture`.

**2. WIN-4's real obstacle is not A2.** The plan treats Accessibility
permission as the only thing between us and a real anchor. Measurement says
there is a second obstacle — multi-display geometry Tk 8.5 will not report —
that no permission grant would clear. `docs/findings/WI-14-anchor-query.md`.
The consequence for anyone reading the WIN-4 row: it is **satisfied by its
fallback for a known cause**, not a gap, and citing only the permission would
imply a fix that does not exist.

**3. The two rows WI-20a left half-finished are closed, and closing them
found nothing wrong.** GAME-1's assembly and START-5's *"the moment the window
opens"* both close at WI-18, both are pinned in `tests/test_game.py`, and both
were then observed on a real screen. **Re-checking every other row against the
wired game rather than against the parts turned up no row that is true of a
component and false of the assembly** — which is the thing a second landing
exists to catch, and it is a better answer than "no rows were checked".

**4. START-2 holds, and a player would still notice something.** The ghost
is always the furthest corridor square from the player, so START-2 is
pinned. But the furthest square is always a corner, all four corners are
always corridor, and the tie is broken deterministically — so **the ghost
always starts in the left-hand column, and 200 distinct mazes produced only
two distinct opening positions** (`docs/findings/WI-6-start-squares.md`:
the player at (9,14) in 115 mazes and (9,13) in 85; the ghost at (1,1) in 115
and (1,27) in 85). Nothing in the specification is broken. It is recorded
because a sweep that only asked "is START-2 pinned?" would have missed it, and
because it is the kind of thing a player sees in three games.

**5. Nothing in the tree is a requirement ticked without evidence.** Every
one of the 49 rows names something, and the two things no test can reach are
declared in section 3a rather than papered over. That is the answer to the
question this item exists to ask.

**6. Seventeen rows have evidence stronger than a test**, because somebody ran
the real thing and wrote down what happened. Every one came from a real-medium
exercise the plan only started demanding after amendment 2, and **SCRN-2's is
the one that matters most** — under candidate 2 "no images" is a convention we
enforce rather than a property of the medium, so seeing `["text"]` and nothing
else on eight windows of the specimen picture, and then **706 items all of kind
`text` on a real generated maze in the assembled game**, is worth more than the
guard that forbids anything else.

**7. GHOST-3's wording reads like the common case and describes the rare
one.** The ghost has a genuine choice on **4.79 ticks in 100**
(`docs/findings/WI-7-ghost-roaming.md`). Nothing is wrong — it is GHOST-2
working — but anyone reasoning about the ghost's behaviour from the random
source will be reasoning about 5 % of its moves. A regular lattice fixture
built for a reproducibility test was so much straighter than a real maze that
it gave one branch point in sixty ticks and made a correct test fail; the test
now guards its own fixture.

**8. No person has played a whole game.** See the note under section 1. The
suite has, twice over, to both endings. A screen has not.

**9. Two functions in the Shell have no automated test**, and that is a kept
rule rather than an oversight — section 3a. The alternative was a test that
constructs a toolkit interpreter, which would put a window on the user's
desktop during `unittest discover`.

---

## 13. What is open, and what a person must do to close it

**None of these is settled, and this sweep settles none of them.** Each row
says what to run, what to look at, and what the answer would cost to act on.
Nothing in the application waits on any of them: the game runs, and every one
of these is a ruling or a glance.

| # | Open | What a person does | What the answer costs |
| --- | --- | --- | --- |
| 1 | **A1 / WIN-3** — does the titlebar read exactly *Terminal Game* to a person? | Run WI-21's harness, `tools/the_questions.py`, and **look at the titlebar**. Nothing before it, nothing after it, no path, no username, no filename | Nothing if yes. Tk has read the string back on all 30 windows this project has opened and **five developers in a row declined to call that an answer**, because the reported name and the rendered titlebar are different things and under candidate 1 they were measured to differ |
| 2 | **A4 / WIN-2** — is Menlo 16pt in a 400 × 570 window large enough to read comfortably? | `/usr/bin/python3 tools/the_look.py --view game --sizes 14,16,18,20 --seconds 5` — four windows, same picture, four sizes, each closing itself | **One constant**: `FONT_POINT_SIZE` in `terminal_game/shell/grid_surface.py`. The window follows automatically — 320 × 480, 400 × 570, 440 × 630, 480 × 720 |
| 3 | **A10 / SCRN-3** — do the strokes of the double lines actually meet? | `/usr/bin/python3 tools/the_look.py --view joinery --seconds 8` and **look for a hairline gap** where two cells meet, or a stroke that steps sideways. **It must be the joinery view, not a game screen** — the specimen picture contains no crossing glyph and a game may never show you one | If no: a different font, or accepting the gap. **Explicitly not closeable by this sweep.** Advance widths are measured uniform with a control, which settles the spacing and nothing else |
| 4 | **A2 revised / WIN-4** — the anchor is the pointer, not a window | Rule on it. **Read C-7 first:** the window opens at the fixed fallback `(120, 120)` on this machine for a reason no Accessibility grant would change. Then ask the modest question — *did it land somewhere you could see it?* | Approved by the lead, **still the user's to overturn**. One constant: hand `WindowAnchor` the `no_anchor` query for A2's literal reading. If you dislike where it lands, **the fix is a better fallback position, not a permission** |
| 5 | **A3 / WIN-5 against END-5 and END-6** — a contradiction in the specification, not an ambiguity | Rule: does the window close the instant the outcome is decided, or when the player presses `q` after seeing the final picture? We proceed on the second | **One line** of `terminal_game/application/session.py`. C-2, and confined to that one work item |
| 6 | **A7 / STAT-2 and STAT-3** — the status-line literals | Rule on two things: whether STAT-2's literal or the specimen picture's leading space wins, and whether both STAT-3 examples are to be reproduced as written | **STAT-2 disagrees with the picture by one leading space**, and **no padding rule of any kind reproduces both STAT-3 examples** (C-3, C-4, measured in `docs/findings/WI-13-status-line-literals.md`). Two files: `terminal_game/presentation/status_line.py` and `tests/test_status_line.py` |
| 7 | **A8 / END-3** — is the dot under the player still eaten on the losing turn? | Rule. As built it is: the player caught on the last dot reads `CAUGHT  score 7`, not 6 | **WI-11 alone**, already landed; a reversal is a small follow-up branch, **never** a WI-15 change. The specification never says and both readings satisfy END-3; we took the reading END-3's own wording presupposes |
| 8 | **A11 / CTRL-5** — modified arrows move the player | Rule: is control-Up moving the player acceptable, or must it be rejected? | Adding modifier state to `KeyPress` in `terminal_game/shell/toolkit.py` and reading it in `terminal_game/presentation/input_translator.py`. **Ruled deliberate, not accidental.** `KeyPress` carries no modifier state, so control-Up cannot be told from Up; modified *letters* are rejected correctly |
| 9 | **SCRN-5** — are the two hues distinguishable to a person? | `/usr/bin/python3 tools/the_look.py --view colours --seconds 8`. Each label is drawn in its own colour as well as the sample, because a hue that reads as a clear block can be unreadable as text | Declared open in `docs/findings/WI-16-the-look.md` §4 and **not carried by the first landing**. The outline half is settled either way: `▐█▌` and `▗█▖` are different shapes and there is a test |
| 10 | **SCRN-7** — does the picture flicker at seven frames a second? | Look at the game while the ghost moves | The repaint is a median 0.68 ms against a 143 ms budget and nothing is ever cleared, so there is no moment holding a blank or half-built picture. That says the work is 0.5 % of a tick; it does not say the window looks right |
| 11 | **The ghost's start-corner tie-break** — the ghost always starts in the left-hand column, so 200 distinct mazes gave only **two** distinct opening positions | Rule: should the corner be drawn at random? | **Breaks no requirement.** One parameter and one `random_source.choice(...)` in `ghost_start_square`, `terminal_game/domain/opening_position.py`. It was not done because WI-6's work item was handed no random source and inventing one would be inventing a requirement |
| 12 | **A9 / C-6** — `CLEARED  score 274` names a score the game cannot reach | Nothing waits on this. The user may simply want to know their example is impossible | A whole game is worth **259–271**, mean 264.5. Kept as a format exemplar; **no test and no row of this sweep asserts 274 as an achieved score** |
| 13 | **Nobody has played a whole game** | **`/usr/bin/python3 -m terminal_game`** — the user runs it, and nobody else may | **This is the one artefact no agent may run** (section 4 rule 5): it is unbounded by design because `q` is the only way out of a finished game, so launched by an agent nobody is there to press it. It answers what no harness can — a game to an ending, a real `q` out of a *finished* game, a close button under a hand, and the process exiting |

### The checklist, and where the answers will be written

Questions 1, 2, 3, 9, 10 and 13 are the ones that need a person in front of a
screen, and **WI-21 is where they are asked properly.** It holds the five
questions as data, every one with `answer = None`, and a structural check that
nothing in the module can fill one in — the sixth refusal in a row to convert a
measurement into an answer, made permanent. Its checklist prints the C-7
warning above the placement question, so the fallback position is not read as a
bug.

**The answers land in docs/findings/WI-21-the-five-questions.md.** That file
is cited here without backticks, deliberately: the backtick convention above is
a claim that a file is on disk and `tests/test_spec_sweep.py` enforces it, and
this sweep's branch was cut before WI-21's landed. The plan's WI-21 entry names
the file `WI-21-human-answers.md`; WI-21 renamed it and flagged the rename for a
ruling, on the ground that a document called *"human answers"* holding five
unanswered questions is the name most likely to be misread by whoever greps for
it later. **This sweep agrees and cites WI-21's name.** If the technical lead
prefers the planned name, it is one line here and one there.

**Two assumptions carried with nothing waiting on them.** **A5** — the game may
not create or modify anything in the user's preferences — has an empty blast
radius, because candidate 2 needs no profile; it is recorded so an answer has
somewhere to land. **A6** — the specimen picture is normative for the
grid-to-screen mapping — is load-bearing but settled: the picture was measured
and satisfies an odd-coordinate cell grid in all 551 squares with no exceptions
(`docs/findings/WI-5-specimen-grid-structure.md`), and C-1 resolved the one
place the architecture's prose disagreed with its own measurement.
