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
