# WI-7 — How often the ghost actually makes a choice

**Measured while writing the GHOST-4 test, and it changed the test.**

## The claim

Under the GHOST-2/GHOST-3 policy the ghost makes a **genuine** random choice
far less often than the shape of the code suggests. Working it through:

`ghost_heading` draws from the random source only when the square straight
ahead is a wall. At that point the reverse is removed from the ways on, and a
draw over a one-element tuple is not a choice — it always returns the same
element. So a genuine choice needs:

> the square straight ahead is a wall, **and** at least two ways on remain
> after the reverse is removed.

The ghost arrived along its heading, so the reverse is always open. That makes
the condition, exactly:

> **a square of degree three or more, entered along its one blocked
> direction.**

A degree-four square is therefore **never** a decision point: every direction
is open, so straight ahead always wins. A degree-three square is a decision
point from exactly one of its three arms — the one opposite its wall.

## The measurement

| Board | Genuine choices |
|---|---|
| `CROSS` (a regular 9 x 9 lattice), 200 ticks, from **every** corridor square and every heading | **at most 1**, and 0 for the rest of the run |
| `CIRCUIT` (hand-built for this), 200 ticks from (1, 4) facing UP | **20** |
| generated maze, seed 23, 300 ticks | 15 |
| generated maze, seed 5, 300 ticks | 14 |
| generated maze, seed 0, 300 ticks | 13 |
| generated maze, seed 7, 300 ticks | 4 |

On the regular lattice the ghost takes at most one fork and then settles into
a cycle that offers none, so **the whole 200-tick path is the same whatever
seed it is handed**. That is asserted as a test in its own right —
`TestTheHandWrittenBoardsAreWhatTheySay.test_a_regular_lattice_gives_the_ghost_almost_nothing_to_decide`
— so that this note cannot quietly go stale.

## Why it changed the GHOST-4 test

The first draft of the GHOST-4 test ran on `CROSS`. It passed. It would also
have passed against a ghost that hunted the player, because on that board the
ghost never reaches a fork at which hunting could show. The test was green and
proved nothing.

Two changes fixed it:

1. **The board.** GHOST-4 now runs on `CIRCUIT`, built so that the two
   three-way squares (1, 4) and (4, 4) are each entered along their blocked
   direction on every circuit, and again on a real generated maze.

2. **A guard that does not re-implement the policy.** Counting decision points
   inside the test would mean writing the policy out a second time and
   comparing it with itself. Instead the test changes the **seed** and
   requires the path to change. A path that moves when the seed moves and
   stands still when the player moves is reading the seed and not the player,
   and that is the whole of GHOST-4.

## What this is worth to somebody later

- **WI-9, when the ghost is wired into the real loop.** The ghost is not as
  random as it looks; over a long game it spends most of its time in a
  corridor cycle. If the game ever feels like the ghost is stuck in a rut,
  this is why, and it is the specified behaviour rather than a bug.
- **Anyone writing another seeded test over the ghost.** A run that reaches no
  fork is a run that proves nothing about the ghost's decisions. The cheap
  check is the one above: change the seed and see whether anything moves.
- **`random.Random.choice` over a one-element sequence still consumes
  randomness** but always returns the same element. A test that counts draws
  rather than outcomes would mis-read this policy badly.
