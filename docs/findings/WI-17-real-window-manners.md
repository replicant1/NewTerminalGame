# WI-17 — What a real window actually does when the game misbehaves

**Measured by:** DEV-A, WI-17, on this machine, with `tools/window_manners.py`.
**Interpreter:** `/usr/bin/python3` — Python 3.9.6. **Toolkit:** Tk **8.5.9**.
**Windows opened:** five, each under 1.5 seconds, **each confirmed gone.**
**Screen gate:** held exclusively, granted and released through the conductor
(section 4, rule 4).

Everything below was run, not reasoned about. Re-run any of it:

```
/usr/bin/python3 tools/window_manners.py --exercise window
/usr/bin/python3 tools/window_manners.py --exercise keys
/usr/bin/python3 tools/window_manners.py --exercise fail-collaborator
/usr/bin/python3 tools/window_manners.py --exercise fail-session
/usr/bin/python3 tools/window_manners.py --exercise close
```

None of them is part of the suite — `unittest discover -p "test_*.py"` does not collect
the script — and every one of them quits on Tk's own scheduler, so none depends on anybody
pressing anything.

---

## 1. The finding that matters: a crashed game exits looking clean

**This is the whole reason WI-17 was worth two days, and it is for WI-18.**

`--exercise fail-session` ran a real `Session` over a real 19 × 29 maze in a real window,
painting through the real surface, and made its composer raise on the fourth picture —
inside the event loop, which is the only place it counts.

| | |
| --- | --- |
| Pictures composed before the failure | 3 |
| Ticks delivered | 3 |
| The window was reaped | **yes** |
| The session reached Ended | **yes** |
| Printed to stderr | **nothing** |
| The exception came back out of `owner.run()` | **no** |
| `report["error"]` | **null** |
| Process lifetime | 0.534 s, against a 4 s backstop |
| Where the crash was recorded | **`session.failure`, and nowhere else** |

Read the last two rows together. The process exits **0**. The window closes tidily. Nothing
is printed. A person watching sees a game that ended, and a script checking the exit code
sees success. The only difference between that and a healthy game is one field on an object
that has already served its purpose.

This is not a defect in WI-15. It is WI-15 doing exactly what amendment 1 told it to: Tk
swallows an exception raised inside an `after()` callback, so a session that *raised* would
sit there with a broken game on an unquittable screen. Routing the failure to the shutdown
path is right. **Recording it rather than absorbing it is what makes it recoverable — and
only if somebody reads the record.**

**So the instruction to WI-18 is now measured rather than reasoned.** `tools/window_manners.py`
shows the shape the check takes, in four lines:

```python
def exit_code_for(report):
    if report.get("error") is not None:        # came out of the loop
        return 1
    if report.get("measured", {}).get("session_failure"):   # did not
        return 1
    ...
```

The second branch is the one nothing would have found by reasoning about the code, because
the code is correct.

## 2. The other failure shape, and a bonus for CTRL-5

There are **two** ways this application can fail inside a callback, and they behave
differently. `--exercise fail-collaborator` is the other: the window owner's collaborator
raises on its third tick.

| | |
| --- | --- |
| Ticks before the failure | 3 |
| `WindowOwner` reaped, then re-raised | yes |
| Tk caught the re-raise and called `report_callback_exception` | yes |
| The exception came back out of `owner.run()` | **yes** |
| The window was reaped | yes |
| Printed to stderr | **nothing** |
| Process lifetime | 0.496 s |

So the chain WI-3 built — hook `report_callback_exception`, keep the first exception, stop
the loop, re-raise out of `run_event_loop` — **works on real Tk**, and this is the first
time it has been exercised through a `WindowOwner` collaborator rather than a bare
scheduled callback.

**The empty stderr is a finding in its own right.** Tk's default
`report_callback_exception` prints a traceback. The adapter replaces it, so **CTRL-5's
"nothing is echoed anywhere" survives the failure path as well as the ordinary one.** A
game that fell over would not spray a traceback across a terminal the player never asked to
see.

A sequencing note for whoever touches this next, because it is not obvious and it is load
bearing. When the collaborator raises, `WindowOwner.end_session()` runs *first* and destroys
the window, so by the time `note_callback_exception` calls `stop_event_loop()` the adapter's
`_root` is already `None` and that call does nothing at all. **The loop returns anyway,
because Tk's `mainloop()` returns when its last window is destroyed.** The arrangement is
correct, but it works for a different reason than it reads as though it does.

## 3. A real key press, and the player actually moves

WI-4 pressed keys into a real window and wrote down that they arrived. That is a weaker
claim than this item owes: *"acted on"*. `--exercise keys` runs each key through WI-9's
`translate` into a real `Session` and watches the player's square.

Six keys, driven into the window this process created, through the handle captured at
creation — nobody's keyboard was touched.

| Key | Intent | The real player, before → after |
| --- | --- | --- |
| `Up` | Move north | (9,13) → **(9,12)** |
| `Left` | Move west | (9,12) → (9,12) — **a wall; nothing at all happened** |
| `Down` | Move south | (9,12) → **(9,13)** |
| `Right` | Move east | (9,13) → **(10,13)** |
| `z` | *nothing* | unchanged |
| `q` | Quit | session **Ended** at 1.483 s, against a 4 s backstop |

Nine ticks arrived at the ghost's cadence, thirteen frames were painted, and stdout and
stderr were empty throughout.

**Two things worth naming.** The `Left` row is **CTRL-3 observed on a screen** — "a press
towards a wall does nothing at all" had only ever been a unit test. And the four squares
are **exactly** what the pure Domain gives for seed 20260916 when the same four moves are
replayed headless, which means the whole WI-9 → WI-15 → WI-11 chain agrees with itself
through a real window and a real event loop. That is the closest thing to an end-to-end
proof available before WI-18.

## 4. The manners themselves

`--exercise window`, over the specimen picture painted by the real surface.

| Asked for | Measured back | |
| --- | --- | --- |
| title `Terminal Game` | `Terminal Game` | exact |
| 400 × 570 px, from Menlo 16pt | 400 × 570 | exact |
| not resizable | `0 0` | exact |

**`root.wm_resizable()` returned the `str` `"0 0"`** — type recorded as `str` in the report,
not a pair. WI-3 measured this and it cost that item a probe run; it is confirmed here on
the same machine so that nobody has to find it a third time. Read it with
`root.tk.splitlist(root.wm_resizable())`.

**A resize request changes nothing.** A `<Configure>` event of the shape a window manager
delivers when somebody drags a corner, 220 px larger on both axes:

| | Before | After |
| --- | --- | --- |
| Window | 400 × 570 | **400 × 570** |
| Canvas items | 696 | **696** |
| Every cell's coordinates | — | **identical** |

The grid is 30 rows of 40 columns and cannot be anything else: cell positions come from the
font metrics and the frame's shape, and the window is not in that calculation at all.

**No caret can appear.** SCRN-7's half that lives in the window rather than on the surface:

| | |
| --- | --- |
| Widget classes in the whole window | `Tk`, `Canvas` — **and nothing else** |
| `canvas.cget("insertwidth")` | `0` |
| `canvas.cget("takefocus")` | `0` |
| `canvas.focus()` — the focused text item | **none** |

A Tk canvas shows an insertion cursor only when one of its text items holds the canvas
focus. No item ever does, the caret is zero pixels wide regardless, and there is no
text-entry widget in the window for one to live in. `tests/test_window_manners.py` guards
the last of those three for the future; the surface's own half is WI-2's and has been since
M0.

**Nothing was echoed**, on any of the five runs: `stdout` and `stderr` were empty strings,
captured across the whole of each run including the failures.

## 5. The close button, and one thing WI-18 must wire

`--exercise close` takes the route a window manager takes. It does not call a Python
function: it asks Tk for the command registered against `WM_DELETE_WINDOW` and evaluates
it, which is what Tk itself does when the message arrives. The one thing it cannot reproduce
is a human hand on a mouse.

| | |
| --- | --- |
| Process ended | 0.981 s, against a 4 s backstop |
| Window reaped | yes |
| Orphan process | none |
| **Session phase at the end** | **`playing`** |

**That last row is a wiring note for WI-18, not a defect in WI-17.** `WindowOwner.open()`
binds the close request to its **own** `end_session`, so the close button takes the window
and the process away and **never reaches the session**. Everything WI-17 promises still
holds. But a close-button exit currently skips the session's own shutdown — and therefore
skips the `session.failure` check in section 1, which is the one thing WI-18 must not miss.

The fix needs no change to `WindowOwner`, which matters because that is WI-3's file and
another lane's: `bind_close_request` is last-writer-wins, so WI-18 rebinds it to the
session's `quit` after `open()` and the window owner's `end_session` still runs, as the
session's `shut_down`.

## 6. Every window opened, and its fate

| # | Exercise | Lifetime | Reaped | Exit |
| --- | --- | --- | --- | --- |
| 1 | `window` | 1.386 s | yes | 0 |
| 2 | `keys` | 1.483 s | yes | 0 |
| 3 | `fail-collaborator` | 0.496 s | yes | 0 *(failure expected and found)* |
| 4 | `fail-session` | 0.534 s | yes | 0 *(failure expected and found)* |
| 5 | `close` | 0.981 s | yes | 0 |

Each quit on its own Tk scheduler, each was reaped in a `finally`, and each acted only on
the handle captured at the moment of creation. Afterwards
`pgrep -fl "window_manners|walking_skeleton|probe_tk_window"` was empty and System Events
counted **0** processes whose name contains "Python". **None was left behind.**

**On the modal sheet, stated the honest way.** *"No modal sheet was raised"* is a negative
about the user's environment, and running the thing that might raise one is not how such a
claim is established — the two honest routes are to make the route structurally absent and
show the absence, or to ask the person. This is the first route, and it is WI-3's
measurement rather than a new one: **the window belongs to this process.** The sheet Tk and
Terminal raise is raised by an application that still holds a window whose *other* process
is alive; under candidate 2 there is no second application and no second process, so
killing the process takes the window with it and there is nothing left to ask about. What
was observed here is the weaker, sufficient fact: five processes exited on their own and
`pgrep` found none of them afterwards.

## 7. What this does not tell you

- **Nothing a person saw.** **Assumption A1 remains open.** Tk read `Terminal Game` back on
  all five windows, which is stronger evidence than candidate 1 ever had, and it is still
  not a person looking at a titlebar. Four developers have now declined to convert one into
  the other. WI-21 asks it properly.
- **Nothing about whether the double lines join up.** SCRN-3, now **assumption A10**. Equal
  advance widths prove the cells line up; they do not prove the strokes touch. Not
  measurable, not touched here, and not rounded up.
- **Nothing about where the window should go.** WI-14's, under A2.
- **Nothing about a human hand on a close button.** Section 5 invokes the same Tcl command
  the window manager would, which is the real path, but a person has not pressed it.
- **Nothing about the assembled game.** The script builds a session so that a key can be
  seen to move a player; **WI-18 owns the entry point**, and its `KeyDispatcher` is three
  throwaway lines, not a proposal.
