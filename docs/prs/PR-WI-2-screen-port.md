# WI-2 — the screen port and its terminal adapter, plus a game process that draws one frame and quits

**Branch:** `wi-2-screen-port`, cut from `main` at `d4c1a7f`
**Lane:** DEV-B, iteration M0
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used.
**Suite:** `python3 -m unittest discover` from the repository root — **84 passed, 0 failed, 0 skipped**.

---

## What this is

A character-cell **port** — put a cell, present a whole frame in one pass, read a key with a
timeout — with a **curses adapter** behind it, and a minimal game process that drives the port end
to end in a real terminal.

It is the first application code in the tree. The tree was empty when this branch was cut, so every
name in it is new and every one of them is open to argument.

## The files

| File | What it is |
| --- | --- |
| `terminalgame/screen/port.py` | The port. `Frame`, `Cell`, `Colour`, `Key`, the `Screen` interface and `ScreenTooSmall`. **Imports no curses, no subprocess and no sys.** |
| `terminalgame/screen/curses_adapter.py` | `CursesScreen` and `TerminalSession`. The only module in the system that imports `curses`. |
| `terminalgame/game_main.py` | The walking-skeleton game process: one frame, a bounded hold, `q` quits. |
| `tests/fake_terminal.py` | A terminal that lives in memory — real state, and a virtual clock. |
| `tests/test_screen_port.py` | The port on its own. |
| `tests/test_curses_adapter.py` | The adapter against the fake terminal. |
| `tests/test_real_terminal.py` | The adapter against **real curses on a pseudo-terminal**. |
| `tests/test_game_main.py` | The game process. |
| `tests/test_layering.py` | The layer rule of plan §3, stated as a test. |
| `docs/findings/WI-2-pty-terminal-restore.md` | What was measured on a real terminal, and the one termios bit that does not come back. |

## How to run it

```
python3 -m terminalgame.game_main              # holds its frame for 3 s, or until q
python3 -m terminalgame.game_main --hold 0     # draws one frame and leaves at once
```

**This is the command WI-3's launcher should open a window on.** It never blocks for ever: with
nobody at the keyboard it ends itself when `--hold` runs out, so a window running it is never left
with a live process in it that nothing can end — which is the condition that raises the modal sheet
nothing can dismiss.

Exit status is `0` normally and `2` for a window below 40 x 30, with the reason on stderr.

## The design, and why

### The port names colours and keys; it does not know what they are

`Colour.WALL`, `Colour.DOT`, `Colour.PLAYER`, `Colour.GHOST`, `Colour.STATUS` are names. Only the
adapter knows that `Colour.WALL` means a curses pair of blue on black. That is what lets WI-5b and
WI-6 ask for the specification's colours without curses leaking above the port (plan §3).

Keys are the same: `Key.UP`, `Key.printable("q")`, `Key.other(code)`. The port hides the escape
sequences and **stops there** — it does not map a key to a direction or to "quit", because CTRL-1
and CTRL-4 are WI-11's, not the terminal's.

### `read_key` takes seconds, and a negative timeout polls

WI-11 recomputes the timeout every pass as the time remaining until the next ghost tick (C7), and
that number goes negative whenever a pass overruns. **curses reads a negative timeout as "block
until a key arrives"**, which would hand the whole game over to the keyboard and stop the ghost
dead. So the adapter clamps to zero: an overdue tick polls and fires. The fake terminal refuses a
negative timeout outright, so this cannot regress quietly.

### One refresh per frame, every cell every time

`present` writes every cell of the frame and refreshes once. Not an implementation detail — C9: the
actor glyphs are three columns wide and overwrite a column of the square next door, so a pass that
wrote only what had changed would leave the other half of somebody else's glyph on the screen.

Cells are grouped into runs of the same colour within a row before being written. This is grouping,
not skipping — `Frame.row_runs` always covers the whole row, and a test asserts the runs rebuild the
row exactly. It is there because one `addstr` per run is both fewer calls and safer for multi-byte
box-drawing glyphs than one `addch` per cell.

### The terminal comes back, on every path

`TerminalSession` restores echo, line buffering, the cursor and curses itself on:

- a normal exit, and an exception (`__exit__` runs either way, and never swallows the exception);
- a failure **during setup**, including the too-small refusal, so a refusal never costs the player
  their terminal;
- `SIGTERM` and `SIGHUP`, which run no `finally` block anywhere in the process. The handler restores
  and then dies of the signal properly, so the exit status still says what killed it.

`SIGINT` is deliberately left alone: Python already turns it into `KeyboardInterrupt`, which the
session's own exit path catches. Restoring is idempotent, and the player's own signal handlers are
put back on the way out.

### Below 40 x 30, it refuses

`ScreenTooSmall` names what was needed and what was found. The terminal is restored **before** the
exception leaves the session, and `game_main` writes the message to stderr after curses has shut
down, so it is readable rather than scrawled across a curses screen.

## The tests

The plan asks WI-2's tests to establish five things. Each is covered twice where it can be — once
against a fake terminal, once against a real one.

| What the plan asks | Where |
| --- | --- |
| A frame is presented in a single pass, not cell by cell | `PresentTest` — one refresh carrying the finished picture; and debris scribbled on the glass between two presents of the *same* frame is wiped out, which a dirty-cell pass could not do |
| The terminal is restored after a normal exit, after an exception, and after a signal | `RestoreTheTerminalTest` (fake) and `RealTerminalSignalTest` (a real `SIGTERM` and `SIGHUP` against real ncurses) |
| A key read returns promptly when a key is waiting, and nothing when the timeout expires | `ReadKeyTest` — the fake terminal keeps a virtual clock, so the tests assert **how long the read actually waited**, not that a call was made |
| Echo is off | `RawModeTest` (fake) and `test_nothing_typed_during_the_game_is_echoed_back` — `hello there` typed into a real pty mid-game never comes back out |
| The curses calls need a seam so these are testable with no terminal | `curses`, `signal` and `locale` are all injected into `TerminalSession`; every fake test runs with no terminal at all |

`tests/fake_terminal.py` is a **fake, not a stub**. It keeps the state a terminal keeps — what is on
the glass, whether it is echoing, whether the cursor shows, whether curses has it — and the tests
assert what it became. `FakeCurses.is_restored` is the whole of C10 in one property.

**No window was opened on the user's screen at any point.** A pseudo-terminal is a real terminal in
every way curses cares about and exists entirely inside the test process, so none of the
window-safety hazards arise. The recipe is written up in the finding for WI-12 to reuse.

## What was measured, not reasoned about

Full detail in `docs/findings/WI-2-pty-terminal-restore.md`. The headline:

> After a complete curses session on a real terminal, `tcgetattr` before and after differ in
> **exactly one bit**: `0x20000000`, `termios.PENDIN`. `ECHO` and `ICANON` are both back on and every
> other field is identical, on all four exit paths — a normal exit, a `q`, a `SIGTERM`, and the
> refusal of a too-small terminal.

`PENDIN` is transient kernel state ("input pending redisplay"), not a mode the player chose. A
restore test that does not mask it fails on a correct implementation, so `PseudoTerminal.modes()`
masks it and says why in place. The finding also records the two pty traps that cost time: `LINES`
and `COLUMNS` must be removed from the child's environment or ncurses believes them over the real
window size, and the child's stderr must be a pipe or the "too small" message lands in the middle of
the captured picture.

## Decisions the rest of the team should know about

1. **The top-level package is `terminalgame`**, not `termgame`. Naming it `termgame` would half-revive
   the five stale root executables that import that name, and the next person to read them would not
   be able to tell which run they belonged to. The stale executables were not read, not repaired and
   not deleted.
2. **The suite command is exactly the one the plan expects** — `python3 -m unittest discover` from the
   repository root, no arguments and no installation. `tests/` is a package (it has an `__init__.py`)
   so discovery finds it on 3.9 without relying on namespace-package behaviour. **Plan §2 asks the two
   developers to confirm this before the first merge: confirmed from this side, unchanged.**
3. **`terminalgame/game_main.py` holds its frame for a bounded time and then exits itself.** The plan
   says "draws a single frame and quits". Quitting *instantly* would give WI-3's launcher nothing to
   join to and a human nothing to look at; waiting for a key *for ever* is the forbidden thing. A
   bounded `--hold` is the only shape that is both. Called out as a deviation below.
4. **The skeleton frame is a placeholder and is labelled as one.** WI-5b composes the real picture
   from a game state. Nothing in `game_main.py` should be mistaken for presentation code, and nothing
   in it constrains WI-5b.

## Deviations from the plan, for a ruling

| # | What | Why | Cost to reverse |
| --- | --- | --- | --- |
| 1 | `game_main` holds its frame for `--hold` seconds (default 3) rather than quitting the instant it has drawn | A process that exits in 20 ms gives WI-3 nothing to observe and a human nothing to see; one that waits for a key could block for ever in a window nothing can close | One line — change the default to `0` |
| 2 | **Additive:** `tests/test_layering.py` enforces plan §3 as a test — curses is imported only by the adapter, and the game process imports no `subprocess` (C11) | The rule is easy to keep at four files and easy to lose at forty | Delete one file |
| 3 | **Additive:** `Frame.put` raises on an out-of-range cell rather than clipping | A negative index would otherwise wrap silently and write to the far side of the frame. WI-5b may want clipping for the three-column actor glyph at column 0; if so it should be an explicit `put_clipped`, not a silent default | Small |
| 4 | The dim-gold and pink of SCRN-4 and SCRN-5 are rendered as dim yellow and bold magenta | An eight-colour terminal has no gold and no pink | Palette is one dict in the adapter |

## Contradictions found

None beyond those the plan already records in §6. The plan's §4.4 instruction to write a report
section 5 saying "not applicable — mutation checking is prohibited" is **obsolete**: the conductor
confirms `.claude/agents/developer.md` has been corrected and the report is now seven items ending at
"What needs a human". No such heading has been written.

## What still needs a human

Nothing here can be confirmed by an agent, and none of it is recorded as verified.

1. **The colours, as a person sees them.** Run `python3 -m terminalgame.game_main` in a Terminal
   window at least 40 x 30 on a black background. Look for: the box border in **blue**; the row of
   small squares in **dim gold** (not bright yellow); `▐█▌` in **bright yellow**; `▐▓▌` in **pink**
   (not purple); the bottom line in **cyan**. Say whether dim yellow reads as gold and bold magenta
   reads as pink. — SCRN-3 to SCRN-6.
2. **Flicker, and the cursor.** During those 3 seconds, does the picture appear in one go, and is the
   text cursor invisible anywhere on screen? — SCRN-7.
3. **The glyphs in the launcher's font.** The box-drawing characters survive a pseudo-terminal. Whether
   the font WI-1 sets on its window has them, at the same advance width, is WIN-2 and needs an eye on
   the real window — the join is WI-3's.
4. **The shell afterwards.** When it exits, type something at the shell prompt in that same window.
   It should appear. That is C10 from the player's side.

Nothing on this branch requests any macOS permission, opens any window, or runs `osascript`.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
