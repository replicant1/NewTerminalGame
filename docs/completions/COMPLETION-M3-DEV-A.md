# COMPLETION — M3, DEV-A

**Run:** 6 · **Iteration:** M3, *a whole game, with no window*
**Lane:** DEV-A · **Work items finished:** **WI-13** and **WI-15**
**Mode:** non-local — real pull requests, merged by the developer

**Why WI-13 is recorded here rather than in `COMPLETION-M2-DEV-A.md`.**
WI-13 is an M2 item; amendment 3 moved it into this lane, and this lane
picked it up in the same sitting as WI-15. `COMPLETION-M2-DEV-A.md` is a
landed document written by the agent that held this lane before me, and
rewriting somebody's finished record to insert an item they did not build is
worse than recording it in the iteration it was actually done in. Both items
are below.

---

## What was finished

### WI-13 — The status line

Branch `r6/wi-13-status-line`, cut from `main` at `6cee5c9`. Pull request
**#44**, merged by DEV-A as **`671f0e5`** once green.

| File | What it is |
| --- | --- |
| `terminal_game/presentation/status_line.py` | three per-ending templates, `status_text`, `status_row` |
| `tests/test_status_line.py` | 28 tests — and the only status-line literals in the project |
| `docs/findings/WI-13-status-line-literals.md` | C-3 and C-4 as numbers taken from the specification |
| `docs/prs/PR-WI-13-status-line.md` | the pull request's body |
| `docs/progress/r6-wi-13-status-line.md` | the progress log |

Requirements: **STAT-1**, **STAT-2**, **STAT-3**, **SCRN-6**, and **SCORE-5**
in part.

### WI-15 — The session controller

Branch `r6/wi-15-session-controller`, cut from `main` at `671f0e5`. Pull
request **#47**, merged by DEV-A as **`b48209f`** once green.

| File | What it is |
| --- | --- |
| `terminal_game/application/__init__.py` | a new subpackage for the Application layer |
| `terminal_game/application/session.py` | `Phase`, `Session`, `new_session` |
| `tests/test_session.py` | 44 tests |
| `docs/prs/PR-WI-15-session-controller.md` | the pull request's body |
| `docs/progress/r6-wi-15-session-controller.md` | the progress log |

Requirements: **GAME-3**, **START-5**, **CTRL-4**, **END-5**, **END-6**,
**WIN-5** under assumption A3, and **GHOST-1** in part.

## The state of the test suite as it was left

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 533 tests in 4.251s

OK
```

**533 passed, 0 failed, 0 skipped**, on `main` at `b48209f`. **28 are
WI-13's and 44 are WI-15's.** The counts reconcile: 374 on `main` at
`6cee5c9`, +28 for WI-13 to 402, then WI-8 and WI-12 landed from DEV-C and
DEV-B taking it to 489, then +44 for WI-15 to 533.

No test opens a window, reads a clock or reaches for a global random source.
Measured after WI-15: `tkinter._default_root` is `None` once every test
module has been imported, so WI-10's rule 5 is unaffected, and `grep` finds
no mention of `presentation`, `shell` or `tkinter` anywhere under
`terminal_game/application/`.

**No mutation test was written and no working code was broken to watch a
test go red.** That is prohibited, and none was invented for either item.

## The seams this lane now owns, and who consumes them

**WI-13 — the status line.** `status_text(score, outcome)` and
`status_row(score, outcome)`. A7 confines every status-line literal to this
item, and the prohibition is about the *item*, not the person: **WI-12 and
WI-19 must build an expected row 29 by calling these, never by typing the
line out.** WI-19 is the one to watch — it is asked to assert whole frames
as text, and a hand-typed 30-line picture would embed the literal without
anyone intending it.

No automated scanner forbidding the literal elsewhere was written, and
deliberately: it would fail exactly that honest work. Amendment 2's lesson —
a rule stated wrongly is worse than no rule — applies directly.

**WI-15 — the session, and the headless game.**

```python
session = new_session(maze, compose=..., show=..., random_source=..., shut_down=...)
session.start(); session.tick(); session.move(direction); session.quit()
session.phase    # Phase.PLAYING | DECIDED | ENDED
session.failure  # the exception that ended it, or None
```

**There is no clock object.** The session reads no clock and schedules
nothing. The window owner already owns the timer and starts it before the
event loop; a session-owned clock would be a second one that only tests use.
A whole game runs headless as fast as it can be driven, which is what WI-19
needs, and `tick()` is the seam. This is a deviation from the plan's
ownership table, which named "the clock seam" as DEV-A's to build, and it is
reported as one.

**A key reaches the session as `move(Direction)` or `quit()`, not as an
`Intent`.** The Application layer may not name Presentation, where WI-9's
`Intent` lives. WI-18's collaborator is already unpacking a `KeyPress` and
calling `translate`, so the dispatch lives there and exists once.

## WI-12 landed mid-flight, and the seam held

`origin/main` moved to `a08b11b` while WI-15 was open. It merged cleanly,
with no conflicts.

DEV-B's `compose_frame(state, status_row, walls=...)` takes two arguments
where WI-15's seam takes one. **That is differently spelled, not wrong**, so
section 2's "conforming would change behaviour" case did not arise. The plan
requires WI-12 to take row 29 as a value and never compose its text, so
binding WI-13's row in is the caller's job:

```python
def compose(state):
    return compose_frame(state, status_row(state.score.points, state.outcome))
```

Verified end to end **outside the suite**, against the real composer, the
real wall glyphs, the real status line and a real generated maze: 40 ticks
gave 41 frames, each 30 × 40, row 29 reading
`'score 0    arrows, q quits              '`, and `q` reaching
`Phase.ENDED` with no failure. The answer was left on PR #45 so it sits with
DEV-B's work as well as with mine.

## What is still with the user, and unchanged

Three questions, none of them settled by this lane:

1. **C-2 — WIN-5 against END-5 and END-6.** We proceed on **A3**, and it
   lands in one line of `Session._advance`: the outcome is decided, the
   final picture stands, `q` ends it. There is a test named for the
   assumption, `test_deciding_does_not_shut_the_session_down`.
2. **C-3 and C-4 — the status-line literals.** We proceed on **A7**. Now
   recorded as numbers in `docs/findings/WI-13-status-line-literals.md`, and
   confined to two files.
3. **A8 — the dot on the losing turn**, and **the ghost's start-square
   tie-break** from WI-6. Both inherited, neither touched. If A8 is
   reversed it is a WI-11 follow-up branch and **never** a WI-15 change:
   the step order lives in WI-11 and nowhere else, per caution C6.

## What the next item in this lane inherits

**WI-18 (the wiring)** has everything it needs and no rules of its own to
invent. Its entry point is: seed a random source, generate a maze,
`new_session(...)` with the two-line `compose` above, open the window, size
it from the surface's metrics, `session.start()`, then `WindowOwner.run()`.
Two things it must not forget:

- the `SessionCollaborator` it hands the window owner is where the intent
  dispatch lives — `translate`, then `quit()` or `move(direction)`;
- **check `session.failure` after `run()` returns** and exit non-zero if it
  is set. A failure inside a tick is routed to the shutdown path rather than
  raised, because Tk swallows a raise from an `after()` callback; if nobody
  reads `failure`, a crashed game exits looking like a clean one.

---

# COMPLETION — M3, DEV-A, second record: **WI-17**

**Added by the agent that took the lane over after WI-15.** Everything above
this line is the previous agent's record of WI-13 and WI-15 and is left
exactly as it was written. WI-17 is an M3 item in this lane and belongs in
this file, and the four document shapes allow one completion per lane per
iteration — so it is recorded here as a second, separately-headed record
rather than by rewriting somebody's finished document or by inventing a
fifth filename. **Flagged as a deviation for a ruling.**

**Work item finished:** **WI-17 — the window's manners**
**Mode:** non-local — real pull request, merged by DEV-A
**Amendment 4** moved this item into this lane from DEV-C.

---

## What was finished

Branch `r6/wi-17-window-manners`, cut from `main` at `67de3f1`. Pull request
**#56**.

| File | What it is |
| --- | --- |
| `tools/window_manners.py` | five bounded, self-closing exercises against real Tk |
| `tests/test_window_manners.py` | 27 tests, no window anywhere |
| `docs/findings/WI-17-real-window-manners.md` | what five real windows said |
| `docs/prs/PR-WI-17-window-manners.md` | the pull request's body |
| `docs/progress/r6-wi-17-window-manners.md` | the progress log |

**No production code was changed.** Amendment 2 shrank this item to mostly
verification and it stayed shrunk: the force-focus and the close-button
wiring had already landed from WI-4's branch, and they are verified here
rather than rebuilt.

## The suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

**601 passed, 0 failed, 0 skipped** on the branch. The base at `67de3f1` was
measured separately at **574**, by moving this branch's one test module aside
and running the same command, so the 27 reconcile exactly and nobody has
retyped a number.

## The screen

**Five windows opened, five reaped, no modal sheet, no orphan.** Lifetimes
0.496 s to 1.483 s, each ended on its own Tk scheduler well inside a 4 s
backstop, each reaped in a `finally`, each acted on only through the handle
captured at the moment of creation. Afterwards `pgrep` was empty and System
Events counted 0 GUI Python processes.

The screen gate from amendment 4 was used as intended: held exclusively,
granted by the conductor after DEV-B released it, and released the moment
the last window was gone so DEV-C could have it.

## The one thing this item found

**A crashed game exits looking clean.** A real `Session` whose composer
raised inside the event loop had its window reaped, reached Ended, printed
nothing, returned from `owner.run()` with **no exception**, and would have
exited **0**. The only evidence was `session.failure`.

That is not a defect — it is WI-15 doing what amendment 1 required, because
Tk swallows an exception raised inside an `after()` callback. It is a
measurement that turns amendment 5's instruction to WI-18 from a reasoned
precaution into an observed fact.

## What the next item in this lane inherits

**WI-18 (the wiring)**, on top of what the previous record already listed:

- **Check `session.failure` after `run()` returns.** Now measured, section 1
  of the finding. `exit_code_for` in `tools/window_manners.py` shows the
  shape in four lines, and this branch's tests pin it.
- **Rebind the close request after `open()`.** `WindowOwner.open()` binds it
  to its own `end_session`, so the close button never reaches the session —
  measured, `phase_at_the_end` was `playing`. `bind_close_request` is
  last-writer-wins, so WI-18 rebinds it to the session's `quit` and needs
  **no change to `WindowOwner`**, which matters because that is DEV-C's file.
- **The `KeyDispatcher` in `tools/window_manners.py` is not a proposal.**
  Amendment 5 puts the intent dispatch in WI-18's collaborator. The one in
  the script is three throwaway lines that exist so a real arrow key could be
  seen moving a real player.

## What is still with the user, and unchanged

- **A1 — the titlebar.** Tk read `Terminal Game` back on all five windows.
  Still not a person seeing a titlebar. Not converted into one here.
- **SCRN-3 — do the double lines' strokes meet.** Not measurable, not
  touched. Five developers have now left that line alone.
