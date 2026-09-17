# WI-14b — call the placement WI-15 decided

**Branch:** `r7/wi-14b-wire-placement`, cut from the tip of `main` at `b302b2d`.

**Suite:** `.venv/bin/python -m pytest -q` — **923 passed, 0 failed, 0 skipped, 7 deselected**.

---

## The defect, measured rather than inferred

```
the assembled game put its window at : Point(x=5, y=38)     <- Tk's own default
WI-15 says it should go at           : Point(x=556, y=206)  <- centred on the display
window 400x570, display 1512x982
```

`placement.py` and `GameWindow.move_to` were both **complete and tested**, and **nothing
in the product called either** — the only callers anywhere were `tests/test_placement.py`
and `tests/test_window_placement.py`. `run_game` called `show()` with nothing in front of
it.

The unit tests either side of the gap were green throughout. Only driving the assembly
found it, which is what WI-17 is for.

## Where this came from, since it is not where it looked

I reported this as my own omission from WI-14. **The technical lead's finding is that the
plan never asked for it**, and that is the more useful answer:

> WI-14's dependencies are WI-2, WI-7, WI-11, WI-12, WI-13. **WI-15 is not among them.** And
> WI-15's only outgoing edge is to WI-17 — **a verification item, which consumes nothing.**
> So WI-15 produced a capability no item was ever told to use.

It has turned that into a check on its own artefact: **every item producing a capability
needs at least one non-verification consumer in the dependency graph, or it is dead on
arrival.** Recorded here because the next person to read this diff will otherwise conclude
somebody forgot a line.

## What the change is

`Game.place()` asks `placement_for` where the window goes and hands the answer to
`move_to`. `run_game` calls it immediately before `show()`, which is where WI-6's own
docstring says placement belongs.

**It decides nothing.** The fallback inside `placement_for` is S-2's choice, implemented and
tested by WI-15. Nothing in `placement.py` or `window.py` is touched — those are lane B's
and lane C's, and the instruction was to call what is there and nothing more. The display
rect comes from the surface widget's public `winfo_screenwidth`/`winfo_screenheight`.

A method rather than an inline call, so that a caller which shows its own window — WI-16,
or a WI-17 script — can place it too.

## **This does not make WIN-4 met**

The reader is `NoAnchor`, which follows nothing, so the window is **centred on the main
display** rather than appearing beside whatever the player was last looking at. That is the
honest fallback and it is what the user is being asked about in human item 4.

The trace row read **not met**. It should read **not met, and not wired** — and after this,
**not met, wired to the fallback**. "Not met" alone leaves a reader believing the fallback
was running, which it was not.

## The tests, and the control that matters

- the placement is **what `placement_for` computed**, asked for rather than recomputed;
- **the control: the window actually moved.** Tk gives a fresh toplevel a position of its
  own — WI-15's own docstring says so — so `position()` answering something is not evidence
  that anything placed it. The evidence is that it *changed*, and changed to the computed
  point. Without this the first test passes on a game that never moved;
- placing does not disturb the 400 × 570 size, because a geometry string carrying `WxH`
  would silently overrule what WI-6 computed from the cell metrics.

## Window hygiene

No window is mapped by any of these tests — `move_to` is `wm_geometry` and works on a
withdrawn window. No second `tkinter.Tk()`, no `update()`, no `ctypes`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
