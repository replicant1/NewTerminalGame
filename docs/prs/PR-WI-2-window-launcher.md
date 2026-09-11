# WI-2 — The window, the launcher and the two executables

**Branch** `wi-2-window-launcher`, cut from `main` (`436dfa5`).
**Iteration** M0 · **Dev B** · lands **WIN-1, WIN-2, WIN-3, WIN-4, WIN-5**.

*(Draft while the work is in progress; the body below is kept current.)*

## What this branch adds

| File | What it is |
|---|---|
| `play` | PROCESS A, the supervisor the player runs. Argv-free. |
| `Terminal Game` | PROCESS B, the child. **The file name is the window title.** |
| `termgame/window.py` | The AppleScript adapter and the supervisor sequence — the only module in the project that shells out to `osascript`. |
| `termgame/loop.py` | The entry point `Terminal Game` calls. In M0 its body is a placeholder static screen that returns on `q`; WI-4 and WI-9 replace the body and **must not need to touch the executable**. |
| `termgame/__init__.py` | Empty, on purpose (see *Merge note*). |
| `tests/test_window_geometry.py` | The offset arithmetic and the fallback chain, as pure functions. |
| `tests/test_window_script.py` | The text of every AppleScript this project can compose. |
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
477 × 707 px window stays on screen and its title bar stays below the menu bar.
The screen size comes from CoreGraphics through `ctypes` — no TCC permission, no
subprocess, no third-party module — and falls back to a conservative
1440 × 900 if that fails. Measured on this machine: 1512 × 982.

**WIN-4 is not verifiable by any agent.** No agent here has a controlling tty,
so there is no "window the player was last looking at" to be offset from. It is
**human check H1**.

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

## Tests

```
/usr/bin/python3 -m unittest discover -s tests
```

Counts are quoted in the final report and in `docs/progress/wi-2-window-launcher.md`.

## Mutation checks

Not applicable — not part of this workflow (plan §2.7).

## What needs a human

**H1** (WIN-4), **H2** (WIN-5), **H3** (WIN-3) and **H4** (WIN-2, font size).
The exact steps are in the final report and in the findings document.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
