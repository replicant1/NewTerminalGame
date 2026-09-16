# WI-7 — The ghost's movement policy

**Developer:** DEV-B · **Branch:** `r6/wi-7-ghost-policy` · **Base:** `main` at `628cb40`
**Iteration:** M1 · **Depends on:** WI-5 (landed)

One pure function of the maze, the ghost's square and its heading. No clock,
no toolkit, no global random source, and **no player**.

## What is in it

| File | |
| --- | --- |
| `terminal_game/domain/ghost.py` | `GhostStep`, `next_step`, `onward_choices`, `GhostIsWalledIn` |
| `tests/test_ghost.py` | 23 tests on hand-built mazes |
| `docs/findings/WI-7-ghost-roaming.md` | What the policy actually does on 30 real mazes |

## The rule, in the order it is applied

1. **Carry straight on while the corridor allows it** (GHOST-2). At a
   crossroads with three ways onward it still goes straight: a junction is
   not a reason to choose.
2. **Otherwise choose uniformly at random among the other ways on**
   (GHOST-3), every way except the one it came from.
3. **Turn back the way it came only when there is nothing else** — a dead
   end. The real generator produces none, but the function is total on one.

`next_step` returns `GhostStep(direction, square)` — both, because "keeps
going in a straight line" only means something if the heading is carried to
the next tick.

## GHOST-4 is enforced by the signature

```python
def next_step(maze, square, heading, random_source) -> GhostStep
```

The player is not an unused parameter; it is **absent**. There is a test on
the exact parameter list, and another that no executable line of the module
contains the word `player`, `dot` or `score` — the docstring says out loud
why they are missing, so that test strips the prose before looking. SCORE-4
("a dot under the ghost is still there to be taken") is guaranteed the
simplest way available: this module has never heard of dots.

## I asked DEV-A for nothing

The plan names **WI-7 and WI-8 as M1's pair to watch**, because both consume
the maze and both might want to add a query to it, and it puts the maze's
query surface in DEV-A's ownership. WI-7 needed **no new query**:
`Maze.ways_on(square)` is exactly the ghost's question, `Direction.opposite`
gives the way it came, and `ways_on` returns directions in the stable
`DIRECTIONS` order, so a seeded choice is reproducible without my sorting
anything. Nothing of DEV-A's or DEV-C's is touched by this branch.

## A test failure that turned into a measurement

My first "two different seeds give different walks" test **failed on correct
code**, and the reason is worth reading.

The ghost chooses far less often than one would guess: a choice needs
straight-on blocked *and* more than one other way open. On the regular
lattice fixture I had hand-built, that happened **once in sixty ticks** — so
two seeds made the same choice at the single place it mattered and produced
identical walks.

The fixture was pathological, not the policy. So I measured the real thing —
30 mazes from DEV-A's generator, 2,000 ticks each, which is about 4 minutes
45 seconds of play at ~7 ticks a second:

| Measured | Result |
| --- | --- |
| Ticks on which the ghost actually had a choice | **4.79 per 100** |
| Corridor squares visited, mean | **65.3 %** |
| Best / worst maze | 93.2 % / 33.3 % |
| Seed 0, distinct squares in its **last** 400 ticks | **237 of 264** |

So the ghost is very nearly a deterministic walker — ninety-five ticks in a
hundred its move is forced — but it does not lock into a cycle, and on the
mazes the generator actually produces it roams two-thirds of the maze. Full
write-up in `docs/findings/WI-7-ghost-roaming.md`.

**The test was rewritten rather than the code.** It now asserts that over
eight seeds *more than one distinct walk arises* — which is the thing that
actually has to be true — and its `setUp` asserts the fixture contains at
least one branch point, so it cannot quietly become vacuous the way it
nearly did.

## A gap this opens for WI-11, raised with DEV-A rather than patched

`origin/main` has been merged in, bringing DEV-A's WI-6 (PR #32). It merged
clean and everything is green — but it surfaced something WI-11 will hit:

**`GameState` holds `ghost: Square` and no heading.** GHOST-2 is "keeps going
in a straight line for as long as the corridor lets it", which is only
meaningful if something remembers which line — and `next_step` returns the
new heading precisely so it can be carried to the next tick. There is
currently nowhere to carry it.

Nothing collides and nothing is broken. But WI-11 is DEV-A's and is the thing
that will call `next_step`, so **it is their call**, and I have not touched
their file. Raised on
[PR #32](https://github.com/replicant1/NewTerminalGame/pull/32#issuecomment-5692200058)
with the two options and my recommendation — `GameState` gains
`ghost_heading: Optional[Direction]`, since it is a frozen dataclass and the
alternative scatters the ghost's state across two places.

`heading=None` already covers the opening position, so WI-6 does not need to
invent an initial direction.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 305 tests — 305 passed, 0 failed, 0 skipped
```

That is with WI-6 merged in. 23 of the 305 are new here. Nothing in this
branch opens a window or imports a toolkit.

## What the tests own

Straight on: continues in a straight corridor, every time over 200 draws, and
**identically under 50 different seeds** — which is the consequence-level way
of saying no choice is being made. At a crossroads with three ways onward it
still goes straight, in whichever of the four directions it was going.

Choosing: at a T it never takes the square it came from over 500 draws; it
takes exactly the two arms and no others; over 2,000 draws the split is
between 45 % and 55 %; at a corner it always turns the one way there is.

Reversing: a dead end reverses, every time, and `onward_choices` there is
empty. A square with no way off it at all raises `GhostIsWalledIn` rather
than returning an illegal move.

Walking: over 400 ticks the ghost never stands on a wall, never moves more
than one orthogonal square, and the heading it reports is always the way it
actually went.

## Deviations needing a ruling

**`heading=None` is accepted, meaning "has not moved yet".** The plan
describes a function of the maze, the square and the heading; on the first
tick of a game there is no heading, because the ghost has been placed and has
not moved. Rather than leave WI-6 and WI-15 each to invent an initial
heading, `next_step` takes `None` and treats every way on as a candidate.
Additive to the plan, so it needs a ruling. If it is unwanted, the caller
supplies a heading and this branch of the code goes.

**`GhostIsWalledIn` for a square with no exits at all.** A dead end has one
way off and the ghost reverses out of it; a square with *none* is not
somewhere the ghost could have walked to, so I raise rather than invent a
move. The generator's MAZE-5 and MAZE-6 make it unreachable.

## Worth the technical lead's attention, though not a contradiction

The 4.79-branch-points-per-100-ticks figure is the specified behaviour, not a
fault — but it means the ghost's randomness has much less influence on a game
than the phrase "picks one of the other ways on at random" suggests. If
anyone later reasons about difficulty or about seeding from that phrase, the
number is the thing to reason from.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
