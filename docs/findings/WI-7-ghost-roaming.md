# WI-7 — how much the ghost actually chooses, and how much of the maze it sees

**Measured by:** DEV-B, run 6, on 30 mazes from DEV-A's real generator.
Pure Domain: no window, no toolkit, no clock.

This started as a test failure and turned into a measurement worth keeping.
It answers a question the requirements do not ask but a reviewer will:
**GHOST-4 says the ghost never hunts the player — so does it roam enough to
be a threat at all?**

---

## 1. The ghost chooses far less often than you would guess

GHOST-2 says the ghost carries straight on for as long as the corridor lets
it, and GHOST-3 only lets it choose where it cannot. So a choice needs *two*
things at once: straight on blocked, **and** more than one other way open.

Counted over 2,000 ticks on each of 30 generated mazes:

| | |
| --- | --- |
| Ticks where the ghost actually had a choice | **4.79 per 100** |

**Ninety-five ticks in a hundred, the ghost's next move is forced.** That is
not a defect — it is GHOST-2 working — but it means the ghost is very nearly
a deterministic walker, and it is worth knowing before anyone tries to reason
about its behaviour from the random source.

### How this was found

A regular lattice fixture I had hand-built for the reproducibility test
produced **one branch point in sixty ticks**. Two different seeds made the
same choice at the single place it mattered and produced *identical* walks,
so a test asserting "two different seeds give different walks" failed on
correct code.

The fixture was pathological, not the policy: its corridors run the full
width of the maze, so straight on is nearly always available. Real generated
mazes branch about three times as often. The test now asserts that **over
eight seeds more than one distinct walk arises**, and guards its fixture by
asserting the walk contains at least one branch point — so it cannot quietly
become vacuous the way it nearly did.

---

## 2. It does roam, and it does not lock into a cycle

2,000 ticks is about **4 minutes 45 seconds** of play at the ghost's ~7 ticks
a second. Over 30 mazes, starting from the middle corridor square with no
heading:

| | Corridor squares visited |
| --- | --- |
| Mean | **65.3 %** |
| Best (seed 7) | 93.2 % |
| Worst (seed 8) | 33.3 % |
| Typical maze size | ~265 corridor squares |

And the cycle question, which is the one that matters: on seed 0 the ghost
visited **237 of 264 corridor squares in its last 400 ticks alone**. It is
still roaming at the end of the run, not going round and round a loop it
fell into early.

**So the policy is well behaved on the mazes the generator actually
produces.** The near-determinism of section 1 does not trap it, because a
maze with no dead ends and no long straight runs presents forced turns often
enough to keep shuffling it around.

---

## 3. What this does *not* say

- **It says nothing about whether the game is winnable or losable**, only
  about where the ghost goes. Whether a player can clear 265 dots before a
  ghost covering two-thirds of the maze runs into them is a question for the
  scripted game (WI-19) and for a person playing it.
- **The worst case is a third of the maze.** One maze in thirty kept the
  ghost to 33 % over nearly five minutes. If a player ever reports a game
  where the ghost seemed to be somewhere else entirely, that is why, and it
  is the specified behaviour rather than a fault.

---

## 4. How to reproduce

Generate a maze with `terminal_game.domain.maze_generator.generate_maze`,
start at the middle corridor square with `heading=None`, and step it with
`terminal_game.domain.ghost.next_step`, counting distinct squares and the
ticks on which `onward_choices` offered more than one direction while
straight on was blocked. No window and no toolkit are involved.
