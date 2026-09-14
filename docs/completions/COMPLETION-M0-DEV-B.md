# M0 — DEV-B — completion

**Iteration:** M0, "Walking skeleton: a window, a screen, and a pure maze"
**Lane:** DEV-B
**Mode:** local — no remote, no `gh`, no pull requests. The technical lead merged.
**Written:** 04:59Z, after WI-2 was merged and verified on `main`.

---

## The short version

**The iteration ended short for this lane, and not because anything failed.** Of the two work
items planned for DEV-B in M0:

| Item | Planned | What happened |
| --- | --- | --- |
| **WI-2** — the screen port and its terminal adapter, plus a game process that draws one frame and quits | 2 d | **Delivered and merged.** Merge commit `021db44` on `main`. |
| **WI-4** — the maze model and its generator | 2 d | **Not dispatched.** The user paused the run before it was handed out. No branch was cut, no code was written, nothing is half-finished. |

This document is written now rather than at the end of a full M0 precisely because M0 is not going
to have an end for this lane. An unwritten completion document because the iteration was cut short
is worse than a short one that says so.

## WI-2 — what landed

**Branch:** `wi-2-screen-port`, cut from `main` at `d4c1a7f`, merged `--no-ff` as `021db44`.
**PR summary:** `docs/prs/PR-WI-2-screen-port.md`
**Progress log:** `docs/progress/wi-2-screen-port.md`
**Finding:** `docs/findings/WI-2-pty-terminal-restore.md`

A character-cell port — put a cell, present a whole frame in one pass, read a key with a timeout —
with a curses adapter behind it in raw, non-echoing mode with the cursor hidden, and a game process
that drives the port end to end.

| File | What it is |
| --- | --- |
| `terminalgame/screen/port.py` | The port. `Frame`, `Cell`, `Colour`, `Key`, the `Screen` interface, `ScreenTooSmall`. Imports no curses, no subprocess, no sys. |
| `terminalgame/screen/curses_adapter.py` | `CursesScreen` and `TerminalSession`. The only module in the system that imports `curses`. |
| `terminalgame/game_main.py` | The walking-skeleton game process. `python3 -m terminalgame.game_main` — the command WI-3's launcher opens a window on. |
| `tests/fake_terminal.py` | A terminal that lives in memory: real state, and a virtual clock. |
| `tests/test_screen_port.py`, `test_curses_adapter.py`, `test_game_main.py`, `test_real_terminal.py`, `test_layering.py` | The suite. |

## Suite state

| Where | Command | Result |
| --- | --- | --- |
| `wi-2-screen-port` at `ebbd510`, before the merge | `python3 -m unittest discover` | **84 passed, 0 failed, 0 skipped** |
| `main` after `021db44` | `python3 -m unittest discover` | **84 passed, 0 failed, 0 skipped** — run by the technical lead and again by the conductor |
| `wi-2-screen-port` at `eeccce3`, fast-forwarded to `main` for this document | `python3 -m unittest discover` | **84 passed, 0 failed, 0 skipped** |

Nothing skipped, which matters here: the real-curses pseudo-terminal tests are guarded by
`skipUnless(PTYS_AVAILABLE)`, and a zero skip count is the evidence that they genuinely ran against
real ncurses rather than quietly excusing themselves.

Plan §2 asked the two developers to confirm the whole-suite command before the first merge. Confirmed
and unchanged from this lane: **`python3 -m unittest discover` from the repository root**, no
arguments and no installation. `tests/` is a package, so 3.9 discovery finds it without relying on
namespace-package behaviour.

## The four rulings, and what they bind

All four deviations raised in the WI-2 PR summary were accepted by the technical lead. Three of them
carry an obligation for a **later** work item, so they are restated here where the person picking
that item up will find them.

### 1. `--hold` is M0 scaffolding and is not a precedent — binds WI-11 and WI-12

`terminalgame/game_main.py` holds its frame for `--hold` seconds (default 3) and then exits by
itself. Accepted for M0, on the explicit constraint that **the real game process exits on `q` and
never on a timer.**

**WI-12 must not inherit a hold.** `game_main.py` is a walking skeleton that exists to prove the port
works end to end and to give WI-3's launcher something to join to; when WI-11's loop and WI-12's
wiring arrive, the timer goes. If anything in the finished game ends a session other than `q`, that
is END-6 broken and A1 flipped by accident.

### 2. `tests/test_layering.py` is a standing obligation, not a one-off — binds WI-4 and WI-7

The layer-rule test was accepted **and promoted**. It currently asserts that only
`terminalgame/screen/curses_adapter.py` imports `curses`, and that nothing in the game process
imports `subprocess` (caution C11).

**WI-4 and WI-7 are to extend it with the domain-purity cases**: the domain imports no `curses`, no
`subprocess`, no `os`, no `time` and no `sys.stdout` (plan §3). The helper that does the work,
`imports(source, module_name)`, already takes a module name as a parameter, so an extension is a new
test method and a list, not new machinery. The reasoning behind the promotion: a test beats prose
somebody has to police.

### 3. `Frame.put` raises on an out-of-range cell — keep raising, and **do not** add clipping — binds WI-5b

I had flagged a worry that a three-column actor glyph centred on column 0 would need clipping. **The
worry was wrong and the case cannot occur.** MAZE-3's border ring means an actor only ever stands on
squares 1 to 17 of 0 to 18, so a glyph centred on column 2s spans columns 1 to 35 of 0 to 36 and can
never run off either edge. The leftmost position that exists puts the glyph at columns 1–3. The
technical lead measured the same thing independently from the specification's picture.

**WI-5b must not add clipping, and must not add a `put_clipped`.** If WI-5b finds a genuine case, it
goes back to the technical lead rather than being softened locally — a silent clip would turn a real
geometry bug into a picture that is quietly one column wrong.

### 4. Dim yellow for gold, bold magenta for pink — accepted, stays a human check

An eight-colour terminal has no gold and no pink. The substitution lives in one dict, `_palette()` in
`terminalgame/screen/curses_adapter.py`. The tests establish that the five named colours reach the
terminal as five **distinct** attributes; whether dim yellow reads as *gold* and bold magenta as
*pink* to a person (SCRN-4, SCRN-5) is not something any agent can settle. It is already on WI-14b's
human-check list and is **not** recorded anywhere as verified.

## The one measurement worth carrying forward

From `docs/findings/WI-2-pty-terminal-restore.md`:

> After a complete curses session on a real terminal, `tcgetattr` before and after differ in
> **exactly one bit**: `0x20000000`, `termios.PENDIN`. `ECHO` and `ICANON` are both back on and every
> other field is identical, on all four exit paths — a normal exit, a `q`, a `SIGTERM`, and the
> refusal of a too-small terminal.

`PENDIN` is transient kernel state ("input pending redisplay"), not a mode the player chose.

**Why this matters more than it looks.** A restore test that compares `c_lflag` unmasked **fails on
correct code**, and the natural reaction to a failing test is to weaken the assertion until it
passes — which throws away the only check that the player's shell comes back at all (caution C10).
The right move is to mask `0x20000000` and leave the rest of the comparison strict.
`PseudoTerminal.modes()` in `tests/test_real_terminal.py` does that and says why in place. **Whoever
writes WI-12's real-run test needs this**, because they will hit it.

The finding also records the two pseudo-terminal traps that cost time: `LINES` and `COLUMNS` must be
removed from the child's environment or ncurses believes them over the real window size, and the
child's stderr must be a pipe or the "too small" message lands in the middle of the captured picture.

## Machine safety

**No window was opened on the user's screen at any point during this lane's work in M0.** No
`osascript` was run. No macOS permission was requested, and none is recorded as granted or verified.

The real-terminal proof is a pseudo-terminal created with `os.openpty()` inside the test process. A
pseudo-terminal is a real terminal in every way curses cares about — size, termios, echo — and it
exists entirely inside the process, so none of the window-safety hazards arise: no window id to
capture, no modal sheet to raise, nothing to reap. The recipe is written up in the finding for WI-12
to reuse rather than rediscover.

The five stale root executables — `verify`, `launch-smoke`, `check-window-placement`, `play`,
`Terminal Game` — were **not read, not repaired, not called from a test and not deleted.**

## What still needs a human

Four things, none of them recorded as verified. All four are on WI-14b's list where the plan puts
them; they are repeated here because WI-14b has not been written and this document may be read
before it is.

1. **The colours as a person sees them (SCRN-3 to SCRN-6).** Run `python3 -m terminalgame.game_main`
   in a Terminal window of at least 40 x 30 on black. Look for: the border in **blue**; the row of
   small squares in **dim gold, not bright yellow**; `▐█▌` in **bright yellow**; `▐▓▌` in **pink, not
   purple**; the bottom line in **cyan**.
2. **Flicker, and the cursor (SCRN-7).** During those three seconds — does the picture appear in one
   go, and is the text cursor invisible anywhere?
3. **Glyph coverage in the launcher's font (WIN-2).** The box-drawing characters survive a
   pseudo-terminal. Whether the font WI-1 sets on its window has them, at the same advance width,
   needs an eye on the real window. That join is WI-3's.
4. **The shell afterwards (caution C10, from the player's side).** When it exits, type at the prompt
   in that same window. It should appear.

## Where this lane stands

- **Delivered and on `main`:** WI-2.
- **Not started:** WI-4, and everything downstream of it in this lane — WI-5a, WI-9, WI-5b, WI-13,
  WI-14a, WI-14b. Nothing is half-done and no branch is left dangling; the run was paused before WI-4
  was dispatched.
- **Left on the branch:** `wi-2-screen-port`, now fast-forwarded to `main` at `eeccce3` plus this
  document. It is for the technical lead to merge, as in every other merge this run.
- **The critical path is untouched by the pause from this side.** WI-4 is the head of the longest
  chain in the plan (WI-4 → WI-7 → WI-8 → WI-10 → WI-11 → WI-12 → WI-14b, 9 developer-days), so
  whoever resumes this run starts there. Nothing WI-2 built constrains it: the maze is pure domain and
  shares no code with the screen edge.
