# WI-18 — The wiring

**Lane:** DEV-A · **Branch:** `r6/wi-18-the-wiring`, cut from `main` at `a9af24a`
**Depends on:** WI-4, WI-14, WI-15, WI-16, WI-17 — all landed · **Mode:** non-local

**Announcement for the other lanes, per the first-lander rule.** Two names land here that
somebody else may want: **`terminal_game.shell.game.compose_picture`** — the two lines that
bind WI-13's row 29 into WI-12's picture, now with a home in production — and
**`GameCollaborator`**, the key-to-intent dispatch. Grep for them rather than writing a
fifth and a second copy.

---

## The game

```
/usr/bin/python3 -m terminal_game
```

One command. Seed a random source, lay out a maze, build the opening position, measure the
font, ask where the window goes, create it at that anchor and that size titled *Terminal
Game*, paint the first frame **before** the event loop is entered, start ticking, hand over
— and when the session ends, close the window and exit with a code that tells the truth.

Two files: `terminal_game/shell/game.py` is the composition root, the one place that knows
about all four layers at once; `terminal_game/__main__.py` is the command, and contains
nothing but the call.

## The two traps, and why they are assertions and not notes

Both were **measured on a real window in WI-17**, and neither would have been found by
reading the code, because the code beneath them is correct.

### 1. A crashed game exits looking clean

Tk swallows an exception raised inside an `after()` callback, so the session cannot raise:
it routes a failure into the same shutdown path `q` uses and keeps it on `session.failure`.
Measured consequence — the window is reaped, the phase reaches Ended, **stderr is empty**,
`run()` returns **normally**, `error` is **null**, and the process would exit **0**.

So `Game.exit_code` reads that field and is the only thing that distinguishes a crash from
a finished game. `tests/test_game.py` asserts it four ways, including one test that
**deliberately does not wrap `run()` in `assertRaises`** and says why in a comment: `run()`
returning is not evidence of anything, which is exactly why `exit_code` has to exist.

### 2. The close button would defeat the first

`WindowOwner.open()` binds the close request to its **own** `end_session`, so pressing the
close button takes the window and the process away *without the session ever knowing* —
skipping its shutdown, and the failure check with it. Measured in WI-17: the phase was
still `playing` afterwards.

`Game.start()` therefore **rebinds the close request to the session's `quit`**, after
opening. The binding is last-writer-wins, so **`terminal_game/shell/window_owner.py` is
untouched** — it is DEV-C's landed file — and its `end_session` still runs, because it is
what the session was handed as its `shut_down`.

## The three lines the layer rule forces

A key reaches the session as `move(Direction)` or `quit()`, never as an `Intent`: `Intent`
is Presentation vocabulary and the Application layer may not name Presentation. Amendment 5
calls that the layer rule biting correctly and puts the translation here. It is
`GameCollaborator.on_key`, and it is three lines.

## The tests — the join only

`tests/test_game.py`, **29 tests, no window anywhere**; the toolkit is WI-3's
`RecordingToolkit` throughout, and `tkinter._default_root` is still `None` afterwards.

The maze is WI-5's, the opening position WI-6's, the rules WI-11's, the picture WI-12's and
WI-13's, the session's three states WI-15's, the window WI-3's, the keys WI-9's — and a
whole game end to end is **WI-19's**, headless and already landed. None of that is
re-asserted. What is asserted:

| | |
| --- | --- |
| The entry point assembles the **real** components | a real `Session` over a real `Maze`, a real `WindowOwner` at the size and place it was given, and the collaborator holding that session |
| START-5 | a first frame is painted **before** `run_event_loop` is called, on the drawing target the window gave back |
| The key dispatch | each arrow → a move in its direction; `q` and `Q` → a quit; five unmapped keys → **nothing asked of the session at all** |
| Ending | `q` takes the session to Ended and closes the window, **exactly once** across three routes |
| **Trap 1** | a crashed game has `exit_code` 1, still loses its window, leaves nothing scheduled, and `run()` does **not** raise |
| **Trap 2** | the close button takes the session to **Ended**, still closes the window exactly once, and closing twice is harmless |
| The picture seam | row 29 of `compose_picture(state)` is **exactly** `status_row(...)` — WI-13's row, not one of the wiring's own |
| The command | `terminal_game.__main__.main` **is** `terminal_game.shell.game.main` |

## Cleaning up rather than adding to it

`tools/window_manners.py`'s `KeyDispatcher` was three throwaway lines of dispatch written
when WI-18 had not landed, explicitly flagged in WI-17's PR as *not* a proposal for this
one. It now **delegates to `GameCollaborator`** and keeps only its notebook, and the six
duplicated dispatch tests in `tests/test_window_manners.py` are replaced by three that
assert the notebook. Both are my own landed files in both directions, which is the only
reason this was mine to do.

## One conflict with WI-20a, resolved — **and it touched DEV-C's file**

Merging `origin/main` brought DEV-C's specification sweep in, and its completeness test
went red. Not a textual conflict: `docs/TRACEABILITY.md` cites
`tests/test_window_manners.py::AKeyReachingTheSessionTest::test_an_unmapped_key_asks_the_session_for_nothing_at_all`
as one of three pins for **CTRL-5**, and this branch **moved that test** — same class name,
same method name — into `tests/test_game.py`, because the throwaway dispatch it covered was
replaced by the production `GameCollaborator`.

**Resolved by updating the path in that one citation, and adding WI-18 to the row's
work-item column.** That is the smallest change that leaves the document true. Nothing the
sweep *claims* has changed, CTRL-5 is still pinned by three tests, and the pin is arguably
stronger: it now names the production collaborator rather than a script's wrapper.

**DEV-C, this is the one line of yours I touched, and I would rather you knew than
found it.** The alternative was keeping a duplicate test alive purely to satisfy a
citation, which would have been the wrong reason to keep a test. It is relayed through the
conductor as well as being here.

## Deviations, stated as deviations

* **`tools/play_the_game.py`** — four bounded, self-closing exercises against the assembled
  game. Additive. It exists because `python3 -m terminal_game` is unbounded by design and
  an agent must never launch that, and because traps 1 and 2 need showing on real Tk. It is
  not WI-21's script: WI-21 asks three named questions of a person.
* **`--seed` and `--seconds` on the production entry point.** `--seconds` is what the
  bounded exercises are run with, and WI-21 will want it. Both are defensible in a shipped
  game — reproducibility and a demo timeout — but they are additions the plan did not ask
  for.
* **`compose_picture` lives in the Shell**, in the composition root, rather than in
  Presentation. It joins two Presentation modules, so Presentation is arguably its home —
  but both of those files belong to another lane and a new Presentation module for two
  lines would be worse. **The same two lines also exist in `tools/the_look.py` and
  `tests/scripted.py` (both DEV-B's) and `tools/window_manners.py` (mine).** This is the
  only copy in production. Consolidating the rest is a one-line change each and is left for
  whoever holds WI-22, because three of the four are not mine to edit.
* **The branch was cut from `a9af24a`, not the `e44d9cc` I was given** — WI-19 landed in
  between and `a9af24a` is its merge, so cutting from the tip avoided an immediate merge.

## What four real windows said

Full numbers in `docs/findings/WI-18-the-game-on-screen.md`. **Four windows, four reaped,
no orphan.** This is *"covered by observation, not by test"*: the suite cannot reach any of
it, because it is forbidden from constructing a toolkit interpreter.

**The game ran, and it played.** `first-frame`: title `Terminal Game`, 400 × 570 from Menlo
16pt at 10 × 19 a cell, **706 canvas items and every one of kind `text`** — SCRN-2 on the
real generated maze — and **8 frames painted in 1.188 s with nothing pressed**, which is
START-5 and GHOST-1 observed rather than inferred. `played`: six real keys, **the player
moved and the score reached 2**; `Left` into a wall cost nothing (CTRL-3), `Down` onto an
eaten square scored nothing (SCORE-3), `z` did nothing (CTRL-5), `q` ended it.

**Trap 1, closed.** `crash` reproduced every one of WI-17's measurements — window reaped,
phase Ended, **stderr empty**, the exception **not** coming out of `run()`, `error`
**null** — and the process exited **1**. Nothing about the failure became visible; the exit
code changed anyway. That run matters more than the test that pins it, because a test
asserting that a check performs the check is close to agreeing with itself.

**Trap 2, closed.** `close` left the session's phase **`ended`**, where WI-17 measured
**`playing`** on the same route. One word, and it is the difference between a clean exit
and a silent crash — with the phase left at `playing` the session's shutdown never ran and
trap 1's check was skipped on every close-button exit.

**Nothing was echoed** on any of the four runs: `stdout` and `stderr` empty strings
throughout, the crash included.

## Contradictions found

**None in the plan or the architecture.** Everything WI-17 measured reproduced exactly.

**C-7 confirmed, and in the better of the two ways.** The window opened at the fixed
fallback (120, 120) on all four runs, and the report shows `anchor_query_saw_something:
false` with `anchor_query_failure: null` — so the query **ran and saw nothing**. It did not
fail and it did not prompt, which is the distinction C-7 rests on, recorded rather than
inferred.

**A11 deliberately untouched.** No modifier state crosses the key seam, so control-Up moves
the player. Amendment 9 ruled it a known gap; `GameCollaborator` passes the `KeyPress`
through unchanged, so widening the seam later costs nothing here.

## What still needs a human

* **A1 — the titlebar.** Not closed here.
* **A10 / SCRN-3 — do the strokes meet.** Not closed here, and not rounded up.
* **A3 — WIN-5 against END-5 and END-6.** Implemented on the architect's reading in WI-15,
  one line, unchanged by this item.
* **C-7 — the window opens at its fixed fallback position on this machine**, because Tk
  reports the pointer in whole-desktop coordinates while describing only the primary
  display. Expected, not a defect, and `--exercise first-frame` records what the anchor
  query actually returned.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
