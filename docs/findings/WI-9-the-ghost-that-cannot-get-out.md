# WI-9 — the ghost that cannot get out

**Item:** WI-9, the ghost's policy. **Lane:** DEV-B, iteration M1.
**Measured on:** `wi-9-ghost-policy` at `0ef8a87`, Python 3.9.6, standard library only.

**In about 1 game in 62, the ghost is permanently confined to a loop covering as little as 4.5 % of
the maze, and no random source can change it.** This obeys GHOST-2 and GHOST-3 exactly as written. It
sits awkwardly with GHOST-1's *"one ghost roams the maze"*. Whoever decides what to do about it needs
the numbers, so here they are.

## How it happens

GHOST-2 and GHOST-3 together mean the ghost consults chance in exactly one situation: **ahead is
blocked, and two or more ways other than back are open.** Anywhere else the move is forced:

| situation | what happens | chance consulted? |
| --- | --- | --- |
| ahead is open | carry straight on (GHOST-2), even at a crossroads | no |
| ahead blocked, one other way | take it — there is nothing to choose between | **no** |
| ahead blocked, two or more others | pick at random (GHOST-3) | yes |
| ahead blocked, nothing but back | turn back (GHOST-3's last resort) | no |

**A corner is the second row, not the third.** Going round a closed ring of corridor, the ghost meets
a corner at every turn, each offering exactly one way that is not back. It takes it, every time,
deterministically. If the ring closes and the ghost never meets a genuine junction on it, it is on
that ring for the rest of the game.

That the braiding pass of WI-4 creates loops is not incidental — MAZE-5 requires it. Every dead end is
opened out, so the maze is full of rings. Most rings touch a junction somewhere; a few do not.

## The measurements

**How often the ghost actually chooses** — 30 games, 400 steps each, 12 000 steps in total:

| | |
| --- | --- |
| Steps where a real choice was made | **568 of 12 000 — 4.7 %** |
| Games where the ghost faced a choice within 400 steps | 28 of 30 |
| Step at which it first faced one | 4 to 62, mean 22.2 |

So **95 % of the ghost's moves are forced**, which is a fair description of GHOST-2 and GHOST-3 rather
than a defect: a one-square-wide maze does not offer many decisions.

**How often it is confined for ever** — 500 games, each walked until it either faced a real choice or
returned to a `(square, heading)` it had already been in:

| | |
| --- | --- |
| Games where the ghost is permanently confined | **8 of 500 — 1.6 %** |
| Length of the loop | 12 to 100 squares, mean 44.0 |
| Share of the maze it can ever reach | **4.5 % to 37.2 %**, mean 16.5 % |
| Seeds, for reproduction | 21, 26, 49, 120, 132, 142, 285, 320 |

A confined run is one that returns to a state it has been in **without having faced a single real
choice on the way**. That is the condition that makes it permanent rather than merely repetitive: with
no choice made, the policy is a pure function of `(square, heading)`, so the sequence repeats for
ever. `new_game(21)` is the smallest: a 20-square loop, 8 % of a 266-square maze.

**Why this is not simply "the ghost repeats itself".** Any deterministic walk on a finite grid must
eventually repeat a state. The distinction measured here is whether chance was ever consulted before
the repeat: seeds 0 and 4 also return to an earlier `(square, heading)`, but they had already made
choices, so a different random source sends them elsewhere. The eight above are unreachable by any
source.

## What it means for the requirements

**GHOST-2, GHOST-3 and GHOST-4 are met.** There is a test that a confined ghost still goes straight
wherever it can, never reverses, and never leaves the corridors. The policy is doing exactly what the
specification tells it to do.

**GHOST-1 says "One ghost roams the maze."** A ghost that can reach 4.5 % of the maze, for the whole
of a game, is not roaming the maze in any ordinary sense of the words. That is a tension between one
requirement's word and two others' mechanics, and **it is not the implementer's to resolve** — GHOST-2
and GHOST-3 are explicit, and the policy implements them as written.

**It is also not obviously a problem.** Nothing in the specification promises the ghost will threaten
the player, and END-1 to END-6 are all reachable without it: the player wins by eating every dot, and
a ghost stuck on a ring is an easier game rather than a broken one. Roughly one game in sixty being
easy may be perfectly acceptable. **That is a judgement about how the game should feel, which is the
user's, not an agent's.**

## If it is decided that the ghost should roam

Recorded so that nobody has to rediscover it, **not** as a recommendation and **not** implemented:

- **The cheapest change is to the maze, not the ghost.** The braid opens exactly one extra connector
  per dead end. Opening more would raise the junction density, and every invariant survives it —
  opening a connector on the odd lattice can only add ways on, so MAZE-2, MAZE-3, MAZE-5 and MAZE-6
  all still hold. This needs no change to the ghost at all.
- **Changing the ghost instead means changing GHOST-2 or GHOST-3**, which are requirements. A ghost
  that sometimes turned where it could go straight would break GHOST-2 as written.
- **Whatever is chosen, the check is this document's second table**, which can be re-run over 500
  seeds in a few seconds.

## What this does not establish

- **Nothing about whether a confined ghost is noticeable in play.** Whether a player would see it as
  "the ghost is stuck" or simply "an easy game" needs a person watching a real game, and no agent can
  judge it.
- **Nothing about GHOST-1's timing.** Seven moves a second is WI-11's; this measurement counts moves,
  not seconds.
- **Nothing about where the player starts relative to the loop.** START-2 puts the ghost furthest from
  the player, so a confined ghost starts far away; whether its loop ever comes near the player's half
  of the maze was not measured.
