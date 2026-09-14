# WI-8 — the player's move

**Branch** `wi-8-player-move`.
**Stacked on `wi-7-game-state` at `af4c6d9` — not cut from `main`.**
**Lane** A (DEV-A), iteration M1. **Local mode** — this file stands in for the
pull request; nothing pushed, no `gh` used, not merged.
**Suite** `python3 -m unittest discover` — **339 passed, 0 failed, 0 skipped**.
**Windows opened: none.** Pure domain.

Requirements: **CTRL-1, CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3, SCORE-5**.

## Why it is stacked

WI-8 depends on WI-7, and WI-7 has not merged — `main` is frozen at `c4171fb`
because nobody can currently reach the primary tree. Cutting WI-8 from `main`
would have meant writing against a `GameState` that is not there. So it is
stacked, and **it must be merged after `wi-7-game-state`**. Its diff against
`wi-7-game-state` is exactly the three files below; against `main` it would also
show WI-7's, which is the usual reason a stacked branch is read against its
parent rather than against the trunk.

## What is new

| File | What it is |
| --- | --- |
| `terminalgame/domain/player.py` | `move_player(state, direction)`, and `NotADirection`. |
| `tests/test_player.py` | 30 tests. |
| `docs/progress/wi-8-player-move.md` | The progress log. |

**No existing file is changed.** That is deliberate — see "Keeping out of DEV-B's
way" below.

```python
from terminalgame.domain.player import move_player

state = move_player(state, EAST)   # a new state, or the same one if blocked
```

## CTRL-3, which is the whole of the risk

> A press towards a wall does nothing at all.

**A blocked move returns the state object it was given.** Not a copy, not an
equal state — the same object, so `move_player(s, NORTH) is s`.

That is the strongest available form of "nothing at all", and it is strong in a
way that matters later: the alternative is to assert that each field came back
unchanged, and such a list goes stale the moment somebody adds a field. Identity
cannot go stale. The test that checks every field individually is there too, but
it is the identity assertion that will still be correct in six months.

**The wall is checked before anything else**, so a blocked move cannot eat a
dot, cannot score, and cannot half-happen. There is a test that puts a dot on a
wall square — nothing should ever do that, but if it did, the ordering is what
stops the player scoring through the wall.

Anything off the grid reads as `WALL` (WI-4's decision), so the border ring
needs no special case; there is a test walking into it from all four sides.

## The trap, and what was done about it

Two of these requirements are satisfied by a function that does nothing at all:

- **CTRL-3** — "a press towards a wall does nothing" is green against a
  `move_player` that never moves anybody.
- **SCORE-3** — "re-entering an eaten square scores nothing" is green against
  one that never scores.

So **every test of either also exercises, against the same state, the case that
must change**:

- the CTRL-3 tests move a way that *is* open and check the player arrived and
  the score went up — `assertIsNot` on the open direction sits in the same test
  as `assertIs` on the blocked one;
- the SCORE-3 test asserts the first visit scored **1** before asserting the
  second visit left it at 1, with a message on each so a failure says which half
  broke.

A `move_player` that never moved, or never scored, fails these rather than
passing them. This is reasoned from the assertions, not demonstrated by breaking
anything: **no working code was modified to watch a test go red.**

The same shape appears once more in `test_walking_the_whole_ring_twice_scores_
only_the_first_lap`, which first asserts that one lap ate *every* dot on the
ring — so the second lap scoring nothing means something.

## What a move is not allowed to touch

The boundary with WI-9 (DEV-B's) and WI-10 is kept by test rather than by
agreement:

- a move **never moves or turns the ghost** — checked for all four directions;
- a move **never changes the maze** (`assertIs` on it);
- a move **never decides the outcome**. Walking onto the ghost's square and
  taking the last dot both leave `outcome` at `PLAYING`, because reading an
  ending out of that state is WI-10's ordered question and it runs afterwards;
- the state handed in **is never modified in place**.

The ghost's dot is taken normally when the player steps onto it — SCORE-4 from
the player's side. Whether that move is also a loss is WI-10's; here it must
simply score, and there is a test saying so.

## Keeping out of DEV-B's way

DEV-B is on WI-9, stacked on the same parent. I found nothing I needed to change
in shared code, and did not have to ask, because:

- **the move needed nothing added to WI-7's module** — `GameState.with_changes`
  already does all of it, so `game_state.py` is untouched;
- **`tests/test_layering.py` is untouched.** Adding `player.py` to its "the
  domain is where it is said to be" list would be an adjacent-line edit to the
  one file DEV-B is also likely to add `ghost.py` to — a predictable conflict
  for no gain, since `domain_files()` already sweeps my module automatically in
  the purity, dependency and screen-geometry scans. The explicit "the scan
  really does look at this module" assertion lives in `tests/test_player.py`
  instead, importing the helper from the layering module rather than
  duplicating it, so the guarantee exists without the collision.

If WI-9 turns out to need a field WI-7 did not define, the plan says DEV-B
agrees it with me first; nothing in WI-8 pre-empts that.

## Deviations, for a ruling

One, and it is small.

**`NotADirection` is raised for anything that is not one of the four.** The plan
does not mention error behaviour. §11.8 says refuse rather than degrade, and the
alternative here is worse than usual: treating an unrecognised direction as "no
move" makes it indistinguishable from CTRL-3's wall, so a wiring mistake in
WI-11 would look exactly like a player pressing into a wall and would never be
found. CTRL-5 says no other key does anything — that is the loop's filter to
apply, and this refusal is what makes a failure of it visible.

## One thing I did not do, deliberately

**`move_player` does not refuse to move a finished game.** If `outcome` is
`CAUGHT` or `CLEARED`, it will still move the player, because nothing in WI-8's
brief says otherwise and the outcome belongs to WI-10.

That is a real gap, not an oversight, and it needs an owner: END-5 and END-6 say
the finished picture stays and `q` is the only way out, so *something* must stop
arrow keys after the game ends. The natural places are WI-10 (which owns the
outcome) or WI-11 (which owns the loop and is where CTRL-5's key filtering
already has to live). **I have flagged it rather than choosing**, because WI-10
is my next item and deciding it here would pre-empt a boundary the plan draws
deliberately. There is a test pinning today's behaviour so that whoever closes
it does so on purpose.

## Assumptions

None new. Q1, Q2 and Q3 are untouched by this item — the move does not care how
the game ends, whether the automation permission exists, or which metric placed
the actors.

## Contradictions found

**None.** CTRL-1 to CTRL-3 and SCORE-1 to SCORE-3 and SCORE-5 are consistent
with each other and with WI-7's state, and all seven are met.

One observation, not a contradiction: **CTRL-2's "the player never drifts on
their own" is a property of the design rather than something this function can
be tested for.** Drift would need somewhere to live — a velocity, a held
direction — and there is nowhere: the move is a function of a state and a
direction, and `GameState` carries no such field. The test is structural and says
so in its docstring rather than pretending to be behavioural; the behavioural
half of CTRL-2 is that two calls move exactly two squares.

## What needs a human

1. **Whether a finished game should still accept arrow keys** — the gap above.
   A ruling, not a measurement.
2. **Nothing else.** No window was opened, nothing touched the desktop, and
   every requirement in this item is checkable without a person looking at a
   screen.

## Commits

| | |
| --- | --- |
| `9a6949b` | WI-8: the player's move |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
