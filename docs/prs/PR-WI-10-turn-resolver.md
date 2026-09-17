# WI-10 — the turn resolver

**Branch:** `r7/wi-10-turn-resolver`, cut from `main` at `3a89d84`
**Lane:** B · **Iteration:** M2 · **Depends on:** WI-8
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**531 passed, 0 failed, 0 skipped** (485 inherited, 46 new)

The one place a game in progress changes, in
`terminal_game/application/turn.py`. First module in the Application layer;
it names no toolkit and no clock, and the layer rule agrees.

---

## END-3 is now structural, not sequential

Per the lead's ruling. The plan's section 1.6 named END-3 as the project's
single fragility because it lived in the order of two statements and **both
orderings end the game** — so a test observing "the game ended" would pass
either way, and the architect's caution C6 named the failure: if the collision
test ever migrates into the movement code, the requirement breaks silently.

`outcome_of` removes the hazard rather than guarding it:

```python
def outcome_of(state):
    if state.player == state.ghost:
        return Outcome.CAUGHT
    if state.dots_remaining == 0:
        return Outcome.CLEARED
    return Outcome.UNDECIDED
```

One total function of the state. The branches are mutually exclusive by
construction, so **the win branch is not merely tested second — it is
unreachable while the player and the ghost share a square.** There is no
collision test left to migrate, and no pair of statements anyone can reorder.

### The coupling that makes this safe, which is new and load-bearing

**A derived outcome is only as stable as the state it derives from.** END-5 is
what keeps it honest: once a game is decided the session stops ticking,
ignores moves, and leaves the last picture standing, so nothing can change
underneath a decision and re-derive a different answer.

> **WI-11's Decided state is what keeps this module's outcome correct.**
> If anything ever makes the state mutable after a decision, END-3 breaks
> again in a new way.

This module does its half with an `is_over` guard at the top of both
resolvers, and both are tested. **Lane A needs to know this** — it is the kind
of dependency that is invisible until someone optimises the Decided state
months from now.

### One behavioural consequence, which the ruling did not cover

Deriving rather than sequencing forces the **eat to happen before the
derivation**, because a win cannot be seen until the last dot is gone. So:

> A player who eats the last dot on the ghost's square **does eat it and does
> score it**, and is still caught.

My earlier early-return sketch would not have scored it. No requirement
distinguishes the two — but **SCORE-1 and SCORE-2 read literally favour this
one**: the player did move onto a square that still had a dot, so it is eaten,
and each dot eaten adds one. STAT-3 puts the score on screen, so this is
visible to a player rather than internal. There is a test named for it, and I
am flagging it here rather than letting it be discovered.

---

## How END-3 is tested

On a board where the two orderings give **different answers**: the player one
step west of the ghost, and the ghost standing on the last dot in the maze.

| resolver | answer |
|---|---|
| as written — move, eat, derive | **`CAUGHT`** |
| with the win tested first | `CLEARED` |

Three tests, not one:

1. **The outcome is `CAUGHT`.** The requirement.
2. **The board really would read as a win under the other order** — after the
   move the state satisfies *both* end conditions at once (`player == ghost`
   *and* `dots_remaining == 0`). This says the board discriminates, without
   touching the resolver, so the test above cannot quietly stop meaning
   anything.
3. **The score and the dot** — asserted, so a reversed resolver fails on three
   counts rather than one flag.

And a **control**: eating the last dot *away* from the ghost is a win. Without
it, "the outcome is caught" would be satisfied by a resolver that never said
anything else.

**Nothing was checked by breaking working code.** No step was swapped, no
guard removed, no value mutated. The boards were built to discriminate.

---

## MAZE-3 — stopped by the border, not by catching anything

The legal moves are exactly `maze.ways_on_from(player)`, which yields only
corridor squares that are on the grid. So:

* a move into a wall is blocked because **it is not a way on** (CTRL-3);
* a move off the edge is blocked the same way — **the resolver never asks
  about a square outside the grid at all**, so WI-1's decision to raise rather
  than answer `WALL` is never exercised and never needs to be;
* movement cannot wrap, because a wrapped square is not adjacent and so is
  never a way on.

A swept test also pins the underlying fact: in every generated maze all
corridor squares are strictly interior, so the grid's edge is unreachable in
play and the bounds question never arises.

---

## The rest of the bar

**CTRL-1, CTRL-2** — one intent, exactly one square, no drift between calls.

**CTRL-3** — a blocked move returns *the identical state object*, so "nothing
at all" is not four separate things that might each be got right. There is
also a test for the dangerous case: standing beside the ghost and pressing
into a wall, which a resolver that moved first and checked afterwards would
turn into a loss.

**SCORE-1, SCORE-2, SCORE-3** — eaten dots stay eaten across a walk away and
back; three dots score 1, 2, 3; an empty square scores nothing.

**END-1 on both arms**, and a test that **the same function decides both**, so
the player-walks-into-ghost and ghost-walks-into-player cases cannot drift
apart.

**SCORE-4** — a ghost move touches no dot and no score.

**END-2, GAME-2** — and a whole game played out on a real generated maze,
walking every corridor square and checking the win lands exactly when the last
dot goes, with the score equal to the number of dots there were.

**The intent vocabulary** (`Intent`) — the five things a key press can mean,
named here so WI-11 and WI-13 cannot each invent a different alphabet. A key
that means none of them produces no intent at all, which is CTRL-5 and WI-13's
to express.

---

## What this deliberately does **not** do

Continuing the shape the lead asked for on any item owning both sides of a
seam. I own WI-8 and WI-10, so nothing external would have stopped me
reaching into either.

* **It does not decide when to stop the game.** END-5 is WI-11's. The
  `is_over` guard makes the resolver inert on a decided game; it does not own
  the Decided state, the tick, or the key handling.
* **It does not move the ghost.** GHOST-1 to GHOST-4 are WI-9's. The ghost's
  next square is a parameter; the policy is not called from here and is not
  imported.
* **It does not translate keys.** CTRL-4 and CTRL-5 are WI-13's. `Intent` is a
  vocabulary; nothing here reads a key.
* **It does not render anything.** STAT-3 chooses its words from the outcome;
  this only says which outcome.
* **It does not construct the opening position.** That is WI-8's `new_game`.

## Deviations needing a ruling

1. **`resolve_ghost_move` validates its square** and raises if it is not a
   corridor square on the grid. The plan says "move, then test collision" —
   two steps, not three. I added it because a silent ghost-inside-a-wall when
   WI-14 wires up the policy would be far worse than a loud error, and both
   branches are tested. Additive.
2. **`resolve_player_intent`** is a convenience wrapper for WI-11. The core is
   `resolve_player_move(state, direction)`; this only unpacks an intent.
3. **`Intent.QUIT` is in the vocabulary** although quitting is WI-11's and
   WI-13's. Included so WI-13 does not have to invent a word for it.

## Contradictions found

**None.** END-1, END-2 and END-3 are consistent once the precedence is fixed,
and fixing it is what END-3 *is*.

One observation for the lead's section 1.6 note: **the fragility is retired by
design rather than by the user spending effort on it.** The question the note
puts to the user no longer has a cost attached to either answer, because there
is no longer an ordering to get wrong.

## What needs a human

Nothing from this item.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
