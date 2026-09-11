# WI-2 — The window, the launcher and the two executables

**Branch** `wi-2-window-launcher`, cut from `main` (`436dfa5`).
**Iteration** M0 · **Dev B** · lands **WIN-1, WIN-2, WIN-3, WIN-4, WIN-5**.

**Two things in the architecture did not survive contact with the machine.**
Both are in §*Contradictions* below, with the measurements. Neither was a
judgement call: as written, WIN-5 would have closed the game window about a
second after opening it, and WIN-4 would have put the game on a display the
player was not looking at.

## What this branch adds

| File | What it is |
|---|---|
| `play` | PROCESS A, the supervisor the player runs. Argv-free. |
| `Terminal Game` | PROCESS B, the child. **The file name is the window title.** |
| `termgame/window.py` | The AppleScript adapter and the supervisor sequence — the only module in the project that shells out to `osascript`. |
| `termgame/loop.py` | The entry point `Terminal Game` calls. In M0 its body is a placeholder static screen that returns on `q`; WI-4 and WI-9 replace the body and **must not need to touch the executable**. |
| `termgame/__init__.py` | Empty, on purpose (see *Merge note*). |
| `tests/test_window_geometry.py` | The offset arithmetic, the display choice and the coordinate-space conversion, the fallback chain — all pure functions. |
| `tests/test_window_script.py` | The text of every AppleScript this project can compose. |
| `tests/test_window_supervisor.py` | The supervisor sequence, with `osascript` replaced by a fake. |
| `tests/test_executables.py` | The two entry points: names, modes, shebangs, and the child's first write. |
| `tests/test_placeholder_screen.py` | The M0 placeholder picture and its bottom-right-cell avoidance. |
| `tests/test_launch_smoke.py` | The one live smoke. Skipped without a controlling tty. |
| `docs/findings/WI-2-terminal-window-id.md` | Every AppleScript incantation tried, with the exact error text of the ones that failed. WI-8 and WI-10 rely on it. |

## How WIN-3 is met, and why the file name cannot change

Terminal composes the window title from components, two of which — the
working-directory prefix and the active process name — have no AppleScript
toggle. The architect's measured recipe, reproduced here unchanged:

1. the child is named literally `Terminal Game` and is launched by
   `do script "exec '<repo>/Terminal Game'"` with **no arguments**, so the
   active-process component *is* the title;
2. the child's **first write** is `\033]7;\007`, which clears the
   working-directory prefix;
3. every scriptable title component is set false, `title displays custom title`
   included — setting it true appends a second name and the title reads
   `Terminal Game — Terminal Game`.

`tests/test_executables.py` pins (1) and (2) — the file's exact name, that it is
executable, and that its first bytes on stdout are the escape sequence. (3) is
pinned by `tests/test_window_script.py`. The title itself is **human check H3**.

## The window-safety rules, and what enforces them

Plan §2.6 / architecture C3. The enforcement is structural rather than
conventional:

- `_window(window_id)` is the **only** way this module names a window, and it
  renders `(first window whose id is N)`. There is no other spelling in the file.
- `script_close_window` puts the `busy` test **inside the script**, so the check
  and the close cannot be separated by the player quitting in between. It
  returns `closed` or `busy`; it never closes a busy tab.
- `close_when_idle` is the one close path and both the success path and the
  `finally` call it. If the child is still running when the grace period runs
  out it reports the window id and **leaves the window open rather than forcing
  it**.
- Liveness is read with `visible`, not `exists` — Terminal keeps a stale window
  object after a close.
- `script_front_position` is the single script that mentions the front window.
  It is a **read**, it runs before our window exists, and
  `test_window_script.py` asserts it contains no `set ` and no `close`.
- The child cannot block forever: with no controlling tty `run_game` returns
  immediately instead of waiting for a key.

## WIN-4, and the clamp

`offset_position` is pure: `(ref.x + 30, ref.y + 30)`, clamped so the whole
477 × 707 px window stays on the *reference's own display* and its title bar
stays below the menu bar. Displays come from `CGGetActiveDisplayList` /
`CGDisplayBounds` through `ctypes` — no TCC permission, no subprocess, no
third-party module, and none of the AppleScript-to-Finder tricks that would
raise a permission prompt on the player's screen.

**WIN-4 is not verifiable by any agent.** No agent here has a controlling tty,
so there is no "window the player was last looking at" to be offset from. It is
**human check H1**.

## Contradictions found, with the measurements

### 1. WIN-5 cannot poll `busy` — it is false for the whole of a running game

ARCHITECTURE.md §6.3 prescribes polling `busy of tab 1` until false and closing
then, reporting that poll going `true, true, true, false`. Measured here, every
~0.11 s from the moment `do script` returned:

```
   0.255  busy=true  nprocs=3     <- the shell being replaced by exec
   0.472  busy=true  nprocs=2
   0.580  busy=false nprocs=2     <- the game is painting, waiting for a key
   1.447  busy=false nprocs=2
   --- q typed into the tab ---
   1.638  busy=false nprocs=0     <- the child has exited
```

The same window running `exec /bin/sleep 4` *does* report `busy true`, so it is
not `exec`: Terminal does not count a process blocked reading the tty as busy,
and the game spends its whole life blocked on a keypress. Polling as prescribed
closes the window about a second after opening it — the game flashes and
vanishes.

**Resolution:** the game is running while
`busy or (count of processes of tab 1) > 0`, and the close is guarded by both
halves. No processes means the game has really ended; `busy` false is what
keeps Terminal's modal sheet away, and `busy` *is* briefly true during the exec.

### 2. WIN-4: AppleScript and CoreGraphics do not share a coordinate space

Writing three positions to a window of our own and reading the same window's
frame back from `CGWindowListCopyWindowInfo`:

| written via AppleScript | CoreGraphics reports |
|---|---|
| `(600, 300)` | `y = -1140` |
| `(-898, 76)` | `y = -1364` |
| `(-3000, -1000)` | `y = -1410`, and AppleScript silently clamped the write to `y = 30` |

A constant 1440 offset in y, none in x. This machine has three displays, and
the window `./play` was launched from is **not** on the main one: read as
CoreGraphics coordinates its position is on no display at all, so the clamp
moved the game window to the main display. Converted, the same point is on the
2560 × 1440 to the left and the game lands at `(-868, 106)` — exactly
reference + 30, on the screen the player is using.

### 3. `front window` can be a window the player cannot see

`position of front window` answered with a window at `(-898, 76)` while
Terminal's *visible* windows were `[367, 2486]`. The reference query now takes
the frontmost **visible** window.

### 4. A closed window stays in `windows`

Three probe runs left ids `3924`, `3927`, `3930` in `id of every window` after
being closed; only `visible` goes false. The census counts visible windows, or
it could never match itself across a close.

## Open question A1 — recorded as an assumption, not a ruling

A1 is with the user and unanswered: does WIN-5 mean the window vanishes on the
final frame, or when the player presses `q`? This branch proceeds on the
architect's assumption — **the last picture stays, `q` exits the child, the
supervisor then closes the window**. If the user answers the other way it is one
wait removed from the supervisor, and WI-11 applies it.

## Merge note for the conductor

`termgame/__init__.py` is added by this branch and by WI-1. Mine is **empty**, so
if WI-1's is empty too git merges the add cleanly; if WI-1 gave it a docstring,
the conflict is one file, trivially resolved in WI-1's favour. Nothing else in
this branch is in a file WI-1 touches.

## What was observed live, and what an agent cannot observe

Three probe runs on the real desktop, each opening one window and closing it by
the id captured at creation. **Terminal's visible windows were `[367, 2486]`
before the first and `[367, 2486]` after the last.** `./play` itself, with the
window id taken from play's own report on stderr rather than by enumeration:

```
   0.132  visible before: [367, 2486]
   1.062  play said: 'play: game window 3984 at (-868, 106) (reference (-898, 76) from front)'
   3.227  name: 'Terminal Game' ; visible: True ; play alive: True
   3.303  typed q
   3.544  play exited with 0
   3.628  visible: False
   3.824  visible after: [367, 2486] ; unchanged: True
```

The `q` was typed by AppleScript, because no agent here has a controlling tty.
That is exactly the gap H1–H4 exist to cover, and **nothing above is offered as
verification of WIN-2's font size, WIN-3's title bar, WIN-4 or WIN-5**.

## Tests

```
/usr/bin/python3 -m unittest discover -s tests
Ran 90 tests in 1.692s
OK (skipped=2)
```

The two skips are the live smoke: it is skipped without a controlling tty, so
it skips in every agent session. Its body was run once with the skip lifted
before it was committed — 2 tests, ok, census unchanged — so what is committed
is known to work rather than only known to skip.

## Mutation checks

Not applicable — not part of this workflow (plan §2.7).

## What needs a human

**H1** (WIN-4), **H2** (WIN-5), **H3** (WIN-3) and **H4** (WIN-2, font size).
H1 and H2 are worth running on a machine with more than one display, since that
is where the coordinate-space defect above was hiding.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
