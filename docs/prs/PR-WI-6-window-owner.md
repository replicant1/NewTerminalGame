# WI-6 — the window owner

The application's own native window: titled exactly *Terminal Game*, black ground, sized
from WI-5's cell metrics to 40 × 30 cells, and able to close itself and end the process.
Plan section 5, iteration M1, lane C. Depends on WI-5 and S-1, both merged.

**Placement is deliberately absent.** That is WI-15, which is also mine later and is the
only later writer here.

## What is here

| File | |
|---|---|
| `terminal_game/shell/window.py` | `GameWindow` — the one window this game has |
| `tests/test_window.py` | 52 tests, 2 of them `needs_window` and excluded by default |
| `docs/completions/COMPLETION-M0-DEV-C.md` | Lane C's M0 record, extended for WI-5 and carried forward here |

## The four requirements, and how each is checked

**WIN-1 — a window of its own.** A real native toplevel with a window-server id, holding
the character grid and nothing else.

**WIN-3 — titled exactly *Terminal Game*.** Under candidate 2 nothing composes around what
this process sets, so the architect's assumption A1 and caution C2 fall away with the
terminal they were about. Checked as an exact string with nothing appended. **What the
*titlebar* shows is still human item 2** and no agent can answer it.

**WIN-2 — 40 × 30 cells, black ground.** The window asks for the size WI-5's metrics
computed; the test asserts *that join*, then separately that the number here is 400 × 570.
Also: the window cannot be resized, because WIN-2 says *exactly* 40 × 30 and a window the
player could drag larger would have rows the game does not know about.

**WIN-5 — closes itself and ends the process.** `close()` is idempotent, fires `on_close`,
leaves the event loop and destroys the window. **It does not call `sys.exit`, deliberately**
— destroying the window is what makes `run()` return, and when the entry point's call to
`run()` returns there is nothing left to do. Ending by *running out of work* is both the
honest mechanism and the only one that can be tested without a subprocess.

**Every test runs on a window that never reaches the screen**, asserting against the
toolkit's own reported state. The two that genuinely cannot — the event loop on a mapped
window — are marked `needs_window` and excluded by `pytest.ini`.

## A defect I found by hitting it, and the user saw it

**My own `needs_window` run hung with a window on the user's screen for about two minutes.**
I killed it at 02:04:17Z by pid — my own process, 41832/41837 — `visibleApplicationCount`
was 8 during the hang and 7 immediately after, and no stray process or window was left.

The cause is not obvious and is worth writing down: **`mainloop` belongs to the Tk
interpreter, not to a window.** `close()` destroyed the window. When the window owns the
interpreter — production — the root goes and `mainloop` returns. When it does not — a
Toplevel on somebody else's root, which is what the tests use — the interpreter survives
and **`mainloop` never returns**: a window gone from the screen and a process that will not
end. That is precisely what ground rule 1.5 exists to prevent.

**Fixed structurally rather than documented:** `close()` now calls `quit()` before
`destroy()`, unconditionally, so `run()` returns whoever owns the interpreter. The
guarantee no longer depends on who constructed the window. Proven by the very tests that
hung — `pytest -q -m needs_window` is now **2 passed in 1.14 s**, run under an external
45-second subprocess deadline so it could not hang twice.

**A second lesson, mine rather than the code's:** I ran a window-mapping suite with no
deadline outside pytest. A pytest-internal timeout does not help when the hang is in
`mainloop`. Every such run now goes inside a subprocess timeout, which is what caught it
the second time.

## One Tk interpreter per process

`GameWindow(master=None)` creates the root — the production shape. `GameWindow(master=root)`
creates a `Toplevel` — what the suite uses. Either way it is a real native window, which is
what WIN-1 asks for.

This is not a style choice. A `mainloop()` entered after other roots had been created and
destroyed in the same process **segfaulted the interpreter** under the suite, and stopped
the moment every window became a Toplevel on one root. **Residual, stated plainly:** anyone
who constructs a second `tkinter.Tk()` in one process can still crash this build. WI-7
cannot hit it as long as it goes through `GameWindow`.

## The exit path, settled with lane A

Lane A asked, while this was still open, whether WI-6 hands WI-7 something to call or owns
the whole exit. **WI-6 owns the guarantee; WI-7 owns the policy.**

- WI-6 does **not** bind `q` — key-to-intent is WI-13's vocabulary and WI-7's wiring. WI-7
  binds `q`/`Q` to `window.close()`.
- WI-6 guarantees the floor unilaterally: the constructor wires `WM_DELETE_WINDOW →
  close()`, so **the window is closeable even if WI-7 binds nothing at all**, and
  `quit()`-before-`destroy()` means the loop always ends. Neither of us can leave a window
  with no way out.
- Keys are bound on the **toplevel**, not the canvas: WI-5's surface refuses the keyboard
  focus so no caret can appear (SCRN-7), so keys have to be caught here.

## Measured while building this, and useful to other lanes

| | |
|---|---|
| **`mainloop()` works on a MAPPED window** and returns when the window is destroyed from inside an `after()` callback — 629 ms, exactly as scheduled; `update_idletasks()` on a mapped window returns in 10.6 ms | **Retires the lead's logged risk** that the event loop shares the path that hangs `update()`. WI-7 will not find it on the user's desk |
| **`mainloop()` also runs on a WITHDRAWN root** — `after()` callbacks fire, `quit()` returns in 60 ms, root survives, `ismapped` and `viewable` stay False | **WI-14's cadence and WI-16's journeys can be driven headlessly.** No real window needed |
| A non-resizable mapped toplevel reports `state() == "zoomed"`, not `"normal"` | Use `winfo_ismapped`; a test asserting `"normal"` fails for no good reason |
| `event_generate` on a withdrawn toplevel delivers nothing | Key delivery cannot be tested headlessly; that test is `needs_window` |
| After `destroy`, a child reports `winfo_exists()` False cleanly; a **root** raises `TclError` | `is_open` handles both, and both shapes are tested |
| Tk normalises binding names: `<Key-q>` → `q`, `<Up>` → `<Key-Up>` | Cost me a test expectation |
| `resizable()` returns the **string** `"0 0"`, whose every character is truthy | Cost me a real bug: `any(bool(f) for f in ...)` said a fixed window was resizable |

## Crash accounting

Eleven interpreter crashes between 01:58:24Z and 02:00:51Z are mine, from re-running the
same crashing test file while bisecting it — one defect, about eleven runs, not eleven
mistakes. **Seven of them crashed at interpreter *exit*, after pytest had printed its
results**, so the command output looked like a clean run and only one was visible to me at
the time. The `.ips` directory is the reliable detector and I was not counting it; I am now.

**Zero new crash reports since 02:00:51Z**, across six full-suite runs and one
`needs_window` run.

## Suite state

```
.venv/bin/python -m pytest -q                    →  586 passed, 0 failed, 0 skipped, 2 deselected
.venv/bin/python -m pytest -q -m needs_window    →  2 passed, 0 failed, 0 skipped
```

Run from the repository root after `git merge origin/main` (`a2373a9`, which brought WI-4b
and WI-10), `.venv` from `/usr/bin/python3` 3.9.6 with pytest 8.4.2. Baseline when this
branch was cut from `9863a95` was **418**; WI-6 adds **52**. The merge was clean — no
conflict this time. `lsappinfo visibleApplicationCount` 7 before and after.

## What needs a human

Unchanged from WI-5 and not added to: **the titlebar** (human item 2 — does it read exactly
*Terminal Game*), **the type size** (human item 3), **whether the box-drawing glyphs look
joined**, and **the Dock tile** the suite now raises. WI-6 puts no new question in front of
anybody.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
