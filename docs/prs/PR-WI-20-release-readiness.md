# WI-20 — release readiness

**Branch:** `r7/wi-20-release-readiness`, cut from the tip of `main` at `c57fce3`.
**The last item in the run.**

| File | |
|---|---|
| `docs/findings/WI-20-release-readiness.md` | the counts, the requirement status read carefully, and the setup recipe. |
| `README.md` | *(+)* **Playing the game** — how to run it. |
| `terminal_game/__init__.py` | *(+)* GAME-1, which was claimed by nothing. |
| `terminal_game/shell/game.py` | *(fixed)* a game ending between two beats left a timer outstanding. |
| `tests/test_game.py` | *(+2)* that defect, both routes into it. |

---

## The counts, both of them

| | |
|---|---|
| `.venv/bin/python -m pytest -q` | **967 passed, 0 failed, 0 skipped, 10 deselected** |
| `... -m "needs_window or not needs_window"` | **977 passed, 0 failed, 0 skipped, 0 deselected**, 17.49 s |

**The second is the first run in the project with all ten window tests together.** There
were four when it became this item's requirement.

| | before | after |
|---|---|---|
| crash reports | **14** | **14** — zero new |
| visible applications | **7** | **7** — nothing left behind, nothing lost |

Under a **180-second deadline in a parent process**, not a pytest timeout, because a hang
inside `mainloop` is not something pytest can interrupt. It finished in 17.65 s.

## That run found a real defect, which is the whole argument for requiring it

First attempt: **1 failed, 974 passed.** Lane C's
`test_the_real_entry_point_runs_and_reaps_itself`:

> **A game that ends between two beats left a scheduled beat outstanding.**

`Game._schedule` declines to book the *next* beat once the session stops accepting play —
but it runs *after a beat*, not after a quit. So `q`, the close button, or `run_game`'s
watchdog would end the game with an `after` still pending. `timer_is_running` reported
`True` for a finished game, and on a shared Tk interpreter the callback was still live and
still fired.

**Nothing in the default suite could have seen it.** It lives in the assembly's shutdown
path and is reachable only by running the real entry point on a real window.

**Two tests, not one** — the `q` route and the close-button route. `run_game`'s watchdog
closes the window rather than sending a key, so a fix handling only the quit intent would
have left the real entry point exactly as it was.

**Counted honestly: WI-20 changed product code**, which its bar did not anticipate. A
release-readiness item that finds a red test must fix it or report the suite as red.
Reporting green was not available.

## The two rows a reader will get wrong if they skim

**WIN-4 — the window is placed, and WIN-4 is still not met.** Both true, and the first
makes the second easy to miss. WI-14b/14c wired the placement WI-15 built and nobody
called; the shipped reader still follows nothing, so it centres on the main display
instead of tracking the player's last window. **"Placement fixed" and "WIN-4 met" are not
the same sentence.**

**WIN-5, END-5, END-6 — 34 tests, answering a question we chose.** These are contradiction
C-1, which cannot be resolved by testing because the requirements disagree with each
other. The suite pins **assumption P1** thoroughly. It does not pin the requirement. A
green suite here means *we implemented what we assumed*.

Nor is **WIN-2's comfort** met by a green suite: 400 × 570 is measured, "large enough to
read comfortably" is not testable and never will be.

## GAME-1 now has somewhere it is stated

WI-18 found it claimed by no test, no source and no docstring — realised by everything and
owned by nothing. The package docstring says it. One line, and it turns an assumption into
a claim. Lane B suggested it and left the call to me; I took it because this was the last
chance and it costs nothing.

## What is still for a person

Five checks, two minutes, in `docs/findings/WI-17-human-verification.md`, each written as a
**failure shape** rather than "does it look right". Plus the WIN-4 decision, with its cost.

**And the sentence this run is handed over with: nobody has yet seen this game.** It has
opened on this desktop five times across four items and closed itself in about a second
every time, unwatched. **977 tests pass and not one has seen a pixel.**

## Window hygiene

The pattern used four times before, at its largest: crash count and visible-application
list either side, deadline outside pytest, reaped on the failure path — the runner exits
non-zero on a timeout or a new crash report rather than letting a kill look like a pass.
Never a second `tkinter.Tk()`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
