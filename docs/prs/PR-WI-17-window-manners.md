# WI-17 — The window's manners

**Lane:** DEV-A · **Branch:** `r6/wi-17-window-manners`, cut from `main` at `67de3f1`
**Depends on:** WI-3, WI-4, WI-9 — all landed · **Mode:** non-local, real pull request

**Announcement for the other lanes, per the first-lander rule.** Nothing in this branch
lands a shared name. It adds one script (`tools/window_manners.py`) and one test module,
and it changes **no production code at all**. If you were waiting on this item for
something, the thing you want is the finding, not the code — see
`docs/findings/WI-17-real-window-manners.md`.

---

## What this item turned out to be

Amendment 2 shrank WI-17 to mostly verification and then attached a warning to it. Two
things it was going to build had already landed from WI-4's branch — the window is
force-focused at start-up, and its own close button ends the session — so those are
**verified here, not rebuilt**. What replaced them is the substance: the three
**real-medium exercises** section 4 of the plan says this item owes, because *proved by a
double is not proved*.

That rule exists because of this item's own dependency. **WI-3 was green and its probe
passed, and neither ever pressed a key.** With Tk-internal focus alone Tk delivers no key
event at all, so the game would have been unquittable and every test would still have been
green. Everything below is therefore a measurement rather than an assertion.

---

## The one thing you should read if you read nothing else

**A crashed game exits looking clean, and now that is measured rather than reasoned.**

`--exercise fail-session` ran a real `Session` over a real maze in a real window and made
its composer raise on the fourth picture. What happened:

| | |
| --- | --- |
| The window was reaped | **yes** |
| The session reached Ended | **yes** |
| Anything printed to stderr | **no** |
| The exception came back out of `owner.run()` | **no** |
| `report["error"]` | **null** |
| Where the crash was recorded | **`session.failure`, and nowhere else** |

The session deliberately does not re-raise — it cannot, because Tk swallows an exception
raised inside an `after()` callback — so it routes the failure into the same shutdown path
`q` uses and keeps it on `session.failure`. The loop then returns normally and the process
exits 0. **Amendment 5 tells WI-18 to check that field. This is the measurement behind the
instruction**, and WI-18 (same lane) will assert it rather than remember it.

---

## What was exercised, and what each one said

Five windows, one per exercise, each bounded by a backstop scheduled on Tk's own scheduler
**before** the event loop is entered, each reaped in a `finally`, each acting only on the
handle captured at the moment of creation. **5 opened, 5 reaped, 0 modal sheets, 0
orphans** — confirmed afterwards with `pgrep` and with System Events counting 0 GUI Python
processes.

### 1. `--exercise window` — the manners themselves (1.386 s)

| Measured | |
| --- | --- |
| `root.title()` | `Terminal Game` |
| Window, asked and got | 400 × 570 |
| `root.wm_resizable()` | the **`str`** `"0 0"` — the WI-3 finding, confirmed |
| A synthesized resize request | window still 400 × 570, canvas still 696 items, **every cell position unchanged** |
| Widget classes in the window | `Tk`, `Canvas` — and nothing else |
| `insertwidth` / `takefocus` / focused canvas item | `0` / `0` / none |
| stdout, stderr during the run | empty, empty |

The resize row is the item's *"a resize request does not change the grid"*, and the widget
row is its *"no caret is ever enabled"* — the window's half of SCRN-7, which had no test
anywhere before this branch.

### 2. `--exercise keys` — a real key press, **acted on** (1.483 s)

WI-4 pressed keys and wrote them down. That is a weaker claim than this item needs, so this
one runs each key through WI-9's `translate` into a real `Session` and watches the player.

| Key | Became | The real player |
| --- | --- | --- |
| `Up` | Move north | (9,13) → **(9,12)** |
| `Left` | Move west | (9,12) → (9,12) — **into a wall, and nothing at all happened** |
| `Down` | Move south | (9,12) → **(9,13)** |
| `Right` | Move east | (9,13) → **(10,13)** |
| `z` | nothing | unchanged |
| `q` | Quit | session **Ended** at 1.483 s against a 4 s backstop |

Nine ticks arrived, thirteen frames were painted, and stdout and stderr were empty
throughout. **The squares are exactly what the pure Domain predicts for that seed** — the
same four moves replayed headless give the same four squares — so the whole WI-9 → WI-15 →
WI-11 chain agrees with itself through a real window. The `Left` row is **CTRL-3 observed
on a screen** rather than only in a unit test.

### 3. `--exercise fail-collaborator` — a real exception in a real `after()` (0.496 s)

The collaborator raised on its third tick. `WindowOwner` reaped and re-raised, Tk caught the
re-raise and handed it to `report_callback_exception`, the adapter kept it and stopped the
loop, and `run_event_loop` re-raised it once `mainloop()` had returned. **The exception came
back out of `owner.run()` and the window was reaped.**

Worth noting on its own: **stderr was empty**. The adapter's hook replaces Tk's default,
which prints a traceback, so CTRL-5's *"nothing is echoed anywhere"* survives the failure
path as well as the ordinary one.

### 4. `--exercise fail-session` — see above.

### 5. `--exercise close` — the real close button (0.981 s)

A window manager does not call a Python function; it sends `WM_DELETE_WINDOW` and Tk
evaluates the Tcl command registered against it. This invokes that command, which is the
real path rather than a stand-in for it — the one thing it cannot reproduce is a hand on a
mouse. The process ended at 0.981 s against a 4 s backstop with no orphan.

**And it found something, which is why it was worth running.** `phase_at_the_end` was
`playing`, not `ended`: `WindowOwner.open()` binds the close request to its **own**
`end_session`, so the close button takes the window and the process away and **never reaches
the session**. Every promise WI-17 makes still holds — closed exactly once, no orphan, no
sheet. But it is a **WI-18 wiring note**: WI-18 must rebind the close request to the
session's `quit` after opening, or a close-button exit skips the session's shutdown and,
worse, skips the `session.failure` check above. `bind_close_request` is last-writer-wins, so
**no change to `WindowOwner` is needed** — which matters, because that file is DEV-C's and
this branch does not touch it.

---

## What is verified rather than built

Per amendment 2, and said explicitly because the amendment asks for it:

| WI-17 promise | Where it already lives | What this branch did |
| --- | --- | --- |
| Force-focused at start-up | `TkToolkit.create_window`, landed on WI-4's branch | **verified** — six keys arrived at a real window |
| The close button ends the session | `WindowOwner.open`, landed on WI-4's branch | **verified** — exercise 5, with the caveat above |
| Non-resizable, and the grid is never other than 40 × 30 | `WindowSpec.resizable`, tested by WI-3's doubles | **verified on real Tk** — exercise 1 |
| Closing twice is harmless and closes once | `tests/test_window_owner.py`, WI-3 | **not re-asserted** — it is WI-3's and re-asserting it would turn one defect into two red files |
| No caret on the *surface* | `tests/test_grid_surface.py`, WI-2 (29 tests, including a caret-recording double) | **not re-asserted.** This branch owns only the *window's* half: no text-entry widget exists |
| Unmapped keys mean nothing | `tests/test_input_translator.py`, WI-9 | **not re-asserted** — only the join, that an unmapped key leaves the session alone |

---

## The automated tests

`tests/test_window_manners.py`. They open nothing: the toolkit is WI-3's `RecordingToolkit`
throughout, and `tkinter._default_root` is still `None` afterwards, which WI-10's rule 5
now guards.

What they own, and nothing else:

* **The script cannot run unbounded.** The backstop is scheduled before the event loop is
  entered, at the stated lifetime, and an action asked for at or past it is refused rather
  than silently never happening.
* **It reaps on the failure path, and says so truthfully.** A loop that raises still leaves
  `window_reaped` true in the report and an `error` recorded.
* **`exit_code_for` notices a session failure**, which is the WI-18 hazard encoded as four
  lines: a run whose `error` is null but whose session recorded a failure is **not** a clean
  exit.
* **The key join**: an arrow reaches the session as a `move`, `q` reaches it as a `quit`,
  and an unmapped key reaches it as nothing at all — asserted against a fake session, so a
  defect in the dispatch turns one test red and none of WI-9's.
* **No production module constructs a text-entry widget** — `Entry`, `Text`, `Spinbox`,
  `ttk.Entry`, `ttk.Combobox` — nor calls `icursor`. SCRN-7's *"no caret is ever enabled"*
  at the window's level, which nothing guarded before. It is written so it cannot pass
  vacuously: it fails if it finds no modules to inspect.

---

## Deviations, stated as deviations

* **`tools/window_manners.py` contains a `KeyDispatcher`.** Amendment 5 puts the intent
  dispatch in **WI-18's** collaborator, and that is where the production one belongs. This
  one is three lines living in a throwaway script, and it exists because *"a real key press
  being acted on"* cannot be shown without it. It is not a proposal for WI-18's.
* **The same script assembles a real maze, session and composer.** For the same reason, and
  with the same disclaimer: WI-18 owns the entry point.
* **`docs/completions/COMPLETION-M3-DEV-A.md` gains a second record** rather than a new
  file. The four document shapes allow one completion per lane per iteration and that file
  already exists for this lane and iteration, written by the agent that held the lane
  before me. Appending a separately-headed WI-17 record leaves their text untouched and
  avoids inventing a fifth shape. Flagged for a ruling.

## Contradictions found

**None in the plan or the architecture.** Both Tk behaviours the plan carried into this item
were confirmed exactly as written — the `after()` swallow and the `resizable()` string.

## What still needs a human

Unchanged, and this branch deliberately did not convert any of it:

* **A1 — does the titlebar read exactly `Terminal Game`?** Tk read the string back unchanged
  on all five windows. That is not a person seeing a titlebar, and it is not an answer.
* **A10 / SCRN-3 — do the blue double lines' strokes meet?** Equal advance widths prove the
  cells line up; they do not prove the strokes touch. Not measurable. Not touched here.

**On the new standard in section 4** — *a negative about the user's environment cannot be
established by an agent running the thing that might do it*. One claim in this branch fell
under it and has been restated rather than dropped: **"no modal sheet was raised"** is now
made by the structural route, not the observational one. The sheet is raised by an
application still holding a window whose other process is alive; under candidate 2 there is
no second application, so killing the process takes the window with it and there is nothing
to raise. What was *observed* is the weaker, sufficient fact — five processes exited on
their own and `pgrep` found none afterwards. Nothing else in this branch claims a negative
about the environment: the stdout/stderr capture is of this process's own streams, and the
absent caret is established structurally, by showing no caret-bearing widget is ever built.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
