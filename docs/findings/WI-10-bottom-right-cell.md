# WI-10 — the bottom-right cell, measured in a real Terminal window

WI-10's brief asks for one thing to be settled by measurement rather than by
reasoning: *"Confirm and, if necessary, fix the bottom-right-cell behaviour
against a real 40 × 30 window."*

**Confirmed. Nothing needed fixing.** The adapter's guard is exactly right, and
the hazard it guards against is exactly as real in a Terminal window as WI-4
found it to be on a pseudo-terminal.

Measured on 2026-09-11 between 03:05 and 03:10 UTC, macOS 26.6.2 (Darwin 25.6.0,
arm64), `/usr/bin/python3` 3.9.6, in **three** windows this work item created
and closed by the id it captured at creation. Terminal's visible windows were
`[367, 2486]` before the first and `[367, 2486]` after the last — the same set
WI-2, WI-4 and WI-8 measured and left unchanged.

Re-run it with:

```
./verify --only corner --verbose
```

---

## 1. The measurement

Two consecutive runs, windows `4318` and `4321`, identical in every field:

```
visible Terminal windows before: [367, 2486]
game window id (from the supervisor): 4318
play said: game window 4318 at (-868, 106) (reference (-898, 76) from front)
the window reported (30, 40) to the OS after 0.00s, and (30, 40) to curses
addstr at the corner: addwstr() returned ERR
insstr at the corner: no error
paint: no error
the screen read back as the picture that went in: True
visible Terminal windows after:  [367, 2486]
```

| Call, in a real 40 × 30 Terminal window | Result |
|---|---|
| `addstr(29, 39, "X")` | raises **`addwstr() returned ERR`** |
| `insstr(29, 39, "X")` | no error |
| `Screen.paint` of a whole 30 × 40 picture | no error |
| the screen read back with `inch`, all 1200 cells | **identical** to the picture, corner included |

So `termgame/screen.py`'s one special case —

```python
if row == last_row and col == last_col:
    window.insstr(row, col, cell.char, attribute)
else:
    window.addstr(row, col, cell.char, attribute)
```

— is correct, is necessary, and is not dead code. Architecture C1 stands, and
WI-4's pty measurement of it was not an artefact of the pty.

## 2. What a real window added that the pty could not

**The size is right before curses looks, and this was not obvious.** `curses`
reads the terminal's size once, at `initscr`, and never again unless it is
told. The supervisor starts the child with `do script` and only *then* resizes
the tab to 40 × 30, so a child that called `initscr` immediately could measure
a window of whatever size Terminal happened to open — and every later
conclusion would be about the wrong window.

The probe therefore polls `os.get_terminal_size()` until it reads 30 × 40
before importing curses at all, and reports how long it waited. **It waited
0.00 s on both runs.** The reason is the same one behind WI-8's title-settling
finding: `do script` opens a window running the user's *login shell*, which
sources their startup files for the better part of a second before the `exec`
line replaces it with our child. The resize lands comfortably inside that gap.

That makes the wait cheap insurance rather than a measured necessity, and it is
worth keeping for exactly that reason: the number is a property of *this
user's* shell profile, and somebody with a fast profile would be racing.

**The probe is a real curses program in a real window, not a stand-in.** It
runs through `termgame.screen.Screen` with `build_attributes()` — real colour
pairs against Terminal's real 256-colour support — which is a thing no pty test
exercises in the same way.

## 3. Two positions, reproduced

Not the object of the exercise, but both runs also landed the window at
`(-868, 106)` from a reference of `(-898, 76)`: exactly **+30 across and +30
down**, which is WIN-4 and is WI-8's number reproduced exactly.
Neither run printed `could not read the screen layout`, so the intermittent
display-layout fallback WI-8 recorded did not occur on either.

**This is still not human check H1** and must not be reported as one. The
reference window here was whatever Terminal window happened to be frontmost
while an agent with no controlling tty ran the probe. Whether the game lands
below and right of *the window a person typed in* is H1, and only a person can
answer it — see `docs/findings/WI-10-human-checks.md`.

## 4. What was deliberately not done

- **The real game was not launched.** It blocks until somebody presses `q`, and
  plan §2.6 rule 4 forbids launching, in a window you opened, anything you
  cannot end. The probe ends by itself in about a second and a half.
- **No keystroke was scripted into another application.** WI-4 declined this
  because it needs Accessibility, which this design does not require, and WI-8
  held that line. WI-10 holds it too.
- **No busy tab was closed**, no window was forced, and nothing was closed that
  this work item had not itself created and captured the id of.
- **No Terminal preference, profile or global setting was touched.**
