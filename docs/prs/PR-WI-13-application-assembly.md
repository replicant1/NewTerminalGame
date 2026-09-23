# WI-13: Application assembly

Risk: HIGH. This is the whole game on the user's real desktop (plan floor, not raised).
Human gate: HIGH
Human gate: needs eyes — WI-13/C11, WI-13/C12, WI-13/C13

**Base:** `53e89be` (`main` with WI-3, WI-9, WI-10 and WI-12). **Lane C, Dev C.** The user merges this pull request. Nobody else does.
**Waiting on FIX-1 (#135)**, which is approved and not yet merged. Until it lands, `main`, and this branch with it, has one failing default test: WI-3's characters-only guard flags WI-9's `ctypes.create_string_buffer`. Once #135 is on `main`, I merge `main` in here and request verification.

## What this is

`.venv/bin/python -m terminal_game`, the README's one command, runs `terminal_game/__main__.py`, which calls `terminal_game/shell/game.py:main()`:

1. `find_anchor()` and `visible_displays()` (WI-9) run *before* the game's window exists.
2. `Session.new(random.Random())` (WI-12) builds a fresh random source from the operating system, and from it a fresh maze and the starting position. The same source drives the ghost.
3. `play(session, GameWindow(), anchor, displays)`:
   - places the window beside the anchor (outer size = WI-3's 400 × 570 plus the 32-point title bar);
   - paints `compose(session.state)` (WI-10);
   - runs until the session ends. After every key (`translate`, WI-6, then `session.handle`) and every tick (`session.tick`), it either paints the composed state or, once the session has ended, closes the window.

The shell asks the session for its state and composes it. The application never calls upward (§1.4).

The scripted runs call the same `play()` with `Session.new(random.Random(13))`, which is the plan's test-only fixed seed. They live in `tests/game_driver.py`, press real AppKit keys (WI-3 brief, F3), and plan each move by reading the session's state.

## How to run the evidence

```
.venv/bin/python -m pytest -q tests/test_game_assembly.py                     # seams, no window
.venv/bin/python -m pytest -q -s -m desktop tests/test_game_desktop.py        # C3-C7, C9: four short game windows, about 20 s
.venv/bin/python evidence/WI-13/from_terminal.py                              # C1, C2, C8: two Terminal windows, each closed afterwards
.venv/bin/python evidence/WI-13/observe.py                                    # observations: three short game windows, PNGs
```

**Do not touch the desktop while the desktop runs are going.** With `-s`, each desktop test prints a `WI-13/<claim>:` line with what it measured; the table quotes my run.

## Claims

Control for every claim: **n/a**. At the base `53e89be`, `terminal_game/shell/game.py` and `terminal_game/__main__.py` do not exist (`python -m terminal_game` there fails with "No module named terminal_game.__main__"). An ImportError proves nothing, so there is no counterpart to control against. Where a technique could pass vacuously, it carries its own check, noted in the row.

`D::<test>` stands for `.venv/bin/python -m pytest -q -s -m desktop tests/test_game_desktop.py::<test>`.

| Claim | Claim text (plan, word for word) | Evidence | Output shows | Control |
|---|---|---|---|---|
| **WI-13/C1** | The README's one command, run from a Terminal window, opens the game window showing a fresh maze, the player, the ghost and ` score 0    arrows, q quits`, and the ghost is moving within half a second with no key pressed. | Executable: `.venv/bin/python evidence/WI-13/from_terminal.py`. It types `.venv/bin/python -m terminal_game` into a new Terminal window, finds the window titled `Terminal Game` whose process runs on that tab's tty, and captures its drawing area twice, 0.5 s apart. Each cell is classified by the exact role colour it holds. Observation: `evidence/WI-13/from-terminal-87cac35-launch1.png`. Supporting: `D::test_c3_…` (the ghost's first move comes one tick, 143 ms, after the window maps). | `launch 1: game window seen 0.64 s after the command …`, `status row cells match ' score 0    arrows, q quits'; player cells [(17, 14), (18, 14), (19, 14)]; dots 262; ghost at [(7, 5), …] then [(9, 8), …] -> moved within 0.5 s: True` (and the same for launch 2) | n/a (new module). The status check compares the *positions* of cyan cells against the expected text's non-blank positions, so a missing or shifted status line fails it. |
| **WI-13/C2** | Two launches in a row show different mazes. | Executable: the same harness, two launches. It compares the wall / not-wall pattern of the 29 × 40 maze cells. | `mazes differ between launches: True (191 of 1160 maze cells differ in wall/not-wall)`. Record: `evidence/WI-13/from-terminal-87cac35.json` | n/a (new module) |
| **WI-13/C3** | In the real window, with no key pressed, the ghost moves between 32 and 38 squares in 5 seconds. | Executable: `D::test_c3_the_ghost_moves_32_to_38_squares_in_5_seconds_with_no_key` | `WI-13/C3: 35 ghost moves in 5.002 s, no key pressed` | n/a (new module) |
| **WI-13/C4** | In the real window, one arrow key press moves the player one square onto a dot, the dot disappears, and the status line's score goes up by one, shown by screenshots before and after. | Executable: `D::test_c4_one_arrow_press_moves_one_square_onto_a_dot_which_disappears_and_scores_one`. Each capture is taken while the state holds still, and judged cell by cell against its composed frame. The test also shows that the screen changed in *exactly* the cells where the two frames differ. Observations: `evidence/WI-13/game-bb85273-before-key.png`, `-after-key.png` | `WI-13/C4: Up moved the player [9, 14] -> [9, 13] onto a dot; score 0 -> 1, dots 262 -> 261; both captures match their frames cell for cell in role colour; the screen changed in exactly the 13 cells the frames differ in, status cells [7] among them` | n/a (new module). "Exactly the cells" works both ways: a cell that changed without its frame changing fails, and so does a frame change that did not reach the screen. |
| **WI-13/C5** | Played to a loss in the real window, the final picture shows the ghost over the player and ` CAUGHT  score N   q quits` with the right N, and it stays unchanged for at least 3 seconds while ticks pass and arrow keys are pressed. | Executable: `D::test_c5_a_loss_shows_the_ghost_over_the_player_and_caught_and_holds_for_3_seconds`. The driver walks into the ghost with real keys, then presses 256 arrow keys over 3.2 s while the timer keeps ticking. Observation: `evidence/WI-13/game-bb85273-loss.png` | `WI-13/C5: lost at score 24 (262 - 238 dots left) after 25 keys; ghost drawn over the player at [5, 1], no player cell visible; status ' CAUGHT  score 24   q quits …'; screen identical after 3.2 s of ticks and 256 arrow keys` | n/a (new module) |
| **WI-13/C6** | Played to a win in the real window, the final picture shows ` CLEARED  score N  q quits` with N equal to the number of dots the maze started with, and it stays unchanged until `q`. | Executable: `D::test_c6_a_win_shows_cleared_with_every_dot_scored_and_holds_until_q`. The driver eats every dot while keeping clear of the ghost, then presses 40 arrow keys over 2 s before `q`. Observation: `evidence/WI-13/game-bb85273-win.png` | `WI-13/C6: won: score 262 = 262 dots at start, after 416 keys; status ' CLEARED  score 262  q quits …'; screen identical after 40 arrow keys over 2 s; then q ended it` | n/a (new module) |
| **WI-13/C7** | Pressing `q` or `Q`, during play and after an ending, closes the window and ends the process within one second, leaving no window, no process and no dialog. | Executable: `D::test_c7_q_and_Q_during_play_and_after_an_ending_close_it_within_a_second`. Four real key presses: `q` and `Q` during play, `Q` after a loss, `q` after a win. | `WI-13/C7: q during play: exit 0 in 0.017 s; Q during play: exit 0 in 0.017 s; Q after a loss: exit 0 in 0.022 s; q after a win: exit 0 in 0.016 s; no process left, nothing on the terminal`. A dialog would keep the process alive. | n/a (new module) |
| **WI-13/C8** | The window opens a little below and to the right of the Terminal window it was started from, wholly on the visible screen, at the right place on a Retina display (not at half or double the intended position). | Executable: `evidence/WI-13/from_terminal.py`. It compares Terminal's own `bounds` for its window with the window server's bounds for the game window, both in points. The Terminal window was on the middle display, whose `backingScaleFactor` is **2.0** (Retina), measured 2026-09-23 (progress log). | `Terminal at [322, -1367], game at [362.0, -1327.0] -> offset [40.0, 40.0] …; game size [400.0, 602.0]`, both launches | n/a (new module). Half or double the intended position would show as an offset of 20 or 80, or a size of 200 × 301 or 800 × 1204. |
| **WI-13/C9** | A screenshot of the real window shows walls in the wall colour, dots in the dot colour, the player in the player colour, the ghost in the ghost colour, the status line in the status colour and the background black, and the dots are dimmer than the player. | Executable: `D::test_c9_a_screenshot_shows_every_role_in_its_colour_and_dots_dimmer_than_the_player`. Observation: `evidence/WI-13/game-bb85273-start.png` | `WI-13/C9: start capture: all 1200 cells match their frame in role colour (walls, dots, player, ghost, status; blanks black); dot (183, 134, 10) luminance 135 < player (255, 255, 0) luminance 237` | n/a (new module). The pixels inside macOS's clipped bottom-corner squares are skipped (WI-3 brief, F1). |
| **WI-13/C10** | The default suite command opens no window, and the layer check (WI-1/C3, C4) passes on the finished tree with modules examined in every layer. | Executable: `.venv/bin/python -m pytest -q` and `.venv/bin/python -m tools.layer_check` | Layer check: `examined: shell 10, presentation 6, application 3, domain 6, entry 2` / `PASS (0 violation(s), 0 problem(s))`. Default suite: *to be filled in once FIX-1 is merged in* (today: `1 failed, 552 passed, 1 skipped, 23 deselected`, the one failure being the FIX-1 guard). | n/a |
| **WI-13/C11** | Seen in play, the walls join into corners, tees and crossings like the specimen picture, with no gaps or misaligned pieces between neighbouring characters, and a lone wall square shows as a single block. — **needs eyes** | Needs eyes: script below. Observations: `evidence/WI-13/from-terminal-87cac35-launch1.png`, `game-bb85273-start.png` | only a person can say | n/a |
| **WI-13/C12** | Seen in play, the picture changes without flicker, the ghost moves at a steady pace, and no text cursor is visible. — **needs eyes** | Needs eyes: script below. Supporting: WI-3/C9 (no mixed frame in 64 captures during repaints) and WI-3/C11 (the 7 Hz tick) | only a person can say | n/a |
| **WI-13/C13** | Started from a Terminal window, the game window appears a little below and to the right of it, and no permission or consent dialog appears at any point. — **needs eyes** | Needs eyes: script below. Supporting: C8 above | only a person can say | n/a |

The seams are also covered with no window. `tests/test_game_assembly.py` (7 tests) asserts the joins only:
- a key reaches the session through `translate`, and the painted frame is exactly `compose` of the new state;
- a tick reaches the session likewise;
- quit closes the window instead of painting;
- the window is placed from the anchor with its outer size;
- `main` finds the anchor and displays before creating the window, and uses a new `random.Random` each run.

## Diff map

```
terminal_game/shell/game.py:1-22     -> docstring (C1, C10)
terminal_game/shell/game.py:35-37    -> TITLE_BAR_POINTS (C8)
terminal_game/shell/game.py:40-49    -> play: placement with the outer size (C8, C13)
terminal_game/shell/game.py:51-66    -> play: the event loop, compose after every event, close on quit (C1, C3-C7, C9, C12)
terminal_game/shell/game.py:69-74    -> main: anchor and displays first, a fresh random source (C1, C2, C8)
terminal_game/__main__.py            -> the README's one command (C1)
README.md "Playing"                  -> the one command, and Don't Reopen (C1)
tests/test_game_assembly.py (new)    -> the seams (C1, C3, C7, C8)
tests/test_game_desktop.py (new)     -> evidence for C3-C7, C9
tests/game_driver.py (new)           -> test support: the fixed-seed scripted runs
tests/shell_run.py:60,69             -> test support: run_driver takes the driver to run (WI-3's harness reused)
tests/shell_pixels.py corner_mask    -> test support: mask for a window with no blank picture
evidence/WI-13/from_terminal.py      -> evidence for C1, C2, C8
evidence/WI-13/observe.py            -> observations
evidence/WI-13/*.png, *.json         -> observations and records
docs/progress/r8-wi-13-application-assembly.md, this file -> records
docs/progress/r8-wi-9-anchor-placement.md, docs/completions/COMPLETION-M1-DEV-C.md -> mechanical: WI-9's held log lines and lane C's M1 completion record, carried as the conductor asked
```

## Walk-throughs

**Launch to the first picture (C1, C2, C8, C13)**
1. `python -m terminal_game` → `terminal_game/__main__.py:7` → `terminal_game/shell/game.py:69` `main()`.
2. `game.py:71-72`: `find_anchor()` (`anchor.py:143`, the frontmost window that isn't ours, 500 ms limit) and `visible_displays()` (`anchor.py:173`).
3. `game.py:73`: `Session.new(random.Random())` (`session.py:74`), which generates the maze and sets up the game from that source.
4. `game.py:74` → `play()`: `game.py:47-49` gives `place(anchor, (400, 602), displays)` (`placement.py:89`), then `GameWindow.place` (`window.py:158`).
5. `game.py:65` paints `compose(session.state)` (`frame_composer.py:84`); `game.py:66` enters `window.run` (`window.py:182`), which maps the window and starts the 7 Hz tick.

**A key and a tick (C3, C4, C5, C6, C12)**
1. A key → `window.py:228` `_key_pressed` → `game.py:57` `on_key` → `translate(name)` → `session.handle(intent)` (`session.py:99`) → `game.py:51` `after_event` → `paint(compose(session.state))`.
2. A tick → `window.py:219` `_tick` → `game.py:61` `on_tick` → `session.tick()` (`session.py:94`) → `after_event`.
3. Once the game is decided, `session.tick` and moves change nothing (WI-12), so every repaint paints the same frame (C5, C6).

**Quitting (C7)**
1. `q`/`Q` → `translate` gives `"quit"` → `session.handle` sets `ended` → `after_event` (`game.py:52-53`) calls `window.close()` (`window.py:210`) → `run` returns 0 → `__main__.py:7` `sys.exit(0)`.

## Needs eyes

Run these in an **ordinary Terminal tab**, from the repository root, at this pull request's head. They take about two minutes in all.

**Before you start.** If macOS shows *"The last time you opened Python, it unexpectedly quit while reopening windows…"*, click **Don't Reopen**. It comes from an earlier crash of a test process, not from the game.

```
.venv/bin/python -m terminal_game
```

What you will see: a window titled *Terminal Game* appears. It shows a blue double-line maze, gold dots, a yellow block near the middle (you), a pink block somewhere else (the ghost, already moving), and at the bottom a cyan line ` score 0    arrows, q quits`.

### WI-13/C13: where it appears, and no dialog (look first, as it opens)

- The game window should appear **a little below and to the right of the Terminal window you typed into**: its top-left corner roughly a finger's width in from the Terminal window's top-left corner, and wholly on screen.
- *Failure looks like:* the window appearing somewhere unrelated (the far corner of another display, or centred on the main display while your Terminal is elsewhere); part of it off screen; or **any permission or consent dialog**, such as "Terminal wants to control…", "…would like to record this screen", or an Accessibility request, at any point.

### WI-13/C11: the walls (ten seconds of looking)

- Look along the walls. Corners, tees and crossings should join the way the specimen picture in `docs/FUNCTIONAL_REQUIREMENTS.md` §3 draws them: two thin parallel lines, continuous through every turn.
- Look for a **lone wall square**: a single solid blue square standing by itself. Most mazes have a few.
- *Failure looks like:* a gap or a step between two neighbouring wall pieces; a corner whose lines do not meet; double lines that turn into single lines partway; a lone wall square drawn as lines or as a small dot rather than as one solid block.

### WI-13/C12: motion (thirty seconds of play)

- Watch the pink ghost for ten seconds without pressing anything, then play with the arrow keys for twenty seconds.
- It should move at a **steady** pace, about seven squares a second, and the picture should change cleanly.
- *Failure looks like:* the picture flashing, flickering or briefly going blank; the ghost stuttering, pausing, or speeding up and slowing down; a blinking text cursor (a thin vertical bar or an underscore) anywhere in the window; or a letter appearing when you press a key other than an arrow.

Then press **`q`**. The window should close at once. *Failure looks like:* the window staying open, or any dialog appearing.

## Findings

- **F1.** A new window grows open over about half a second on macOS 26. Its bounds read at first sight are about 99 % of the final size (396 × 596 instead of 400 × 602, offset by 2 and 3 points). The C8 harness reads them after 0.8 s. The game places itself correctly; only an early reading is off.
- **F2.** `python -m terminal_game` needs no permission at any point. The anchor query and the display query are read-only, and no Accessibility or Screen Recording request appeared in the harness runs, which only a person can confirm for their own session (C13).
- **F3.** SIGTERM is how the C1/C2/C8 harness ends the game it launched in Terminal. Typing `q` into another application's window would need an Accessibility permission. `q` itself is C7.

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
