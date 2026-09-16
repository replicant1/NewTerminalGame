# WI-3 — What Tk actually does with the game's own window

**Measured by:** DEV-C, WI-3, on this machine, with `tools/probe_tk_window.py`.
**Interpreter:** `/usr/bin/python3` — Python 3.9.6. **Toolkit:** Tk **8.5.9**.
**Windows opened:** three, each for about a second, each confirmed gone.

Everything below was run, not reasoned about. The probe is in the repository and
can be run again:

```
/usr/bin/python3 tools/probe_tk_window.py          # the normal path
/usr/bin/python3 tools/probe_tk_window.py --fail   # the failure path
```

It is **not** part of the suite — `unittest discover -p "test_*.py"` does not
collect it — and it quits itself on Tk's own scheduler, so it does not depend on
anybody pressing anything.

---

## 1. The window is exactly what it was asked to be

| Asked for | Measured back | |
| --- | --- | --- |
| title `Terminal Game` | `Terminal Game` | exact |
| 512 × 600 px window | window 512 × 600, canvas 512 × 600 | exact |
| position (140, 140) | (140, 140) | exact |
| background `black` | `black` | exact |
| not resizable | not resizable, on **both** axes | exact |

**The title is the finding that matters.** Under candidate 1 the architect
measured (V4) that the terminal composed extra parts around it and reported
`rodneybailey — Terminal Game — sleep 2`. Under candidate 2 the process owns the
window and Tk reports the title back **unchanged**. That is the architecture's
claim about WIN-3, measured.

**It is not, however, an answer to assumption A1.** Reading a string back from
the toolkit that set it is not the same as a person seeing the titlebar, and
macOS may add its own furniture — a proxy icon, a modified dot — that the
toolkit never hears about. **A1 remains open and still needs a human**, as the
plan says, at WI-4 and again at WI-21.

The geometry being exact matters too, and for a reason easy to overlook: it
means WIN-2's "40 characters wide and 30 rows deep" reduces to WI-2 getting the
cell metrics right. There is no second source of error between the number WI-2
computes and the window the player sees, and no window-manager rounding to
absorb. The canvas is created with `highlightthickness=0` and `borderwidth=0`
for exactly this reason: the default two-pixel highlight ring would have eaten
into the grid silently.

## 2. The cadence holds on real Tk

| | |
| --- | --- |
| Nominal interval (GHOST-1, 1000/7 rounded) | **143 ms** |
| Observed interval over 8 ticks | **144.2 ms** |
| Observed rate | 6.93 ticks a second |

GHOST-1 asks for "about seven times a second". The repeating tick is built from
Tk's one-shot `after`, re-armed after each tick, and the 1.2 ms of drift per tick
is the cost of that. It is not worth correcting: a game that is 0.8 % slow than
seven ticks a second is still "about seven times a second", and compensating
would add a monotonic-clock correction to the one piece of the Shell that most
wants to stay obvious.

## 3. Tk swallows exceptions raised inside callbacks — and what we did about it

**This was found by accident**, when the probe's own measurement code had a bug
(see section 4). It is the most consequential thing in this document.

**Measured:** an exception raised inside an `after` callback does **not** escape
`mainloop()`. Tk catches it, hands it to `report_callback_exception`, which
prints a traceback to stderr, and **the event loop carries on**. The probe
completed normally and exited **0**, with a traceback printed and one of its
measurements silently missing.

Left alone, that would have meant:

- a session that fell over would have looked exactly like a session that ended;
- the seam's contract — "a collaborator that raises loses its window **and** the
  failure is visible" — would have been true of the recording double in the
  tests and false of the real thing.

The window would still have been reaped, because `WindowOwner` reaps *before* it
re-raises. But the process would have exited 0 with a traceback nobody reads.

**What we did:** `TkToolkit.create_window` now points Tk's
`report_callback_exception` at `TkToolkit.note_callback_exception`, which
remembers the **first** exception, stops the event loop, and lets
`run_event_loop` re-raise it once `mainloop()` has returned.

**Measured after the change**, with `--fail`, which schedules a callback that
raises on purpose:

| | |
| --- | --- |
| The exception came back out of `owner.run()` | yes |
| The window was reaped | yes |
| The session ended at the failure (900 ms), not at the 1200 ms backstop | yes — lifetime 1.055 s, 6 ticks |
| The process exited by itself | yes |

> `--fail` raises a `DeliberateProbeFailure` from a probe callback. That is an
> error path exercised with an input that legitimately produces an error. It is
> **not** a mutation of working code to watch a test go red, which is
> prohibited, and no production code is altered to produce it.

**Anyone else building on this toolkit should know it.** If WI-16, WI-17, WI-18
or WI-21 ever construct a Tk root by some route that does not go through
`TkToolkit`, they inherit the swallowing behaviour and will not be told.

## 4. Two smaller measurements, both of which cost time to find

**`root.resizable()` with no arguments returns the Tcl string `"0 0"`, not a
pair.** Unpacking it raises `ValueError: too many values to unpack (expected
2)`, which is what produced the accident in section 3. Read it with
`root.tk.splitlist(root.wm_resizable())` and convert each part with `int`.

**A window created by this process dies with this process.** Killing the probe
outright takes the window with it. There is no second application left holding a
window, and therefore **no modal "terminate running processes?" sheet** for
anybody to dismiss — the hazard the architect's caution C7 is about, and the one
that blocked a previous run. This is a real safety advantage of candidate 2 over
the supervisor design, and it is why the probe can afford an external SIGKILL
backstop at all.

## 5. What this does not tell you

- **Nothing about glyphs, fonts or cell metrics.** That is WI-2's, and
  `docs/findings/WI-2-cell-metrics.md` is where it goes. The sizes above are a
  stand-in chosen to be obviously not a character count.
- **Nothing about where the window *should* go.** The probe placed it at a fixed
  offset. WIN-4's anchor is WI-14's, under assumption A2, and still needs the
  permission question settling.
- **Nothing a person saw.** No human has looked at any of these three windows.
  A1 is open.
