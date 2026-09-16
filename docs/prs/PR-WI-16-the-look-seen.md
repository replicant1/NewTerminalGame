# WI-16 — The look, seen

**Real-medium exercise (amendment 2, rule 1): NOT YET RUN. I am waiting on
the conductor's screen gate and have opened no window.** Everything in this
branch that does not need one is finished and green; the human check and its
findings document follow once the screen is mine.

**Developer:** DEV-B · **Branch:** `r6/wi-16-the-look-seen` · **Base:** `main`
**Iteration:** M3 · **Depends on:** WI-2, WI-4, WI-12 — all landed

## What is in it

| File | |
| --- | --- |
| `tools/the_look.py` | Three views, bounded and self-reaping. Not collected by `unittest` |
| `tests/test_the_look.py` | 31 tests, none of which opens a window |

## The one question a measurement cannot close

**SCRN-3 — do the blue double lines actually join up?** The state of the
evidence, and I produced half of it, so I want to be plain about what it does
*not* say:

- In WI-2 I measured that all 113 glyphs the picture uses share one advance
  in Menlo at 14/16/18/20pt, with a control showing glyphs Menlo *lacks* fall
  back to visibly different advances. **That settles the spacing.** The
  glyphs are in the right places.
- It says nothing about whether the *strokes meet*. That is about the shapes,
  not the metrics, and DEV-C recorded the same conclusion independently in
  WI-8's glyph census.

**I have not closed it by inference from my own measurement, and this branch
does not.** What it does is make the looking cheap.

## Three views, so one sitting answers all three questions

```
/usr/bin/python3 tools/the_look.py                  # all three, 8s each
/usr/bin/python3 tools/the_look.py --view joinery
/usr/bin/python3 tools/the_look.py --sizes 14,16,18,20 --view game
```

**`joinery` — every wall junction at once.** The thing that makes SCRN-3
answerable in seconds rather than by hunting round a maze for a crossing:

```
╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╗
║   ║   ║   ║   ║   ║   ║   ║   ║   ║
╠═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╣
```

Corners, tees, crossings and straights, all joining, filling the window.
**Derived from WI-8's `wall_layer` on a lattice maze, not hand-drawn** — this
module declares no wall glyph and there is a test that it declares none. The
lattice yields all 11 junctions *including the crossing the specimen picture
happens not to contain*, which is the one glyph nothing else on this project
has ever put on a screen.

**`colours` — the five colours beside the thing each belongs to**, so "can
you tell the player from the ghost" is answerable at a glance:

```
 2|  wall     ═════                        |
 5|  dot      ▪▪▪▪▪                        |
 8|  you      ▐█▌                          |
11|  ghost    ▗█▖                          |
15|  the two actors differ in shape        |
29|score 0    arrows, q quits              |
```

Each label is in its own colour as well as the sample, because a hue that
reads well as a solid block can still be unreadable as text. Row 29 is the
**real** status line from WI-13, not a sample of cyan.

**`game` — the real thing.** A real generated maze, the real composer, the
real status line, at a fixed seed so that two people discussing "the picture"
are discussing the same picture.

**`--sizes 14,16,18,20` answers A4 properly.** One window per size, in turn,
each reaped before the next opens — so the person compares rather than
guesses, and answers "is the type comfortable" once instead of three times.

## Window hygiene

The tool follows DEV-C's proven pattern from `tools/walking_skeleton.py`
rather than inventing a second one. Per window:

- the deadline is scheduled on the toolkit's scheduler **before** the event
  loop is entered, so it never depends on anybody pressing anything;
- the reap is in a `finally`, so a failure still takes the window away;
- **the next view does not open until the last is confirmed gone** — and if a
  window is ever *not* reaped the run stops rather than opening another;
- only the handle captured at creation is ever acted on;
- `--seconds 0` and a negative deadline are **refused at parse time**, so a
  window with no deadline cannot be asked for, let alone opened.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 564 tests — 564 passed, 0 failed, 0 skipped
```

31 are new here. **None opens a window**, and two of them assert that:
importing the tool and building all three views leave `tkinter._default_root`
as `None`.

## What the tests own

Per the plan, this item's automated tests own **the colour vocabulary
reaching the surface unchanged** — the picture is already pinned by WI-12 and
the glyphs by WI-8, and re-asserting either here would turn one defect into
two red files. So:

- each view painted through the recording surface shows exactly the frame it
  was given;
- the glyph each requirement names arrives under the colour that requirement
  names — the dot gold, both actor motifs in their own colours, the wall
  glyph blue, row 29 cyan;
- the five visible colours are all **different values** on the surface, since
  there is no point showing a person two hues that are the same;
- nothing but characters is ever drawn, for any view.

And that the tool **cannot run unbounded**: every configuration parses to a
positive deadline and at least one window; zero, negative and empty are
refused; and the three questions are actually put to the person in words,
because a tool that opens a window without saying what to look for is worth
nothing.

## First run: the suite went to 16 seconds

Every view rebuilt a generated maze, and satisfying MAZE-4, MAZE-5 and MAZE-6
is the expensive thing in the tree. The three frame builders are now cached —
a frame is immutable, so sharing one is safe — and the suite is back to 4.3s.

## Still to come on this branch

The human check itself, and `docs/findings/WI-16-the-look.md`: the font size
chosen, whether the double-line glyphs join up cleanly at it, and whether the
five colours are distinguishable. **Blocked on the screen gate**, not on
anything technical.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
