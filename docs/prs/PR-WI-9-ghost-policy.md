# WI-9 — the ghost's policy

**Branch:** `wi-9-ghost-policy`, **stacked on DEV-A's `wi-7-game-state` at `af4c6d9`**, not cut from `main`
**Lane:** DEV-B, iteration M1
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **344 passed, 0 failed, 0 skipped** (7.7 s).
**Windows opened:** none. Pure domain.

**Why it is stacked.** WI-9 depends on WI-7's state vocabulary — `GameState`, `ghost`, `ghost_heading`
— and WI-7 cannot merge while nobody can reach the primary working tree. Based on `main` this branch
would show WI-7's commits as its own and the diff would be unreadable. The baseline to compare
against is therefore **309 tests on `wi-7-game-state`**, not `main`'s 256; WI-9 adds 35.

**Merge order** when the tree unfreezes: WI-3, WI-7, WI-8, then this. I will merge `main` in and re-run
before reporting it ready, so what is merged is what was tested.

---

## What this is

Where the ghost goes next. A pure function of the maze, the ghost's square and its heading — GHOST-2,
GHOST-3, GHOST-4 and SCORE-4. GHOST-1's seven-times-a-second clock is WI-11's; this module says
*where*, never *when*, and has no clock in it.

| File | What it is |
| --- | --- |
| `terminalgame/domain/ghost_policy.py` | `ways_on`, `choose_heading`, `ghost_move`, `move_ghost`. |
| `tests/test_ghost_policy.py` | 35 tests in nine classes. |
| `docs/findings/WI-9-the-ghost-that-cannot-get-out.md` | The one measurement that needs a decision. |
| `docs/progress/wi-9-ghost-policy.md` | The progress log. |

**`tests/test_layering.py` is not touched by this branch** — see the section on it below.

## The rule, stated once

At a square, the **ways on** are the sides that are corridor. Given a heading, **ahead** is where it is
going, **back** is `heading.opposite()`, and **the others** are the ways on that are neither.

- **GHOST-2** — if ahead is a way on, take it. This wins even at a crossroads with side openings: the
  corridor still lets the ghost carry straight on, so it is not a place it has to choose.
- **GHOST-3** — otherwise pick at random among the others; take back only when the others are empty.

Back is therefore never chosen while anything else is open, which is "only when there is no other
choice" written as code rather than hoped for.

## GHOST-4 is enforced by the signature, not by good behaviour

`choose_heading(maze, square, heading, random_source)` and `ghost_move(...)` **do not take the
player's position.** Not take it and ignore it — do not take it. A function that cannot see something
cannot take notice of it, so GHOST-4 stops being a promise about behaviour and becomes a property of
the code that a reader checks in one line.

`move_ghost(state, random_source)` is the one place it could be lost, because it is handed a whole
`GameState` and that contains the player. It is three lines and pulls out exactly the maze, the square
and the heading before calling the policy.

Checked both ways, because either alone is weak:

- **structurally** — `inspect.signature` on each policy function, asserting no parameter is or
  contains "player", and pinning the parameter list exactly so that adding one later is a deliberate
  act rather than a slip;
- **by consequence** — the plan's own words: the player is placed on **every corridor square of the
  maze in turn** and the ghost's move must be identical every time. And again over a 50-move run from
  three widely separated player positions, because a ghost that hunted only when close would survive a
  single move.

There is also a test that the ghost **walks onto the player's square** when the player is directly
ahead. "Takes no notice" cuts both ways: a ghost that avoided the player would fail GHOST-4 just as
surely as one that chased them, and no test asserting "it did not move towards the player" would
notice.

## Every negative requirement is paired with its positive

Two of these requirements are negative, and a negative is where a test goes vacuous most easily,
because **an implementation that never does the thing at all passes every test checking it did not do
the thing.**

| The negative | What would pass it vacuously | The positive that fixes that |
| --- | --- | --- |
| GHOST-3: turns back **only** when forced | a ghost that can never reverse | `test_it_does_turn_back_in_a_dead_end` — and from all three approach directions. The generator cannot make a dead end (MAZE-5), so the maze is written out by hand |
| GHOST-4: takes **no notice** of the player | a ghost that never moves toward the player because it never moves at all | the player on every corridor square in turn, plus the test that it *does* walk onto the player |
| GHOST-2: does not stop to choose where it can go straight | a policy that never consults chance | the crossroads is run with a random source that **raises if asked**, and the tee proves chance *is* consulted elsewhere |
| SCORE-4: changes nothing but the ghost | a `move_ghost` that changes nothing at all | the same test asserts both actors' fields moved over the run: `{"ghost", "ghost_heading"}` exactly, no more and no less |

One more that is easy to miss: north is first in `DIRECTIONS`, so **a policy that simply took the first
way on would look correct whenever the ghost happened to be heading north.**
`test_going_straight_on_is_not_an_accident_of_the_direction_order` drives the same crossroads heading
south, east and west.

## The one thing that needs a decision — and it is not a bug

**In about 1 game in 62, the ghost is permanently confined to a loop covering as little as 4.5 % of the
maze, and no random source can change it.**

This came out of a test of mine that failed. I had assumed different random sources give different
ghost walks; on maze 21 they do not. Rather than retune the test around it I chased why, and the
answer is a genuine property of GHOST-2 and GHOST-3 together.

The ghost consults chance in exactly one situation: ahead blocked **and** two or more ways other than
back open. **A corner is not that situation** — it offers exactly one way that is not back, so the
ghost takes it deterministically. Round a closed ring that never touches a junction, the ghost goes
round for ever.

Measured (full workings in the finding):

| | |
| --- | --- |
| Steps where the ghost makes a real choice | **4.7 %** of 12 000 steps over 30 games |
| Games where the ghost is confined for ever | **8 of 500 — 1.6 %** |
| Size of the loop | 12 to 100 squares; 4.5 %–37.2 % of the maze, mean 16.5 % |
| Reproduce with | `new_game(21)`, `new_game(26)`, and six more seeds named in the finding |

**GHOST-2, GHOST-3 and GHOST-4 are all met** — there is a test that a confined ghost still goes
straight wherever it can, never reverses and never leaves the corridors. **But GHOST-1 says "one ghost
roams the maze"**, and a ghost on 4.5 % of the maze is not roaming it. That is a tension between one
requirement's words and two others' mechanics, and it is **not the implementer's to resolve**: GHOST-2
and GHOST-3 are explicit and I implemented them as written.

It may well not matter — nothing promises the ghost will threaten the player, every ending stays
reachable, and one game in sixty being easy could be entirely acceptable. **That is a judgement about
how the game should feel, and it is the user's.** The finding records, without recommending, that the
cheapest lever is the *maze* rather than the ghost: opening more than one connector per dead end in
WI-4's braid would raise the junction density, and every maze invariant survives it because opening a
connector on the odd lattice can only add ways on.

The property is pinned by tests either way, so whoever changes anything sees exactly which assertions
move.

## `tests/test_layering.py` — deliberately not touched

`maze.py` and `maze_generator.py` are named explicitly in that file's module list, and
`game_state.py` was added to it by WI-7. **`ghost_policy.py` is not**, and that is a decision rather
than an oversight — so it is recorded here, as the conductor asked, so the asymmetry does not read as
an accident.

`domain_files()` walks the whole package, so the new module is swept by every purity test
automatically; the explicit entry buys nothing. What it costs is an adjacent-line edit in the one file
the technical lead has flagged as the cross-lane risk, touched by four items across two lanes.
**DEV-A made the same call for `player.py` in WI-8**, and matching it means WI-8 and WI-9 add no
conflict to that file at all.

The equivalent assertions live in this item's own test file, importing the layering helpers rather than
duplicating them: that the purity sweep really does include `ghost_policy.py`, and that the module
imports nothing whatever from outside the Domain — it needs nothing but its arguments and does not
even import the maze.

## What WI-11 and WI-10 inherit

```python
from terminalgame.domain.ghost_policy import move_ghost, ghost_move, choose_heading
```

- **`move_ghost(state, random_source)` → a new `GameState`.** Changes `ghost` and `ghost_heading` and
  nothing else.
- **It does not set the outcome.** Whether the move ended the game is WI-10's ordered function, asked
  after every move by either actor. Deciding it here would put caution C6 in two places, and there is
  a test that a ghost walking onto the player leaves the outcome `playing`.
- **`random_source` is required, never defaulted**, on every entry point — there is a test for it — so
  no caller can get an unreproducible ghost by forgetting an argument.
- **The state handed in is not modified and not handed back.** `GameState` is immutable, so mutation
  is impossible, but returning the same object would let a caller holding the old state see the ghost
  teleport.

## Deviations, for a ruling

**1. A ghost with nowhere to go stays put and keeps its heading**, rather than raising. Plan §11.8
says to refuse where an argument makes a requirement impossible, and this looked like a candidate. It
is not: GHOST-2 and GHOST-3 are both conditioned on there being somewhere to go, so a walled-in square
does not make either unsatisfiable — it makes them vacuous. Standing still is a well-defined answer a
caller can use.

It is also consistent with DEV-A's neighbouring decision: `opening_heading` in WI-7 falls back to a
fixed direction for the same case rather than failing, reasoning that "a ghost that cannot move is not
a broken opening position, it is a maze with nowhere to go". **Two sibling functions in one subsystem
disagreeing about this would be worse than either choice alone.** The case is unreachable in play —
MAZE-5 gives every corridor square at least two ways on, and there is a test asserting that over
20 generated mazes — so it is only constructible by hand.

**2. `ways_on(maze, square)` is public.** The plan asks only for the policy. It is exposed because
every test of GHOST-2 and GHOST-3 needs to ask "what could the ghost have done here", and a test that
recomputed that itself would be marking its own homework.

## Contradictions found

**One, with the measurement: GHOST-1's "roams the maze" against GHOST-2 and GHOST-3's mechanics.**
1.6 % of games, 4.5 %–37.2 % of the maze reachable, 500 seeds, reproducible from eight named seeds.
Full workings in `docs/findings/WI-9-the-ghost-that-cannot-get-out.md`. Not a blocker; needs a
decision that is the user's rather than mine.

## What needs a human

**One, and it is the decision above.** Whether a ghost confined to a loop is noticeable in play —
whether a player reads it as "the ghost is stuck" or simply as an easy game — needs a person watching
a real game, and no agent can judge it. Once the game runs end to end, the exact steps are:

```
python3 -c "from terminalgame.domain.game_state import new_game; print(new_game(21).maze.as_text())"
```

then play seed 21 and seed 26 and watch whether the ghost ever leaves its circuit. Both are the
smallest confined cases measured. What to look for: whether the game still feels like it has a ghost
in it.

**No window was opened and nothing touched the desktop.**

## Commits

| | |
| --- | --- |
| `d2406b0` | WI-9: start the log, and measure the layering-file merge rather than guess |
| `0ef8a87` | WI-9: the ghost's policy, with GHOST-4 enforced by the signature |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
