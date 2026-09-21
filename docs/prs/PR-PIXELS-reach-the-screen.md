# PR-PIXELS — a test that reads the screen

Risk: HIGH — it photographs the user's display. Aim the capture at the wrong rectangle and it
records whatever else is there; that happened twice during this investigation and caught
windows belonging to the user. The geometry is the dangerous part, not the assertions.

Two tests and a helper, all `needs_window`, plus a finding. No application code.

## Why

The user looked at the running game and said there was no maze in it. **996 tests were green.**

They were green because every one of them reads what Tk was *told*, never what reached the
screen. Tk records `text='╔'`, `fill='#2121de'` on a canvas item it never draws, and
`itemcget` returns the record. A window showing nothing satisfies the whole suite. The test
that runs the real entry point says as much in its own comment:

> *What this can honestly observe, and no more: `run_game` maps a window, returns rather than
> hanging, and leaves nothing open.*

The plan handed the visual checks to a human, and gave a reason:

> **because no agent on this machine can capture the pixels to judge it**

**That premise is false**, and it had never been tested. `screencapture` is on every Mac,
Screen Recording is already granted here, and a capture returns real window content. It took
four accidental captures to notice.

## What lands

- **`tests/pixels.py`** — capture a widget by *Tk's own* geometry, parse the BMP, histogram it.
  Standard library and `screencapture`; `requirements.txt` is untouched.
- **`tests/test_pixels_reach_the_screen.py`** — two tests, and **which one fails tells you
  where the fault is**:
  - *the control*, twenty lines of Tk owing nothing to this project — a canvas, one filled
    rectangle. If it fails the toolkit cannot draw and no application code is implicated.
  - *the check*, the real game, asserting its wall ink is in the frame.

  Section 7 of the plan asks for exactly this pairing — *a guard needs a control* — and a
  capture test is the purest case: photograph the wrong rectangle, or nothing at all, and it
  reports success forever.
- **`docs/findings/WI-17-pixels-reach-the-screen.md`** — the false premise, the measurement,
  and the recipe.

## What they say right now

Both fail, and **the control fails too**, which is the finding:

```
FAILED  test_a_plain_canvas_reaches_the_screen
FAILED  test_the_game_reaches_the_screen
2 failed, 10 passed, 986 deselected in 7.34s
```

A bare Tk canvas with a solid `#2121de` rectangle on a black ground photographs as **17,195 of
17,200 sampled pixels pure white**. Tk 8.5.9 maps windows here and paints nothing in them, on
python 3.9.6 / aqua / three Retina displays. **So the blank game is not an application
defect** — and `requirements.txt` pins this interpreter as *"the only one with a working
`_tkinter`"*, where "working" only ever meant importable.

**These land failing, deliberately.** The default suite is unchanged at 986 green; both are
`needs_window`, excluded by ground rule 1.6, and run only when asked. A guard that is green on
a broken screen would be worse than none.

## Scrutiny

- **`tests/pixels.py:capture`** — the geometry. This is the risk in the whole change. It must
  photograph the widget and nothing else; `winfo_rootx/rooty` are the only trustworthy source,
  and AppleScript's `position` is measured-wrong on a secondary display.
- **`tests/test_pixels_reach_the_screen.py:_drive`** — the watchdog. Plan §1.5: a test that
  maps a window needs an exit that does not depend on the thing under test working.
- **The control's independence** — if it shares anything with the game's rendering path it
  cannot discriminate, and both tests become one test.
- **`tk_root` and `quit()`** — the fixture is session-scoped and shared. A `destroy()` would
  take the interpreter out from under every later test; the first draft created a second
  `tkinter.Tk()` and hung the run.

## Suite

`.venv/bin/python -m pytest -q` → **986 passed, 12 deselected**, unchanged.
`-m needs_window` → **10 passed, 2 failed**, the two being these.
