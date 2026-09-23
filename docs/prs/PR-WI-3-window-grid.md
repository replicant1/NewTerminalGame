# WI-3: Window and character grid

Risk: HIGH. It opens, sizes and closes windows on the user's real desktop. That is the plan's floor, and I have not raised it.
Human gate: HIGH
Human gate: needs eyes — WI-3/C15, WI-3/C16

**Base:** `75723e7`, the merge-base with `main` (WI-1, #122, merged in at `21190c0`); the branch was first cut from `8bc9496`. WI-1's desktop mark, `--strict-markers`, the pinned-interpreter check and the window guard all apply to this branch.
**Lane C, Dev C.** The user merges this pull request. Nobody else does.

## What this is

The shell from candidate 2 lives in `terminal_game/shell/`. `GameWindow` opens one Tk window titled `Terminal Game`. The window is 40 × 30 cells of Menlo at 16 px (each cell 10 × 19 points, so 400 × 570). It paints *frames*: 30 rows of 40 `(character, role)` cells, one canvas text item per cell. It delivers named key presses, and a tick scheduled against deadlines at 7 Hz. It closes itself on `close()`, on the title-bar close button, on Quit from the application menu, or when a handler fails. The pure parts need no toolkit and run in the default suite: the frame check, the palette, the typeface choice, the tick schedule and the geometry string. The window itself is proved by **desktop tests**. Each one runs `tests/shell_driver.py` as its own process under a pseudo-terminal with a hard deadline. The tests judge **screen captures of the real window cell by cell**, and never what Tk reports it was told (run 7, `AMEND-6`).

The evidence harness the plan asks for is `evidence/WI-3/card.py`. It is the test card: the specimen picture, with a yellow marker that moves on the arrow keys and a pink one that moves on ticks. The C15 and C16 scripts below run it.

### How to run the evidence

```
.venv/bin/python -m pytest -q -s -m desktop tests/test_shell_window_desktop.py     # all 17 window tests, about 90 s, about 12 short windows
.venv/bin/python -m pytest -q tests/test_shell_pure.py tests/test_shell_characters_only.py   # no window
```

With `-s`, each desktop test prints one line starting `WI-3/<claim>:` that gives what it measured. The *Output shows* column below quotes those lines from my run at `da046e1`+ (numbers vary slightly from run to run). **Do not touch the desktop while the desktop tests run.** The key tests need the game's window to stay the key window. If it loses focus, they fail and say that in words (see Findings, F4).

## Claims

Every control is `n/a`: **at the base `75723e7` the shell package holds only WI-1's `terminal_game/shell/__init__.py`; none of `window.py`, `frame.py`, `palette.py`, `typeface.py`, `ticker.py` or `geometry.py` exists there**, so no claim has a counterpart to run against. An overlay would fail on `ImportError`, which proves nothing. Where the evidence depends on a *technique* (a posted drag, a pixel mask, a source scan), I give that technique its own positive control in the same run. Those are listed under each claim.

Every desktop command is `.venv/bin/python -m pytest -q -s -m desktop tests/test_shell_window_desktop.py::<test>`. Below, `D::<test>` stands for that.

| Claim | Claim text (plan, word for word) | Evidence | Output shows | Control |
|---|---|---|---|---|
| **WI-3/C1** | Started from a terminal, the program opens exactly one new window of its own, and writes nothing to the terminal it was started from during a normal session. | Executable: `D::test_c1_one_window_of_its_own_and_nothing_on_the_terminal`. The driver's stdin, stdout and stderr are a pseudo-terminal. While the window is up, `tests/shell_windows.swift` lists the window server's on-screen windows for the driver's pid. | `WI-3/C1: window server: 1 window for pid … (400x602); NSApp visible windows 1; terminal output after the harness echo: card='', keys='', flip=''` | n/a (new module). **See F2**: the harness passes `-ApplePersistence NO`, and AppKit echoes it as one stderr line, which is the only line removed. The earlier unflagged runs (card, keys ×2, trial) had completely empty output. |
| **WI-3/C2** | The window's drawing area is exactly 40 cells wide and 30 cells deep for the fixed-width typeface in use, with no extra margin, measured in the real window. | Executable: `D::test_c2_drawing_area_is_exactly_40_by_30_cells`. It combines Tk's mapped geometry, the window server's bounds, and six captures in which every cell holds `█` in a role, judged cell by cell at `(c·10, r·19)`. | `WI-3/C2: Menlo cell 10x19; root [400, 570] canvas [400, 570] at [0, 0]; window server 400x602 = 570 + 32-pt title bar; 6 x 1200 role cells judged on screen, 0 out of place` | n/a (new module) |
| **WI-3/C3** | The person cannot resize the window: after an attempt to resize it, the drawing area is still exactly 40 × 30 cells. | Executable: `D::test_c3_resize_attempts_leave_40_by_30`. Three attempts are made: a posted mouse drag of the bottom-right corner outward by 150 × 150 points, a click on the green zoom button, and a Tk size request. After them the border ring is captured and judged. | `WI-3/C3: control drag on a resizable Tk window: [400, 570] -> [550, 720]; corner_drag: root [400, 570] canvas [400, 570]; zoom_button: … [400, 570]; geometry_request: … [400, 570]; zoom button enabled=False` | n/a (new module). **Technique control in the same test:** the identical posted drag against a plain *resizable* Tk window (`resize-control`, not the shell's window) resizes it 400×570 → 550×720. So the drag is a real resize attempt. |
| **WI-3/C4** | If the preferred typeface is not available, the window uses another fixed-width typeface and still measures exactly 40 × 30 of that typeface's cells. | Executable: `D::test_c4_without_the_preferred_face_another_fixed_face_still_measures_40_by_30`. The families passed are `("No Such Typeface WI-3", "Courier New")`, then `("No Such Typeface WI-3",)` alone. Also `.venv/bin/python -m pytest -q -v tests/test_shell_pure.py -k "chosen or proportional or toolkits_fixed"`, which shows `4 passed, 23 deselected` (4 tests of the choice rule, including "an installed but proportional face is passed over"). | `WI-3/C4: preferred face missing -> Courier New cell 10x18, root [400, 540] canvas [400, 540], border ring judged on screen; no preference installed -> Menlo [400, 570]` (Menlo is `TkFixedFont` on this machine) | n/a (new module) |
| **WI-3/C5** | The whole drawing area is black wherever nothing is painted, including the two right-hand columns. | Executable: `D::test_c5_black_wherever_nothing_is_painted`. Seven captures of an empty picture, then every background cell of the specimen capture. | `WI-3/C5: 7 blank captures: 0 non-black pixels outside macOS's outline and rounded corners; specimen: every background cell black, 60 cells in columns 38-39 checked` | n/a (new module). **See F1**: macOS draws a 1-px outline and rounds the bottom corners. Those pixels are identified by rule, and the corner ones must form a staircase anchored in the corner, so a stray mark in a corner still fails. |
| **WI-3/C6** | The window's title, as the toolkit reports it, is exactly `Terminal Game`. | Executable: `D::test_c6_title_is_exactly_terminal_game` | `WI-3/C6: Tk title 'Terminal Game'; window server name 'Terminal Game'` | n/a (new module) |
| **WI-3/C7** | Any character can be painted in any of the 1,200 cells in any of the six colour roles, and a screenshot of the real window shows each painted character inside its own cell in its role's colour. | Executable: `D::test_c7_any_character_in_any_cell_in_any_role_lands_in_its_cell_in_its_colour`. Six frames put every cell in every role. Five frames carry the 256-character alphabet (printable ASCII, U+2500–U+259F, `■`, `▪`) in each visible role, with neighbouring cells always in different roles. Then the specimen. A cell fails if any pixel inside it is not a shade of its own role's colour, or if it holds a painted character with no ink. Observation: `evidence/WI-3/card-da046e1-specimen.png`. | `WI-3/C7: roles0-5: 7200 cell/role pairs, alphabet0-4: 256 characters x 5 roles, specimen: 1200 cells; 0 cells with ink of another colour, 0 painted cells without ink` | n/a (new module). **Scope, stated plainly:** "any character" is proved for the 256 characters above, which are all the game draws and more. A double-width character (such as CJK) cannot fit one cell in any fixed-width face. See F1 for the bottom-corner cells. |
| **WI-3/C8** | Only characters are drawn: everything on the drawing surface is text or the black background, never an image or a shape standing in for a glyph. | Executable (a guard in the default suite, re-checked on every run): `.venv/bin/python -m pytest -q tests/test_shell_characters_only.py`. Executable (desktop): `D::test_c8_only_text_on_the_drawing_surface` | Default: `3 passed`, one of which is the control below. Desktop: `WI-3/C8: children ['.!canvas']; canvas item types ['text']; 1200 items` | n/a (new module). **Guard control:** `test_the_scan_catches_every_kind_of_non_text_drawing` shows that the scanner flags each of `create_rectangle/line/oval/polygon/image/window` and `PhotoImage` in a sample, and `test_the_scan_reads_every_shell_module_including_the_window` shows it did not read nothing. |
| **WI-3/C9** | Replacing one frame with another never shows a picture that is neither: over 5 seconds of repeated repaints, every screenshot matches, cell for cell, one of the frames that was asked for, and no text cursor or caret is visible in any of them. | Executable: `D::test_c9_repaints_only_ever_show_a_frame_that_was_asked_for_and_no_caret`. Two frames differing in more than 1,000 cells alternate every 15 ms for 5 s, while captures are taken back to back. | `WI-3/C9: 246 repaints in 5 s; frames differ in 1030 cells; 64 captures: 24 are frame A, 40 are frame B, 0 neither; 6 blank captures over 1.5 s show no caret` | n/a (new module) |
| **WI-3/C10** | Keys pressed in the window reach the program as named keys (the four arrows, `q`, `Q`, and any other key as itself), and nothing typed ever appears in the window. | Executable: `D::test_c10_keys_arrive_named_and_nothing_typed_appears`. Real AppKit key events are posted into the game's own event queue (see F3 for what that covers) while its window is the key window of the active application, which is checked. | `WI-3/C10: posted ['Up', 'Down', 'Left', 'Right', 'q', 'Q', 'Q-caps-lock', 'a', 'z', '1', 'space', 'Return', 'Escape', 'Tab', 'BackSpace', 'F1'] -> received ['Up', 'Down', 'Left', 'Right', 'q', 'Q', 'Q', 'a', 'z', '1', 'space', 'Return', 'Escape', 'Tab', 'BackSpace', 'F1']; screen before and after typing: black` | n/a (new module) |
| **WI-3/C11** | A repeating tick is delivered between 6.5 and 7.5 times a second, measured over 5 seconds with no key pressed, and again over 5 seconds while keys are pressed as fast as a script can send them. | Executable: `D::test_c11_tick_rate_with_and_without_keys`. Also `tests/test_shell_pure.py -k "tick or rate or stall or period"`, which shows deadline scheduling keeps 35 ticks in 5 s even when each tick's work takes 60 ms. | `WI-3/C11: idle_window: 35 ticks in 5.001 s; flood_window: 35 ticks in 5.001 s; keys delivered during the flood: 16920` | n/a (new module) |
| **WI-3/C12** | When the program ends the session, its window closes by itself and the process exits with status 0 within one second, leaving no window and no process behind. | Executable: `D::test_c12_ending_the_session_closes_the_window_and_exits_0_within_a_second`. In the keys run the program ends the session from its `q` handler; in the card run it ends it from a scripted step. | `WI-3/C12: keys: exit 0 0.021 s after close(), alive=False; card: exit 0 0.016 s after close(), alive=False` | n/a (new module) |
| **WI-3/C13** | Closing the window with its title-bar close button, or quitting from the application menu, ends the process in the same way, leaving no window, no process and no dialog. | Executable: `D::test_c13_close_button_and_quit_menu_end_the_process_the_same_way`. It uses `performClick:` on the window's own close button, and `performActionForItemAtIndex:` on the application menu's Quit item. | `WI-3/C13: close-button: exit 0 0.012 s after the click, alive=False; app-quit: exit 0 0.032 s after the click, alive=False; menu item 'Quit Python'`. A dialog would keep the process alive, and it exited within 33 ms. | n/a (new module) |
| **WI-3/C14** | If a key or tick handler raises an error, the window still closes and the process exits with a non-zero status and prints the error, instead of leaving a frozen window. | Executable: `D::test_c14_a_failing_handler_closes_the_window_exits_nonzero_and_prints_the_error` | `WI-3/C14: raise-key: exit 1, last line 'RuntimeError: deliberate failure in a key handler (WI-3/C14)'; raise-tick: exit 1, last line 'RuntimeError: deliberate failure in a tick handler (WI-3/C14)'` | n/a (new module) |
| **WI-3/C15** | At the chosen type size, a person at a normal seat can read the characters comfortably and can tell the double-line, block and dot characters apart. — **needs eyes** | Needs eyes: script below. Observation: `evidence/WI-3/card-da046e1-specimen.png` | only a person can say | n/a |
| **WI-3/C16** | The window's title bar shows exactly "Terminal Game" and nothing else. — **needs eyes** | Needs eyes: script below. Observation: `evidence/WI-3/card-da046e1-specimen.png` (title bar included). C6 is the machine read-back. | only a person can say | n/a |
| **WI-3/C17** | The default suite command opens no window, while the desktop command runs this item's window tests. | Executable: `.venv/bin/python -m pytest -q` and `.venv/bin/python -m pytest -q -m desktop`. Every window test here carries `pytestmark = pytest.mark.desktop`, and the default-suite tests import no toolkit. | Default: `160 passed, 1 skipped, 17 deselected`. The 17 deselected are exactly this item's window tests. Desktop: `17 passed, 161 deselected`, and with `-s` each test prints its `WI-3/<claim>:` line. | n/a (new module). WI-1's guard cannot see a window made by a subprocess (its README says so). That is why every test here that starts the driver carries the mark. |
| **WI-3/A1** | A frame that is malformed anywhere, even in its last cell, is rejected whole: `paint` raises `ValueError` naming the cell, and the picture on screen does not change. | Executable: `D::test_a1_a_malformed_frame_is_rejected_whole_and_changes_nothing`, and `tests/test_shell_pure.py -k "malformed or not_a_frame"` (8 cases: seven at row 29 or cell (39, 29), and one frame that is not a sequence at all) | `WI-3/A1: rejected with "cell (39, 29) holds 'xx', not exactly one character"; cells changed on screen: 0` | n/a (new module) |
| **WI-3/A2** | A handler that raises `SystemExit` (which tkinter lets out of its loop instead of reporting) still ends the session: the process exits with the status it gave and leaves no window. | Executable: `D::test_a2_system_exit_from_a_handler_ends_with_its_status_and_no_window` | `WI-3/A2: handler raised SystemExit(3) -> process exit 3, alive=False` | n/a (new module) |
| **WI-3/A3** | `place(x, y)`, called before `run`, puts the window's outer top-left corner (title bar included) at screen point (x, y), and writes the position to Tk as an absolute one even when it is negative. | Executable: `D::test_a3_place_puts_the_outer_top_left_at_the_point_given`, and `tests/test_shell_pure.py -k absolute` (`(-877, -1348)` → `+-877+-1348`) | `WI-3/A3: place(120, 140) -> window server top-left (120, 140), drawing area at (120, 172)` | n/a (new module). A negative position is proved only as the string Tk receives. It was not placed on a second display. |

## Diff map

Against the base `75723e7`: `terminal_game/shell/__init__.py` is modified (6 docstring lines); every other file below is new.

```
terminal_game/shell/__init__.py:6-11 (modified) -> WI-3/C8 (the characters-only rule written where a developer meets it)
terminal_game/shell/window.py:1-48             -> docstring, TITLE (C6), exit statuses (C12, C14)
terminal_game/shell/window.py:54-66            -> WI-3/C1 (one Tk root, withdrawn until run, never seen half-built)
terminal_game/shell/window.py:67-75            -> state for C11, C12, C14
terminal_game/shell/window.py:76-88            -> WI-3/C2, WI-3/C4 (face choice, cell metrics, 40 x 30 size)
terminal_game/shell/window.py:90-95            -> WI-3/C6 (title), WI-3/C5 (black root), WI-3/C3 (resizable off, min = max), WI-3/C2 (size)
terminal_game/shell/window.py:97-122           -> WI-3/C2 (no border, no highlight, at 0,0), WI-3/C5 (black), WI-3/C8 (only text items), WI-3/C9 (no insert cursor), WI-3/C7 (one item per cell at c*cw, r*ch)
terminal_game/shell/window.py:124-129          -> WI-3/C13 (close button, app-menu Quit), WI-3/C10 (key binding), WI-3/C14 (handler errors)
terminal_game/shell/window.py:131-146          -> WI-3/C2, WI-3/C4 (family, cell_size, size: the measured interface)
terminal_game/shell/window.py:148-156          -> evidence access for C2, C8, A3 (root and canvas, for the shell's own tests)
terminal_game/shell/window.py:158-166          -> WI-3/A3
terminal_game/shell/window.py:168-180          -> WI-3/C7, WI-3/C9, WI-3/A1
terminal_game/shell/window.py:182-208          -> WI-3/C1 (maps once), WI-3/C10 (focus), WI-3/C11 (schedule), WI-3/C12; finally -> WI-3/A2
terminal_game/shell/window.py:210-212          -> WI-3/C12
terminal_game/shell/window.py:216-226          -> WI-3/C11
terminal_game/shell/window.py:228-231          -> WI-3/C10
terminal_game/shell/window.py:233-237          -> WI-3/C14
terminal_game/shell/window.py:239-254          -> WI-3/C12, WI-3/C13, WI-3/C14 (the one way out)
terminal_game/shell/frame.py                   -> WI-3/C7 (frame shape), WI-3/A1 (whole-frame check)
terminal_game/shell/palette.py                 -> WI-3/C7 (six roles and their colours), WI-3/C5 (background black)
terminal_game/shell/typeface.py                -> WI-3/C4 (choice rule), WI-3/C2, WI-3/C15 (the 16 px size)
terminal_game/shell/ticker.py                  -> WI-3/C11
terminal_game/shell/geometry.py                -> WI-3/A3
tests/test_shell_window_desktop.py (new)       -> evidence for C1-C14, A1-A3
tests/test_shell_pure.py (new)                 -> evidence for C4, C7, C11, A1, A3
tests/test_shell_characters_only.py (new)      -> evidence for C8 (the guard and its control)
tests/shell_driver.py, shell_run.py, shell_appkit.py, shell_screen.py,
  shell_pixels.py, shell_testcard.py, shell_windows.swift (new)   -> test support for the desktop evidence
evidence/WI-3/card.py (new)                    -> the plan's test-card harness; C15, C16 scripts; observations
evidence/WI-3/card-da046e1-*.png, *-transcript.json -> observations for C7, C15, C16
docs/progress/r8-wi-3-window-grid.md, docs/prs/PR-WI-3-window-grid.md -> records
```

## Walk-throughs

**Launch to first picture (C1, C2, C4, C5, C6, C7)**

1. `GameWindow()` → `terminal_game/shell/window.py:63` creates the one Tk root, and `:66` withdraws it before the event loop ever turns, so nothing is on screen yet.
2. `:76-82` asks `choose_family` (`typeface.py:28`) for the first preferred family that is installed and reports fixed metrics. Failing that, the toolkit's own fixed face. `:83-88` makes the cell `measure("M")` × `linespace` and the area 40 × 30 cells.
3. `:90-95` sets the title, the black ground, no resizing (min = max = the area), and the size.
4. `:97-107` makes a canvas exactly that size with no border, highlight or insert cursor, packed at (0, 0). `:109-122` creates 1,200 text items, each at its cell origin `(c·cw, r·ch)`, anchored north-west.
5. `paint(frame)` → `:176` `check_frame` (`frame.py:21`) validates all 1,200 cells before `:177-180` reconfigures each item's text and colour (`palette.py:28`).
6. `run()` → `:197-200` maps the window once, raises it, forces focus, and gives the canvas the focus. `:201-203` starts the tick schedule and enters Tk's loop.

**A key and a tick (C10, C11, C9)**

1. A key press reaches Tk's binding from `:127` → `_key_pressed` `:228-231` → `on_key(event.keysym)`.
2. `_arm_tick` `:216-217` sets `after(delay_ms)`, where `ticker.py:24` measures the delay to the *next deadline*, not a fixed interval. `_tick` `:219-226` advances the deadline (`ticker.py:28`), re-arms, then calls `on_tick()`.
3. Any repaint the handler makes is `paint` (`:168-180`): every cell changes within one callback, and Tk redraws only when control returns to its loop.

**The ways out (C12, C13, C14, A2)**

1. The program calls `close()` `:210-212` → `_shut` `:239-254`, which cancels the pending tick, then `quit()` and `destroy()`. `mainloop` returns, and `run` returns `EXIT_OK` at `:208`.
2. The title-bar close button → `WM_DELETE_WINDOW` bound at `:125` → `close`. Quit in the application menu → `::tk::mac::Quit` bound at `:126` → `close`.
3. A handler raises → tkinter calls `report_callback_exception`, set at `:129` → `_handler_failed` `:233-237`, which prints the traceback to stderr, sets status 1 and calls `_shut`.
4. A handler raises `SystemExit` → tkinter re-raises it out of `mainloop` → the `finally` at `:204-207` calls `_shut`, and the `SystemExit` continues with its own status.

## Needs eyes

Both checks are one run of the test card. It takes two minutes at most.

**Before you start.** If macOS shows *"The last time you opened Python, it unexpectedly quit while reopening windows…"*, click **Don't Reopen**. A test process of mine crashed during development (F2). The alert is about that crash and not about this program, and after that one answer it should not come back.

From the repository root, at this pull request's head:

```
.venv/bin/python evidence/WI-3/card.py
```

You will see a new window, about 400 × 600 points, in the top-left of your main display. It shows a maze drawn in blue double lines, small gold dots in the corridors, a yellow block near the middle, a pink block at the bottom left, and at the bottom a cyan line reading ` score 0    arrows, q quits`. The pink block walks back and forth along the bottom corridor by itself. The arrow keys move the yellow block one square at a time (it ignores walls; this is a test card, not the game). Press **`q`** to close it.

### WI-3/C15: readable, and the three kinds of character tell apart

Sit as you normally would. Look at the maze for ten seconds.

- **Can you read the status line** ` score 0    arrows, q quits` without leaning in? *Failure looks like:* squinting, or leaning closer to read `arrows`.
- **Walls vs. dots vs. blocks.** You should see three different things: the walls as **two thin parallel blue lines**, the dots as **small gold squares**, the markers as **solid filled blocks** (yellow and pink), and two **solid blue squares** standing alone in the lower left (the lone wall squares). *Failure looks like:* a double line that reads as a single line or a dashed line; dots you cannot tell from blocks; or the lone blue squares looking like dots.

If the type is too small, say so. It is one constant (`FONT_PIXELS = 16` in `terminal_game/shell/typeface.py`). Before asking for bigger, one thing is worth knowing: 16 px is the largest Menlo size at which the toolkit's cell width matches the font's own spacing. Above it, box-drawing characters placed cell by cell may show hairline gaps, so "bigger" needs its own look.

### WI-3/C16: the title bar

Look at the window's title bar.

- It should read exactly **`Terminal Game`**, two words, with nothing before or after them. *Failure looks like:* anything else in the title bar: `Python`, `card.py`, a path, a dash and more words, or no title at all. (The menu bar at the top of the screen will say *Python*. That is the application menu, not the title bar, and it is expected.)

Then press **`q`**. *Failure looks like:* the window staying open, or any dialog appearing.

## Findings

- **F1. macOS 26 owns the bottom corners and the outline of the drawing area.** I measured this on 800 × 1140 captures of a 400 × 570 window. macOS draws a 1-pixel grey `(25,25,25)` outline over the left, right and bottom edges. It also **rounds the window's bottom corners**, clipping a staircase-shaped region within 24 × 24 points of each corner, where the desktop shows through. It clips the outermost pixels of cells (0, 29) and (39, 29), and slightly clips (1, 29) and (38, 29). In the game those cells are blank: the status line starts with a blank, and columns 37–39 are margin. For C5 and C7, those pixels are taken from the same run's empty-picture capture and skipped, and the empty-picture check requires them to be exactly the outline plus a corner-anchored staircase. I cannot remove this. It is the platform's window shape.
- **F2. After any Python crash, every later Python+Tk launch on this Mac blocks on a modal "reopen windows?" alert.** `sample` shows `TkpInit` stuck in `NSPersistentUIRestorer promptToIgnorePersistentStateWithCrashHistory` → `NSAlert runModal`. My own driver crashed once during development (see F5, since fixed), and macOS's *Problem Reporter* dialog opened. I have not touched either window. The test harness therefore passes `-ApplePersistence NO` on the driver's own command line. That is AppKit's argument domain: it applies to that process only and persists nothing. AppKit echoes it as one stderr line, and `tests/shell_run.py::program_output` removes exactly that line and nothing else. **For WI-13:** the real game would block on the same alert after any crash. Whether the game should defend against that is a product question.
- **F3. What the key evidence does and does not cover.** Key events are posted into the game's own AppKit queue (`NSEvent keyEventWithType…` + `postEvent:atStart:`). That is the path a real key takes once the window server has delivered it to the application, so AppKit's key window and Tk's key translation are both exercised. It skips the window server's choice of which application receives the key, so the tests also check that the game is the active application and its window is the key window. Posting CGEvents from outside would need an Accessibility permission, which would raise a prompt, so I did not use it.
- **F4. The key tests depend on the game keeping the focus.** Twice the application stopped being key partway through the keys run, and the keys posted after that were dropped: once in development, and once in a full desktop run after the WI-1 merge. The cause was not established; the likeliest is activity on the shared desktop. The keys scenario now takes the focus back before each key phase if it has been lost, and **records each time it does** (`refocused`, printed in C10's line; it has been `[]` in every run since). The tests still check focus at each phase, and fail with that explanation rather than reporting a wrong key.
- **F5. `performClick:` must be queued, not called, from inside a Tk callback.** Called synchronously through ctypes, Tk re-enters Python without the GIL and the interpreter aborts (`PyEval_RestoreThread … GIL is released`). That abort is the crash in F2. The test support now queues it with `performSelector:withObject:afterDelay:0`.
- **F6. Tk 9 keeps `NSWindowStyleMaskResizable` set on a `resizable(False, False)` window.** It disables the zoom button and enforces the size through min = max instead. The drag, zoom and size-request attempts all leave 400 × 570.
- **F7. Ctrl-C at the terminal ends the game with status 1 in under a second, and prints nothing.** Tk handles `SIGINT` natively, and `run` never returns. The window goes with the process. This is not claimed. It is a note for WI-13.

## Interface for WI-9 and WI-13

- `GameWindow(*, title="Terminal Game", families=PREFERRED_FAMILIES, font_pixels=16, tick_hz=7, clock=time.monotonic)` builds the window **withdrawn**.
- `window.size` gives `(400, 570)`: the drawing area in points. The outer window is one title bar taller (32 points on macOS 26). `window.cell_size` and `window.family` are also available.
- `window.place(x, y)` puts the **outer top-left** (title bar included) at global screen point `(x, y)`, before `run`. Negative coordinates are fine.
- `window.paint(frame)` takes a frame of 30 rows × 40 `(character, role)` cells. Roles are the strings `"wall" "dot" "player" "ghost" "status" "background"` from `terminal_game.shell.palette`, and a `StrEnum` whose values are those strings also works. A malformed frame raises `ValueError` and changes nothing.
- `window.run(on_key, on_tick) -> int` blocks until the session ends. `on_key(name)` gets Tk key names (`"Up" "Down" "Left" "Right" "q" "Q"`, and others as themselves, such as `"a" "space" "Escape" "F1"`). `on_tick()` is called 7 times a second. The call returns 0 for `close()`, the close button or menu Quit, and 1 for a handler error. `sys.exit(window.run(...))`.
- `window.close()` ends the session from inside a handler.

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
