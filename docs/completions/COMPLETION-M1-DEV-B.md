# M1 — DEV-B's lane, complete

**Developer:** DEV-B · **Iteration:** M1, *the pieces of the game* ·
**Mode:** non-local, real pull requests, merged by me

DEV-B's M1 lane is WI-7 (2 days) and WI-9 (1 day). Both are built, merged,
and green on `main`. Nothing in this iteration opened a window.

---

## What landed

| Item | Branch | PR | State |
| --- | --- | --- | --- |
| **WI-7** — the ghost's movement policy | `r6/wi-7-ghost-policy` | [#33](https://github.com/replicant1/NewTerminalGame/pull/33) | **merged** |
| **WI-7a** — closing lines for WI-7's log | `r6/wi-7a-close-the-log` | [#37](https://github.com/replicant1/NewTerminalGame/pull/37) | **merged** |
| **WI-9** — the input translator | `r6/wi-9-input-translator` | [#40](https://github.com/replicant1/NewTerminalGame/pull/40) | **merged** |

| File | |
| --- | --- |
| `terminal_game/domain/ghost.py` | `next_step`, `onward_choices`, `GhostStep`, `GhostIsWalledIn` |
| `terminal_game/presentation/input_translator.py` | `translate`, and the intent vocabulary |
| `tests/test_ghost.py`, `tests/test_input_translator.py` | 23 + 25 tests |
| `docs/findings/WI-7-ghost-roaming.md` | What the ghost policy actually does on 30 real mazes |

---

## Suite, as left

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 374 tests in 3.8s

OK
```

**374 passed, 0 failed, 0 skipped**, on `main` with everything through WI-11
landed. 154 of the 374 are DEV-B's across M0 and M1.

---

## Announced, per amendment 1's rule 4

**The intent vocabulary** — `Intent`, `IntentKind`, `QUIT`, `move(direction)`
in `terminal_game/presentation/input_translator.py`. WI-15 consumes it. Put
to DEV-A on [PR #39](https://github.com/replicant1/NewTerminalGame/pull/39#issuecomment-5692246571),
and named in the presentation package docstring so it is greppable.

**Directions are DEV-A's, not mine** — see the contradiction below.

---

## Contradiction found in amendment 1

**The ownership table and the first-lander rule disagree about directions.**

The table says *"Directions and headings — DEV-B, in whichever of WI-7 or
WI-9 lands first"*. The first-lander rule, in the same section and stated as
the general rule, says the first spelling to land on `main` wins — and
`Direction` landed **on day one in DEV-A's WI-5**, as part of the maze's
query surface.

**The tree follows the first-lander rule.** WI-7 conformed to
`terminal_game.domain.maze.Direction`, WI-9 conformed to it, and DEV-A's
WI-11 imports it too. Four items, one vocabulary, no duplication.

**So the table row is what is wrong, not the code.** Declaring a
presentation-layer `Direction` beside the domain's — which is what the table
literally asks for — is exactly the duplication amendment 1 exists to
prevent. Recommending the row be corrected to name DEV-A (WI-5). No code
should move.

---

## The measurement worth keeping

**The ghost chooses on about 4.79 ticks in a hundred.** GHOST-2 means a
choice needs straight-on blocked *and* more than one other way open, and
those coincide rarely. Ninety-five ticks in a hundred the ghost's move is
forced.

It still roams: **65.3 % mean corridor coverage** over 2,000 ticks (about
4m45s of play) across 30 generated mazes, range 33–93 %, and seed 0 visited
237 of 264 squares in its *last* 400 ticks, so it does not settle into a
cycle. Full write-up in `docs/findings/WI-7-ghost-roaming.md`.

This mattered twice. It is why a test of mine failed on correct code — see
below — and it is the number anyone reasoning about difficulty should use
instead of the phrase "picks one of the other ways on at random".

---

## Two tests that were weaker than they looked, found and fixed

Recorded because the point of saying so is that somebody can disagree.

**In WI-7, a test failed on correct code.** "Two different seeds give
different walks" failed because my hand-built lattice fixture had one branch
point in sixty ticks, and the two seeds honestly made the same choice. The
fixture was pathological, not the policy. **The test was rewritten, not the
code**: it now asserts that over eight seeds *more than one distinct walk
arises*, which is the thing that has to be true, and its `setUp` asserts the
fixture contains a branch point at all so it cannot go vacuous.

**In WI-9, two assertions could not have failed.** One asserted
`"print" not in vars(module)` — builtins are not module globals, so it was
always true. One looped over a list and only asserted inside an `if`.
Replaced with a stdout/stderr capture across every key (the real guarantee),
an imports check that can fail, and a source check.

Several fixtures now assert their own significance in `setUp` — 696 non-blank
cells in five colours, five differing cells, at least one branch point, a
spread of more than 40 keys — so they cannot shrink to nothing and keep
passing.

---

## Raised with the other developers, not escalated

**With DEV-A, and taken:** `GameState` held `ghost: Square` with no heading,
but GHOST-2 needs the heading carried between ticks, which is why `next_step`
returns one. Raised on
[PR #32](https://github.com/replicant1/NewTerminalGame/pull/32#issuecomment-5692200058)
with two options and a recommendation; DEV-A added
`ghost_heading: Optional[Direction]` and `with_ghost_heading`. Their file,
their change, and their WI-11 now calls `next_step` through it.

**With DEV-C, and open:** `KeyPress` carries keysym and char and **no
modifier state**. Control-Q is correctly rejected (it keeps the keysym but
types a control character); **control-Up cannot be told from Up**, because an
arrow types no character either way, so control-Up moves the player. The
plan's WI-9 test list asks that modified keys map to nothing — modified
letters do, modified arrows cannot at this seam. Raised on
[PR #25](https://github.com/replicant1/NewTerminalGame/pull/25#issuecomment-5692247918)
**with a recommendation not to change it**: control-Up moving the player is
harmless, and a Tk modifier bitmask would spoil a deliberately
toolkit-neutral value. Flagged so it is a decision rather than an accident.

**Not raised, because it did not arise:** the plan names WI-7 and WI-8 as
M1's pair to watch, on the grounds that both consume the maze and might each
add a query in a different shape. **WI-7 needed no new query.**
`Maze.ways_on` is exactly the ghost's question.

---

## Still open

**For the technical lead:**

- The ownership-table contradiction above — a table correction, not a code
  change.
- **`heading=None` is additive to the plan.** `next_step` accepts it as "has
  not moved yet" and treats every way on as a candidate, so WI-6 does not
  have to invent an initial direction. Needs a ruling.
- **`tk_grid.create_surface` and `measure_metrics` still have no automated
  test** (from M0), because exercising them needs a live toolkit interpreter.
  Verified by hand, headlessly; exercised for real by WI-4.

**For a human**, unchanged from M0 and still unanswered: is Menlo 16pt in a
400 x 570 window large enough to read comfortably (**A4**); do the
double-line box glyphs join up cleanly at that size; does it flicker on a
mapped window. All three are WI-16's, which is DEV-B's in M3.

---

## Next for DEV-B

M2: **WI-12, the frame composer** — 3 days, depends on WI-1, WI-6 and WI-8.
WI-1 and WI-6 have landed; WI-8 is DEV-C's and I need its wall glyphs before
I can compose rows 0–28. The plan pairs WI-12 with WI-13 and fixes the
boundary: WI-13 owns row 29 and produces it as a value, WI-12 places what it
is given and writes nothing there itself.
