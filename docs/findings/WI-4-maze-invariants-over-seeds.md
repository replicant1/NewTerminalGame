# WI-4 — the maze invariants, measured over 20 000 seeds

**Item:** WI-4, the maze model and its generator. **Lane:** DEV-B, iteration M0.
**Measured on:** `wi-4-maze-generator` at `6db3c50`, Python 3.9.6, standard library only.

Architecture caution C8 is backed by a measurement over **300** mazes. This is the same measurement
run over **20 000**, plus the numbers describing what the generator actually produces, so that
anyone touching the carve or the braid later has something to compare against rather than a
recollection.

## What was run

```
MAZE_SWEEP_SEEDS=20000 python3 -m unittest tests.test_maze_generator
```

**Result: 30 tests, 0 failed, 0 skipped, 58.8 s.** Seeds 0 to 19 999, one maze each, every maze
checked for all of the following.

| Property | Requirement | Failures in 20 000 mazes |
| --- | --- | --- |
| 19 squares across, 29 deep | MAZE-1 | **0** |
| No 2 x 2 block of open corridor | MAZE-2 | **0** |
| No corridor square with both coordinates even | C8's mechanism | **0** |
| Border ring intact — each of the four sides checked separately | MAZE-3 | **0** |
| Two seeds never give the same layout | MAZE-4 | **0** — 20 000 seeds, 20 000 distinct layouts |
| No corridor square with fewer than two ways on | MAZE-5 | **0** |
| Every corridor square reachable from every other | MAZE-6 | **0** |

## What the generator produces — 2 000 seeds

Measured by running the carve and the braid separately, which is also how `TheTwoPassesTest` in the
suite works.

| | Minimum | Maximum | Mean |
| --- | --- | --- | --- |
| Dead ends the carve leaves behind | 8 | 22 | 14.5 |
| Connectors the braid then opens | 8 | 21 | 14.3 |
| Corridor squares in the finished maze | 259 | 272 | 265.3 |
| Most ways on from any one square | 3 | 4 | 3.5 |

Corridor occupies **47.0 % to 49.4 %** of the 551 squares of the grid.

**The braid is doing real work.** The carve never once produced a maze that already satisfied MAZE-5;
it left between 8 and 22 dead ends every time. This matters because "zero dead ends" over a sweep
would read exactly the same whether the braid were removing them or the carve had happened never to
make any, and that is the first thing a later reader would want to know.

**Four is the whole range, and one never appears.** A square has four sides, so four ways on is the
ceiling, and it is reached. One never occurs, which is MAZE-5 seen from the other direction.

## Why MAZE-2 is not really a measurement at all

The table above reports 0 in 20 000, but the interesting thing about that row is that it could not
have been otherwise, and the argument is worth keeping because it is what caution C8 is protecting.

Call a square a **cell** when both coordinates are odd and a **connector** when exactly one is.
Neither pass ever opens a square with both coordinates even. Now take any 2 x 2 block of squares: of
its two columns one has an even x, and of its two rows one has an even y, so **exactly one of the four
squares has both coordinates even**, and that square is wall. So no 2 x 2 block can be open all
through, on any maze this generator will ever produce, at any grid size, under any random source.

That argument holds only while the braid stays on the lattice, which is precisely what C8 says. A
braid that opened an arbitrary wall would break it immediately, and the 20 000-seed sweep is what
would catch the day somebody relaxes the restriction without reading this.

**The sweep is therefore not the guarantee — the invariant is.** The sweep is what notices when the
invariant stops being true.

## The cost, and where the sweep lives

| Seeds | Time for `tests.test_maze_generator` |
| --- | --- |
| 400 — the default in the ordinary suite | 1.4 s |
| 20 000 — `MAZE_SWEEP_SEEDS=20000` | 58.8 s |

Generating one maze costs about **0.7 ms**; checking one against every property above costs about
**2 ms**. The default of 400 is the plan's "several hundred" and keeps
`python3 -m unittest discover` at 6.5 s for the whole suite. Anything longer goes behind
`MAZE_SWEEP_SEEDS` rather than into the default run.

## What this does not establish

- **Nothing about how a maze looks on a screen.** There is no screen geometry in the Domain
  (caution C5), so nothing here says whether 19 x 29 squares at two terminal columns each fit the
  40 x 30 window. That belongs to Presentation and to WI-5a.
- **Nothing about whether the mazes are *interesting*.** Every property here is a floor. Whether the
  layouts are pleasant to play is a human judgement and nobody has made it — see the human check in
  the PR summary.
- **Nothing about the distribution of layouts beyond "all different".** 20 000 distinct layouts out of
  20 000 seeds says the generator is not degenerate; it does not say the layouts are uniformly
  distributed over the space of legal mazes, and nothing in the specification asks for that.
