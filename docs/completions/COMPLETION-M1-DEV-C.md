# M1 — developer C — completion record

**Iteration:** M1, *A picture in a window of its own*.
**Lane:** C. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-a319e57ac3a444133`.
**Recorded** 17 Sep 2026, 02:30Z.

## What was finished

**WI-6 — the window owner.** Lane C's other M1 item, **WI-8 (the opening position)**, was
**moved to lane B** by the technical lead: section 7 sequences WI-8 → WI-10 as a pair
touching the same ground, and lane B already owned WI-10, so one developer owning the game
state end to end removes that seam rather than managing it. It is not recorded here.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#90](https://github.com/replicant1/NewTerminalGame/pull/90) | WI-6: the window owner | `main` | `ea00019` |

Merged by me. Branch `r7/wi-6-window-owner`, cut from `main` at `9863a95`, merged with
`origin/main` at `a2373a9` before being marked ready — **no conflict**.

**Files added:** `terminal_game/shell/window.py`, `tests/test_window.py` (52 tests, 2 of
them `needs_window`), `docs/prs/PR-WI-6-window-owner.md`,
`docs/progress/r7-wi-6-window-owner.md`.

## The four requirements

**WIN-1** a real native toplevel of this process's own, holding the character grid and
nothing else. **WIN-3** titled exactly *Terminal Game*, checked as an exact string with
nothing appended — under candidate 2 nothing composes around it, so the architect's A1 and
C2 fall away with the terminal they were about. **WIN-2** the window asks for the size
WI-5's metrics computed, and cannot be resized. **WIN-5** `close()` is idempotent, fires
`on_close`, leaves the loop and destroys the window — and **does not call `sys.exit`**,
because destroying the window is what makes `run()` return and ending by running out of
work is both the honest mechanism and the only one testable without a subprocess.

## The defect the user saw, and the fix

**My own `needs_window` run hung with a window on the user's screen for about two minutes.**
Killed at 02:04:17Z by pid — my own process — with `visibleApplicationCount` back to its
prior value immediately and nothing left behind.

**`mainloop` belongs to the Tk interpreter, not to a window.** `close()` destroyed the
window; when the window owns the interpreter the root goes and `mainloop` returns, but when
it does not — a Toplevel on somebody else's root — the interpreter survives and **`mainloop`
never returns**. A window gone from the screen and a process that will not end.

**Fixed structurally:** `close()` now calls `quit()` before `destroy()`, unconditionally, so
the guarantee no longer depends on who constructed the window. Proven by the very tests
that hung — they now pass in 1.14 s, run under an external subprocess deadline.

**One Tk interpreter per process.** `GameWindow` creates the root when given no master and a
`Toplevel` when given one, because a `mainloop` entered after other roots had been created
and destroyed in the same process **segfaulted the interpreter**. Residual, stated plainly:
a second `tkinter.Tk()` anywhere in one process can still crash this build.

## Measurements that went to other lanes

- **`mainloop()` works on a mapped window** and returns when the window is destroyed from
  inside an `after()` callback — 629 ms. **This retired the lead's logged risk** that the
  event loop shared the path that hangs `update()`, so WI-7 did not find it on the desk.
- **`mainloop()` also runs on a withdrawn root**, `after()` fires, `quit()` returns in
  60 ms, nothing on screen. **WI-14's cadence and WI-16's journeys need no real window.**
- A non-resizable mapped toplevel reports `state() == "zoomed"`, not `"normal"`.
- `event_generate` on a withdrawn toplevel delivers nothing.
- `resizable()` returns the **string** `"0 0"`, whose every character is truthy — which
  cost me a real bug: `any(bool(f) for f in ...)` said a fixed window was resizable.

## Crash accounting

**Eleven interpreter crashes between 01:58:24Z and 02:00:51Z are mine**, from re-running one
crashing test file while bisecting it — one defect, about eleven runs. **Seven crashed at
interpreter *exit*, after pytest had printed its results**, so the command output looked
clean and only one was visible to me at the time. The `.ips` directory is the reliable
detector and I now count it either side of anything that maps a window.

## Suite state

```
.venv/bin/python -m pytest -q          →  586 passed, 0 failed, 0 skipped, 2 deselected
.venv/bin/python -m pytest -q -m needs_window    →  2 passed
```

On `ea00019`, `main` with WI-6 in it, at 02:07:54Z. Baseline when the branch was cut from
`9863a95` was **418**; WI-6 adds **52**.
