# WI-18 — The game, on a real screen, for the first time

**Measured by:** DEV-A, WI-18, on this machine, with `tools/play_the_game.py`.
**Interpreter:** `/usr/bin/python3` — Python 3.9.6. **Toolkit:** Tk **8.5.9**.
**Windows opened:** four, each under 1.5 seconds, **each confirmed gone.**
**Screen gate:** held exclusively, granted and released through the conductor.

**This is "covered by observation, not by test"** in the sense section 4 now names. None
of it can be in the suite, because the suite is forbidden from constructing a toolkit
interpreter — which is the rule that keeps a window off the user's desktop. A sweep row
citing anything below must cite it as an observation, not tick it as tested.

```
/usr/bin/python3 tools/play_the_game.py --exercise first-frame
/usr/bin/python3 tools/play_the_game.py --exercise played
/usr/bin/python3 tools/play_the_game.py --exercise crash
/usr/bin/python3 tools/play_the_game.py --exercise close
```

Each opens one window, schedules everything on Tk's own scheduler before the event loop is
entered, keeps a backstop, and reaps in a `finally`. **The game itself —
`/usr/bin/python3 -m terminal_game` — is unbounded by design and an agent must never launch
it**; these four are what an agent runs instead.

---

## 1. The game runs, and it plays

**`--exercise first-frame`** — 1.188 s.

| Asked for | Measured back | |
| --- | --- | --- |
| title `Terminal Game` | `Terminal Game` | exact |
| 400 × 570 px, Menlo 16pt at 10 × 19 a cell | 400 × 570 | exact |
| black, not resizable | black, `0 0` | exact |
| position (120, 120) | (120, 120) | exact — see §3 |

**706 canvas items, and every one of kind `text`.** SCRN-2 observed on the real generated
maze rather than on the specimen picture, which is a different and larger drawing: nothing
but characters reached the screen.

**8 frames were painted in 1.188 seconds with nothing pressed.** The first was up before
the event loop was entered and the rest are the ghost moving at its own cadence. START-5 —
*"the game is under way the moment the window opens"* — and GHOST-1, both observed rather
than inferred.

**`--exercise played`** — 1.488 s, six real keys driven into the window this process
created.

| Key | What happened to the real player | |
| --- | --- | --- |
| `Up` | (9,13) → (9,12), **a dot eaten** | score 1 |
| `Left` | a wall — **nothing at all happened** | CTRL-3 |
| `Down` | back to (9,13), **already eaten** | SCORE-3, score still 1 |
| `Right` | (9,13) → (10,13), **a dot eaten** | score 2 |
| `z` | nothing | CTRL-5 |
| `q` | session **Ended** at 1.488 s against a 5 s backstop | CTRL-4, END-6 |

**The score reached 2 by somebody pressing keys at a window.** That is the whole
application — WI-9's translation, WI-18's dispatch, WI-15's session, WI-11's rules, WI-6's
dots, WI-12's and WI-13's picture, WI-2's surface, WI-3's window — agreeing with itself
through a real event loop. Thirteen frames, stdout and stderr empty throughout.

## 2. Both traps, closed on real Tk

These two are the reason this item had to do anything at all, and both are things WI-17
measured one level down.

### Trap 1 — a crashed game must not exit clean

**`--exercise crash`** — 0.550 s. A composer that raises on the fourth picture.

| | WI-17 measured | WI-18 measures |
| --- | --- | --- |
| The window was reaped | yes | **yes** |
| The phase reached Ended | yes | **yes** |
| Printed to stderr | nothing | **nothing** |
| The exception came out of `run()` | no | **no** |
| `error` | null | **null** |
| **The process's exit code** | **would have been 0** | **1** |

Every one of WI-17's observations reproduced exactly, and the last row is the item. Nothing
about the failure became visible — it is still silent, still unraised, still unprinted — and
the process now exits non-zero anyway, because `Game.exit_code` reads `session.failure`.

**Why this run matters more than the test that pins it.** `tests/test_game.py` asserts the
same thing against a recording double, and a test asserting that a check it can see
performs the check it can see is close to agreeing with itself. This is the run where the
check changes something an outside observer can measure.

### Trap 2 — the close button must reach the session

**`--exercise close`** — 0.987 s. The real `WM_DELETE_WINDOW` command, evaluated the way Tk
evaluates it when a window manager sends the message.

| | WI-17 measured | WI-18 measures |
| --- | --- | --- |
| Window reaped, exactly once | yes | **yes** |
| Orphan process | none | **none** |
| **Session phase afterwards** | **`playing`** | **`ended`** |

That single word is the difference between a clean exit and a silent crash: with the phase
left at `playing` the session's shutdown never ran, and the failure check in trap 1 would
have been skipped on every close-button exit.

`Game.start()` rebinds the close request to the session's `quit` after opening.
**`terminal_game/shell/window_owner.py` is not touched** — the binding is last-writer-wins,
and that file belongs to another lane. Its `end_session` still runs, because it is what the
session was handed as its `shut_down`; that is why the window still closes exactly once.

## 3. C-7, confirmed in the better of the two ways

The window opened at **(120, 120)** — the fixed fallback — on all four runs, as the plan
predicted. What the report adds is *why*, and it is a distinction worth having:

```
"anchor_query_saw_something": false,
"anchor_query_failure": null
```

**The query ran and saw nothing. It did not fail, and it did not prompt.** Tk reports the
pointer in whole-desktop coordinates while describing only the primary display, so a
pointer on a secondary display cannot be bounded and WI-14 correctly treats it as nothing
seen. Expected behaviour, not a defect, and no permission would change it.

## 4. Nothing was echoed, on any run

`stdout` and `stderr` were empty strings on all four exercises, captured across the whole of
each run — including the crash. CTRL-5 asks for a game that echoes nothing, and the one
thing that would legitimately print, the crash report in `main`, is on the path a person
sees rather than inside the loop.

## 5. Every window opened, and its fate

| # | Exercise | Lifetime | Reaped | Exit |
| --- | --- | --- | --- | --- |
| 1 | `first-frame` | 1.188 s | yes | 0 |
| 2 | `played` | 1.488 s | yes | 0 |
| 3 | `crash` | 0.550 s | yes | 0 *(the game exited 1, which is the pass)* |
| 4 | `close` | 0.987 s | yes | 0 |

Each ended on its own Tk scheduler well inside its backstop, each was reaped in a
`finally`, and each acted only on the handle captured at the moment of creation — never
"the front window", never by title. Afterwards `pgrep` found no tool process under any of
the five names this project has used, and System Events counted **0** processes whose name
contains "Python".

**On the modal sheet**, stated the way amendment 6 requires: *"no modal sheet was raised"*
is a negative about the user's environment and is not established by running the thing that
might raise one. The structural argument is WI-3's and unchanged — the window belongs to
this process, so there is no second application left holding one, and killing the process
takes the window with it. What was *observed* is the weaker, sufficient fact: four
processes exited on their own and none of them was there afterwards.

## 6. What this does not tell you

- **Nothing a person saw.** **A1 is open.** Tk read `Terminal Game` back again; that is not
  a person looking at a titlebar, and this is the fifth time this project has declined to
  treat it as one. **WI-21** asks it properly.
- **Nothing about whether the strokes meet.** **A10 / SCRN-3**, untouched. Equal advance
  proves the cells line up, not that the strokes touch.
- **Nothing about a hand on a mouse.** §2's close button evaluates the same Tcl command a
  window manager would, which is the real path — but nobody clicked it.
- **Nothing about a whole game.** Two dots out of 259–271 were eaten. A game played to
  either ending is **WI-19**'s, headless and already landed, and no exercise here reached an
  outcome — every run ended `UNDECIDED`, by `q`, by the close button, or by the crash.
- **Nothing about a modified arrow.** **A11**: `KeyPress` carries no modifier state, so
  control-Up is indistinguishable from Up and moves the player. Ruled a known gap in
  amendment 9 and deliberately not fixed here.
