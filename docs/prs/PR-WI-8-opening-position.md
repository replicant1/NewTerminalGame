# WI-8 — the opening position

**Branch:** `r7/wi-8-opening-position`, cut from `main` at `9863a95`
**Lane:** B · **Iteration:** M2 (moved from M1 with the reassignment) ·
**Depends on:** WI-1
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**467 passed, 0 failed, 0 skipped** (418 inherited, 49 new)

The game's starting state and the vocabulary for how a game ends, in
`terminal_game/domain/state.py`.

This item moved from lane C to lane B so that one developer owns WI-8 and
WI-10, and the seam section 7 asked two people to manage — *"WI-8 creates the
game state and owns the outcome vocabulary; WI-10 is the only thing that
changes it"* — stops existing rather than being managed. **That makes the
boundary easier to move by accident, so the section below on what is
deliberately absent is the one to read.**

---

## START-1, and why it is swept rather than sampled

The grid centre is `(9, 14)`. **Its row is even**, so on WI-2's carving
lattice it is a *connector* rather than a cell, and it is carved only when
that particular wall happens to be opened.

> Measured over 200 seeds: the centre is corridor in **109** of them.

So an implementation that assumed the centre was walkable would **pass a
single-seed test and fail on nearly half of real games**. START-1 is therefore
tested over 120 seeds, asserting the rule that holds in both halves: the
player is on the centre when the centre is carved, and on the nearest square
that is carved otherwise.

That nearest square is always `(9, 13)`. The four squares at distance 1 are
`(9, 13)`, `(9, 15)`, `(8, 14)` and `(10, 14)`; the last two have **both**
coordinates even and so are never carved at all, and of the remaining two
reading order takes the upper. Both are cells on the lattice, so both are
corridor in every generated maze — a separate test pins that, because it is
what makes "never further than one square from the centre" true.

**The sweep also asserts that both halves actually occurred.** A sweep that
happened to draw only mazes with a carved centre would pass while saying
nothing about the other half — a single-seed test wearing a sweep.

## START-2, and showing which metric was used

*"The corridor square furthest from the player, measured across the grid
rather than along the corridors"* is only testable on a maze where the two
answers differ. There is one, and it differs loudly:

| | square | straight-line | walking |
|---|---|---|---|
| straight-line furthest — **what START-2 asks for** | `(4, 20)` | 328 | 20 steps |
| walking furthest — what it explicitly does not | `(4, 4)` | 8 | 36 steps |

An implementation measuring along the corridors would put the ghost **two
squares from the player** at the start of every game. The test asserts both
that the right square is chosen and, separately, that the walking-furthest
square is *not* — the second is the failure the fixture exists to catch.

**A test checks that the fixture really does discriminate** before the tests
that rest on it. Without that, a later edit could flatten the maze into one
where both metrics agree and the tests would keep passing while proving
nothing.

### The tie-break (assumption P7)

**Reading order — topmost, then leftmost**, for both START-1 and START-2.
Reading order is the one ordering WI-1 already guarantees is stable, so it
costs nothing to adopt and cannot drift. It is pinned by tests for both, and
it is not a rare case: the tie between the squares above and below the centre
fires in roughly half of all games.

## START-3 and START-4

A dot on every corridor square **except the player's** — and only the
player's. The ghost's square keeps its dot, which is SCORE-4: *"a dot under
the ghost is still there to be taken."* Score zero, outcome undecided.

## SCORE-5 — "never goes down", structurally

`GameState` is a slotted class with read-only properties. Of its four
transitions, **exactly one touches the score, and it adds one**. There is no
setter, no subtraction anywhere in the module, and a negative score cannot
even be constructed.

Tested as a consequence rather than a claim: assigning to `score` raises; a
walk over the whole transition surface asserts the number never falls; eating
a square whose dot has gone returns the state unchanged (SCORE-3, so WI-10 may
call it on every move without asking first); and eating the same dot twice
scores once.

---

## What is deliberately absent, and why that matters more than usual

Because I now own WI-8 *and* WI-10, nothing outside this file would have
stopped me implementing the endgame rules here. Section 4 of the plan traces
**END-1, END-2 and END-3 to WI-10**, and SCORE-1 to SCORE-3 likewise. So:

* `Outcome` names the three answers. **It does not decide which applies.**
* `with_player_at` moves the player and **does not eat**. Whether a move is
  legal is CTRL-3's and whether it eats is SCORE-1's — both WI-10's.
* `ate_dot_at` removes a dot and scores it. **When to call it is WI-10's.**

**One design note for WI-10, raised here rather than acted on.** END-3 — *"eating the last dot on the square the ghost is standing on is a loss"* — is
the fragility the plan names in section 1.6, because it lives in the order of
two steps and both orderings end the game. A derived outcome that tests
"caught" before "cleared" would make END-3 structural rather than
order-dependent, and retire that fragility. **I have not done it**, because
the outcome rules are WI-10's and pre-empting them from WI-8 is exactly the
boundary-creep the reassignment makes easy. I will decide it in WI-10, in the
open, with the plan's required test on a board where the two orderings
disagree.

---

## Deviations needing a ruling

1. **`distance_squared` lives in `state.py`, not `maze.py`.** It is geometry
   about `Position` and arguably belongs with it, but `maze.py` is now
   imported by four other items and I would rather not touch a file that many
   people are branching over for a helper only this item uses. Move it if you
   would rather it sat with `Position`.
2. **`GameState` carries the maze.** The alternative is passing the maze
   alongside the state everywhere. It makes the state self-contained for
   WI-10 and WI-11; it also means a state is only meaningful against its own
   maze, which is the intent but is worth naming.
3. **`nearest_corridor_to` and `furthest_corridor_from` are public.** They
   are the two halves of START-1 and START-2 and are tested directly. WI-17's
   human-verification pack may want them; nothing else should.

## Contradictions found

**None.** START-1 to START-4, SCORE-4 and SCORE-5 are mutually consistent and
consistent with the specimen.

One near-miss worth recording rather than a contradiction: START-3 says *"every
corridor square holds one dot, except the square the player starts on"* while
SCORE-4 says a dot under the ghost is still there. These agree — the exception
is the player's square and only the player's — but they are two requirements
four sections apart that together decide one line of code, and an
implementation that excepted both actors would satisfy a careless reading of
START-3. There is a test named for it.

## What needs a human

Nothing from this item.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
