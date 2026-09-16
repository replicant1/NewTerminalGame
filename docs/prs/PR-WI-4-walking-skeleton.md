# WI-4 — The walking skeleton

**Developer:** DEV-C · **Branch:** `r6/wi-4-walking-skeleton` · **Base:** `main`
**Milestone:** M0, the last item in it · **Effort budgeted:** 1 developer-day

## What this is

The end-to-end proof M0 exists to reach. `tools/walking_skeleton.py` opens the
application's own window at the size WI-2's font metrics give, paints **the specimen
picture from the requirements** through the real surface, logs the ticks arriving and
the keys pressed, and closes the window and exits when `q` is pressed or after a
bounded number of seconds, whichever comes first.

Candidate 2 was chosen over the architect's own recommendation. **This is the first
moment anybody can say whether that choice works. It does** — see
`docs/findings/WI-4-first-window.md`, which is the substance of this item.

```
/usr/bin/python3 tools/walking_skeleton.py                  # 10 seconds, or press q
/usr/bin/python3 tools/walking_skeleton.py --seconds 3 --json
```

## It found a real defect, and it is the kind no test would have caught

WI-3's adapter called `canvas.focus_set()` and nothing more, on the reasoning that
forcing focus is rude. WI-3's tests passed and WI-3's probe passed — because **neither
ever pressed a key.**

Measured here against a real window: with `canvas.focus_set()` alone, **no key event is
delivered at all**, even though `focus_get()` returns the canvas, the bindtags are
right and the binding is on the right tag. Tk-internal focus is not enough; the
toplevel needs the *operating system's* keyboard focus.

A game window that opened without OS focus would have taken no arrow keys and no `q` —
and CTRL-4 and END-6 make `q` the only way out of a finished game. The player would
have been left with a window they could close only from the window manager, which is
the very thing WIN-5 is for.

**Fix:** `root.lift()` and `root.focus_force()` as the window opens, in
`TkToolkit.create_window`. Fifteen lines, comment included. **This is a change to
WI-3's adapter made in WI-4's branch, and it needs a ruling** — see Deviations.

Measured after the fix, driving `Up, Left, Down, Right, z, q` into the real window: all
six arrived in order, and `q` ended the session at **1.437 s** against an 8 s deadline.

## What else was measured

| | |
| --- | --- |
| Window | 400 × 570 at (160, 160) — exactly what Menlo 16pt at 10 × 19 a cell gives |
| Title read back | `Terminal Game`, exact |
| Canvas | **696 items, every one of kind `text`** — SCRN-2 holds in fact, not only by convention |
| Rows painted | 30 |
| Tick | 144.0–144.3 ms observed against a nominal 143, over three runs |
| Windows opened | five, each self-quitting, **each confirmed gone** |

## What is in it

| File | What it is |
| --- | --- |
| `tools/walking_skeleton.py` | The skeleton. `WalkingSkeleton` is the assembly and takes every collaborator as an argument; `main()` is the only part that touches the real toolkit. |
| `tools/__init__.py` | Makes `tools` importable so the assembly can be tested. Nothing in `tools/` is named `test_*`. |
| `tests/test_walking_skeleton.py` | The join, and only the join. |
| `docs/findings/WI-4-first-window.md` | What the window actually did, what the titlebar read, and the three questions for a human. |

Also carried on this branch, rather than in a fourth documents-only PR: the closing
update to `docs/completions/COMPLETION-M0-DEV-C.md` and the last progress lines of WI-3
and WI-3a. The completion record is one per lane per iteration and WI-4 is the lane's
last M0 item.

## Tests

`/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"` — **247 passed, 0
failed, 0 skipped.**

**These tests own the join and nothing else.** That the surface is built on the
drawing target the *window* handed back; that the frame reaches the surface; that ticks
and keys reach the journal; that `q` ends the session and another key does not; that a
deadline is scheduled *before* the event loop is entered, so the run is bounded whatever
anybody does or does not press. Nothing about titles, sizes, colours, glyphs or cadence
— every one of those already has an owner in WI-1, WI-2 or WI-3.

One test asserts the specimen frame reproduces `tests/specimen.py` character for
character, so the skeleton cannot quietly paint something it made up.

**No test in this branch constructs a toolkit window**, and one new test pins that
directly: after the whole suite has imported everything, `tkinter._default_root` is
`None` — no Tk interpreter is ever created. See Contradictions for why that wording
matters.

## Contradictions found, with the measurement

**"The suite loads neither `tkinter` nor `_tkinter`" is not true, and has not been since
WI-3 landed.** It was relayed to me as an established property to preserve. Measured, by
importing each test module one at a time: the suite *does* load both, and exactly one
module brings them in — `tests/test_tk_toolkit.py`, which imports the Tk adapter because
the adapter cannot be checked against the seam otherwise.

The property that actually keeps a window off the screen is stronger and does hold:
**no Tk interpreter is ever created.** `import tkinter` reaches nothing; `tkinter.Tk()`
is what reaches the window server, and nothing in the suite calls it —
`tkinter._default_root` is `None` after every test module has been imported. There is
now a test asserting that, in the one module where it could stop being true.

Worth correcting rather than leaving, because WI-10 is about to build a guard and the
two statements ask for different guards: one would forbid a necessary import, the other
forbids the thing that actually opens a window.

## Two fixes to shared test machinery

**The recording double now models virtual time.** It fired timers in the order they
were *scheduled*, which is not what a scheduler does: the skeleton schedules its
ten-second deadline before the event loop starts the 143 ms tick, so the deadline fired
first and no tick was ever delivered. `schedule_once` now records a due time and
`fire_due_timer` takes the soonest and moves the clock to it. Every one of WI-3's timer
tests passes unchanged.

## Deviations needing a ruling

1. **`root.lift()` and `root.focus_force()` added to WI-3's Tk adapter.** Justified by
   the measurement above, but it is a behaviour change to a landed item, made from a
   later item's branch, and the plan puts "the window's manners" in WI-17. Flagging it
   rather than slipping it in.
2. **`tools/walking_skeleton.py` reads the specimen from `tests/specimen.py`.** A
   `tools/` module importing from `tests/` is backwards. The alternative was a second
   transcription of a 30-row picture, which is two things to drift apart. Raised rather
   than decided; if the specimen should live somewhere both can use, that is DEV-B's
   file to move.
3. **`--press` drives synthetic key events into the window.** It exists so the key path
   could be measured against real Tk without touching the keyboard of whoever is sitting
   at the screen. It presses only into the window this process created.

## What still needs a human

Three questions, with the exact steps in section 5 of the finding:

1. **Does the titlebar read exactly `Terminal Game`?** (A1.) Tk reports the title back
   unchanged, which is stronger evidence than the architect had — but that is a string
   read back from the toolkit that set it, not a person seeing a titlebar, and macOS may
   add furniture the toolkit never hears about. **Nobody has looked at any of the five
   windows.**
2. **Is the type large enough to read comfortably?** (A4.) 400 × 570 from Menlo 16pt.
3. **Do the blue double lines actually join up?** Equal advance widths are measured;
   whether the strokes meet is something only an eye can settle.
