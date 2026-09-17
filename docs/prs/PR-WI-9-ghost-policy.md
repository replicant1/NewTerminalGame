# WI-9 — the ghost's movement policy

**Branch:** `r7/wi-9-ghost-policy`, cut from the tip of `main` at `5850eb4`. Not stacked.

| File | |
|---|---|
| `terminal_game/domain/ghost.py` | `next_ghost_move`, `candidate_directions`, `GhostMove`, `RandomSource`. |
| `tests/test_ghost.py` | 18 tests. |
| `docs/progress/r7-wi-9-ghost-policy.md` | |
| `docs/progress/r7-wi-4-frame-composition.md` | *(modified)* WI-4's log tail, carried forward as the lead ruled. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**210 passed, 0 failed, 0 skipped**, nothing deselected. 192 were already there; WI-9 adds
18.

---

## Lane B's `Direction`: accepted as it stands

You gave me the option of taking its shape up with lane B. **There is nothing to raise.**
`ways_on_from` returns `{Direction: Position}` in `Direction` declaration order, which is
exactly the vocabulary GHOST-3 needs, and `opposite()` is the right word for *the way it
came*. The policy — which of those ways to take — is entirely here, and none of it leaked
upward. No conversation was needed, so none was had.

## Two things I derived and then measured

**A real junction never offers more than two ways to turn.** Straight ahead must be blocked
before any choice happens, which leaves at most three exits; one of those is the way the
ghost came. Reasoned first, then measured over 2000 steps of the specimen maze: **widest
candidate set = 2.** So GHOST-3's *"picks one of the other ways on at random"* is always a
coin flip and never anything richer. Worth knowing before somebody writes a weighting.

**The candidate order is part of the contract, not an accident.** `choice` over a list is
only repeatable if the list is. If candidates came out of a set or a dict in whatever order
they happened to be in, the same seed would walk a different maze and **WI-16's seeded
playthroughs would be worthless.** Candidates are therefore built in `Direction`
declaration order, that is stated in the docstring, and a test walks the specimen maze 500
steps twice from one seed and requires the identical path.

## Ruling C-3, demonstrated rather than restated

The reverse clause is implemented and correct, and **its test uses a hand-built dead end**
as the plan requires — with a guard test asserting that the hand-built maze really *is* a
dead end, so the reversal test cannot pass for the wrong reason.

Alongside it, the other half of C-3 is now evidence rather than argument: the specimen maze
passes WI-1's structural checker (solid border, no dead ends, fully connected), and **5000
ghost steps around it reverse zero times**. That is what "unreachable in any maze this game
generates" means, and it is why nobody should be puzzled to find the clause uncovered by a
generated-maze test.

## How each requirement is pinned, and against which failure

- **GHOST-2** is the one easy to pass by accident, because a policy that turned at random
  would still go straight sometimes. So straight ahead is taken away from the random source
  entirely: the same crossroads is run through a chooser that **always takes the first**
  candidate and one that **always takes the last**, and both must give straight on. A
  ten-square corridor is then walked end to end.
- **GHOST-3** gets 4000 seeded draws at one T-junction: both turns must come up, the
  reverse must come up **zero** times, and the split must be even enough to be called
  uniform (2000 ± 300 — nine standard deviations, so it says something without being
  fragile).
- **GHOST-4** is met by the signature, so it is pinned by an **architecture guard** on the
  signature — there is no parameter a player could arrive in — plus a test that a hundred
  identical calls give one identical move, so nothing hidden can be in play.

## Design decisions (section 1.8 — reported, not asking)

**Randomness arrives through a `RandomSource` protocol** with one `choice` method,
satisfied structurally by `random.Random`. Ground rule 1.3 forbids Domain naming a
module-level random source, so the module cannot even import `random` to *type* the
parameter — the protocol is how the shape gets stated without the import.

**`GhostMove` returns both the direction and the square.** The square is what WI-10's
resolver wants; the heading is what the *next* call wants. Returning only the square would
make the caller re-derive the heading by subtracting two positions, which is the sort of
arithmetic that goes wrong once.

**Illegal states raise rather than degrade** — a ghost off the grid, on a wall, or on an
isolated corridor square with no way on. Each is a broken maze rather than a rule, and
returning "stay put" would make a bug look like behaviour. A random source that answers
with something it was not offered raises too: that is a GHOST-3 violation arriving from
outside, and a named error beats a wrong move.

## A correction I made to my own tests, recorded rather than left silent

Two of my test **expectations** were wrong on the first run and I fixed the tests, not the
code: `candidate_directions(CROSSROADS, heading SOUTH)` is `[WEST, EAST, SOUTH]` (I had
excluded the wrong direction), and a three-square stub is a dead end at **both** ends. No
working code was altered to make anything pass, here or anywhere.

## Notes for the items downstream

- **WI-10:** the resolver is handed a policy; `next_ghost_move(maze, square, heading, rng)`
  gives you `move.square` and you carry `move.direction` as the new heading.
- **WI-14:** `random.Random(seed)` satisfies `RandomSource` directly. The candidate order
  is stable, so a seed reproduces a walk exactly.
- **WI-8:** the ghost needs a starting heading as well as a starting square, and nothing in
  WI-8's bar mentions one. Not a contradiction — the plan leaves internal interfaces to us
  — but it is the one piece of ghost state nobody has claimed, and whoever assembles first
  will have to pick it.

## Window hygiene

Pure Domain: no toolkit, no clock, no filesystem, no `ctypes`, no window. The layer-rule
checker passes with the new module in place.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
