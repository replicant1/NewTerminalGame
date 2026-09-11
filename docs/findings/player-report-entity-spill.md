# A row of pixels left behind when an entity moves up

**Reported by the player**, 2026-09-11, while playing the finished game. Not
found by `./verify`, and `./verify` could never have found it: no stage of it
can see a screen. This is the first defect in the project found the way the
human-check pack argues defects of this class have to be found.

## The report

> whenever the pacman or the ghost moves up, it leaves behind a row of pixels
> at the bottom of the character's footprint.

## What was ruled out, and how

**The character grid is correct.** Two frames were rendered through the real
`view.render` — the player on a corridor square, then the same player one
square up — and the grids diffed:

```
row  2 before |║▐█▌■ ▪ ║ ▪ ║ ▪ ║ ▪ ■ ▪ ═════ ▪ ■ ▪ ║   |
row  2 after  |║   ■ ▪ ║ ▪ ║ ▪ ║ ▪ ■ ▪ ═════ ▪ ■ ▪ ║   |   <- vacated
       changed:  ^^^
```

Exactly three cells change, to three spaces. Repeated at an interior junction
for **UP, DOWN and RIGHT**: no stale entity glyph anywhere off the new
position in any direction. So neither `view.render` nor the rules are at
fault, and the cause is below the character level.

## The cause

`Screen.paint` writes every cell and calls `refresh`; ncurses then emits only
the cells that **changed**. When an entity moves from row *R* to row *R-1*,
rows *R-1* and *R* change and **row *R+1* does not** — so ncurses sends
nothing for it and the terminal never repaints those pixels. `U+2588` FULL
BLOCK, which both entities are built from, rasterises taller than its cell box
in some fonts and sizes; the pixels it painted below itself live in row
*R+1*'s boxes, and nothing ever cleans them up.

While the entity is standing there the spill is invisible, being contiguous
with the glyph. It only becomes visible when the entity leaves. It is most
obvious moving **up** because moving *down* the entity lands on the orphaned
row and covers it.

## The fix

`Screen.paint` now records what it wrote and calls `redrawln` over every row
that changed **plus one row either side**.

**`redrawln`, not `touchline`.** `touchline` only re-copies the window into
ncurses' virtual screen; `doupdate` then diffs that against its record of the
physical screen and emits nothing when the characters are identical — which is
exactly this case, and would have been a fix that changed nothing. `redrawln`
declares those lines *corrupt on the physical screen*, which is what junk
pixels are.

**`clearok(True)` was rejected.** A forced full repaint every frame would fix
it and would reintroduce precisely the flicker SCRN-7 forbids and human check
H5 exists to catch. The repair is deliberately the narrowest thing that can
work.

The repair can only ever *widen* what is re-sent, never narrow what is drawn
— a bug in it can cost a repaint but cannot lose a cell. There is a test
asserting exactly that.

## Measured

| | |
|---|---|
| Rows redrawn for one upward move | **4 of 30** |
| Added cost of `paint` | **+0.014 ms/frame** |
| Against the 143 ms tick | **0.01%** |
| Suite | 774 -> **783**, `OK (skipped=2)` (now 637; see the note on removed harness tests) |
| `./verify` | 3 of 3, 23.4s |

## Confirmed fixed

**The player confirmed on 2026-09-11, after the fix, that the spill is gone.**
That is the only evidence that could ever have settled it: no agent on this
project has a screen, and the pixels are below the level any test can reach.

It also settles the mechanism by consequence. The repair only ever forces
`redrawln` over the band of rows around a change; if the cause had been
anything other than pixels surviving in rows ncurses was not re-sending, that
repair would have changed nothing visible. It did.

The two observations below were what was wanted before the confirmation came
in. The first is now moot; the second is answered.

**The mechanism was inferred, not seen.** No agent on this project has a
screen. What is *proved* is that the character grid is clean; that the
remaining cause must be below the character level; and that the repair issues
the right calls over the right rows. That the pixels are actually gone can
only be established by a person looking at the screen.

1. **Did the sliver also appear moving left or right?** Never answered, and no
   longer needed. It would have distinguished this mechanism from a narrower
   one, but the fix repairs the band in every direction either way.
2. **Is it gone now?** **Yes** — reported by the player against the fixed
   build.

This belongs with human check **H5** (SCRN-7, "nothing flickers"), which is
the check that owns what the screen actually does between frames.
