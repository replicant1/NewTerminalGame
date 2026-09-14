# WI-2 — the screen port and its terminal adapter

04:51:23Z  START   WI-2 the screen port, its curses adapter, and a game process that draws one frame and quits. Branch wi-2-screen-port cut from main (d4c1a7f). LOCAL MODE, DEV-B.
04:51:23Z  NOTE    WI-2 this worktree's HEAD was behind main and still held the previous run's termgame/ and tests/; branching from main gives the empty tree the plan describes.
04:51:23Z  READ    WI-2 docs/IMPLEMENTATION_PLAN.md in full — §2 runtime, §3 layer rule, §4 ground rules, §7 M0 WI-2 row and its test obligations.
04:51:23Z  READ    WI-2 .claude/shared/progress-tracking.md
04:51:23Z  READ    WI-2 docs/ARCHITECTURE.md §9 cautions — C9 (whole frame, never dirty cells) and C10 (restore on every exit path) are mine.
04:52:52Z  READ    WI-2 docs/FUNCTIONAL_REQUIREMENTS.md — SCRN-1/2/7, CTRL-4/5, WIN-2 are what this port has to make possible.
04:52:52Z  PLAN    WI-2 package `terminalgame`, subpackage `screen`: port.py (Frame, Cell, Colour, Key, Screen ABC, ScreenTooSmall — imports no curses) and curses_adapter.py (CursesScreen + TerminalSession — the only curses importer). Entry point `terminalgame.game_main`.
04:52:52Z  DECIDE  top-level package name -> `terminalgame`, because naming it `termgame` would half-revive the stale root executables that import that name and confuse the next reader.
04:52:52Z  DECIDE  colour vocabulary -> a symbolic `Colour` in the port, mapped to curses pairs only in the adapter, because SCRN-3..6 must be expressible above the port without curses constants leaking up.
04:52:52Z  DECIDE  key vocabulary -> port returns `Key.UP/DOWN/LEFT/RIGHT`, `Key.printable(ch)`, `Key.other(code)`; it does NOT map to game directions, because CTRL-1/CTRL-4 are WI-11's job and the port's job is only to hide the escape sequences.
04:52:52Z  DECIDE  read_key timeout -> seconds in, milliseconds to curses `window.timeout()`, negative clamped to 0, because curses reads a negative timeout as "block forever" and WI-11 will hand it an already-overdue tick.
04:52:52Z  DECIDE  signals -> handlers for SIGTERM and SIGHUP only; SIGINT left alone because Python already turns it into KeyboardInterrupt which the session's finally catches.
04:52:52Z  DRAFT   WI-2 terminalgame/screen/port.py and terminalgame/screen/curses_adapter.py
04:53:59Z  DRAFT   WI-2 tests/fake_terminal.py — a fake terminal that keeps real state (glass, echo, cursor, curses mode) and a virtual clock, so tests assert what the terminal became rather than which call was made.
04:53:59Z  DRAFT   WI-2 tests/test_screen_port.py, tests/test_curses_adapter.py
04:53:59Z  TEST    57 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
04:53:59Z  VERIFY  runtime -> python3 --version reports 3.9.6, matching the plan's §2.
04:54:49Z  COMMIT  94815df WI-2: the screen port and its curses adapter
04:54:49Z  DRAFT   WI-2 terminalgame/game_main.py — the walking-skeleton game process: one frame, a bounded hold, q quits. Runs as `python3 -m terminalgame.game_main`.
04:54:49Z  DECIDE  the skeleton's lifetime -> draw one frame, then poll for q until a bounded --hold (default 3 s) expires, because a process that quits instantly gives WI-3's launcher nothing to join to and one that waits for a key could block forever in a window nobody can close.
04:54:49Z  TEST    73 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
04:55:57Z  DECIDE  how to prove the real adapter -> drive it on a pseudo-terminal from os.openpty(), because it exercises real ncurses and real termios while opening nothing on the user's screen.
04:55:57Z  VERIFY  real curses on a 40x30 pty -> frame reaches the glass with box-drawing glyphs intact, q acted on in well under a second against a 30 s hold, "hello there" typed mid-game never echoed, 20x10/80x24 refused with exit 2.
04:55:57Z  VERIFY  terminal restored on a real pty -> tcgetattr before vs after differs in exactly one bit, 0x20000000 = termios.PENDIN, on all four exit paths (normal, q, SIGTERM, refusal). ECHO and ICANON both back on; every other field identical.
04:55:57Z  DECIDE  restore assertion -> compare termios with PENDIN masked out, because PENDIN is transient kernel state ("input pending redisplay"), not a mode the player chose; masking it is the only way the assertion can be both strict and correct.
04:55:57Z  VERIFY  SIGTERM/SIGHUP in a real process -> terminal restored AND the process still dies of the signal (returncode -15 / -1), so the handler does not swallow it.
04:55:57Z  NOTE    WI-2 two pty gotchas worth knowing: LINES/COLUMNS must be removed from the child's environment or ncurses believes them over the window size; and the child's stderr must be a pipe or the "too small" message lands in the captured picture.
04:55:57Z  DRAFT   WI-2 docs/findings/WI-2-pty-terminal-restore.md
04:55:57Z  TEST    81 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
04:57:01Z  COMMIT  3bb717f WI-2: a game process that draws one frame and quits
04:57:01Z  COMMIT  048714a WI-2: prove the adapter against real curses on a pseudo-terminal
04:57:01Z  DRAFT   WI-2 tests/test_layering.py — plan §3 as a test: curses imported only by the adapter, no subprocess anywhere in the game process (C11). Additive; flagged for a ruling.
04:57:01Z  DRAFT   WI-2 docs/prs/PR-WI-2-screen-port.md
04:57:01Z  VERIFY  suite command -> `python3 -m unittest discover` from the repository root works unchanged, no arguments and no installation; tests/ is a package so 3.9 discovery finds it without relying on namespace packages. Plan §2 asked this be confirmed before the first merge — confirmed from DEV-B's side.
04:57:01Z  ASK     DEV-A/technical lead: the top-level game package is named `terminalgame`; DEV-A's launcher needs a name of its own and must not import from it (plan §3).
04:57:01Z  ASSUME  proceeding on `terminalgame` for the game process and leaving the launcher's name entirely to DEV-A; nothing on this branch depends on what they pick.
04:57:01Z  ASK     technical lead: WI-2's outcome says the process "draws a single frame and quits" — I gave it a bounded --hold (default 3 s) so WI-3 has something to join to and it can never block for ever. Ruling wanted; reversing it is one line.
04:57:01Z  ASSUME  proceeding with --hold defaulting to 3 s; `--hold 0` gives the literal reading of the plan and is already tested.
04:57:01Z  RISK    the five colours reach the terminal as five distinct attributes, but whether dim yellow reads as GOLD and bold magenta as PINK (SCRN-4, SCRN-5) is a human check and is listed as one — not recorded as verified.
04:57:01Z  TEST    84 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
04:57:01Z  NOTE    WI-2 no window was opened on the user's screen at any point, no osascript was run and no macOS permission was requested. The real-terminal proof is a pseudo-terminal inside the test process.
04:57:01Z  DONE    WI-2 wi-2-screen-port 519fe3d (log's own commit follows; the branch head is what the lead merges)
