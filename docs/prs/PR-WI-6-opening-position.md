# WI-6 — The opening position

**Developer:** DEV-A · **Branch:** `r6/wi-6-opening-position` · **Base:** `main`
**Depends on:** WI-5 (merged) · **Iteration:** M1
**Requirements:** START-1, START-2, START-3, START-4, SCORE-1, SCORE-3, SCORE-5, GAME-1, GAME-2

---

## What this is

The game at the moment the window opens, and the vocabulary it is carried in.
Three modules, all Domain, all pure — no toolkit, no clock, and, unlike WI-5
and WI-7, **not even a random source**.

| Module | What it holds |
| --- | --- |
| `terminal_game/domain/dot_field.py` | `DotField` — which corridor squares still hold a dot (START-3, SCORE-1, SCORE-3) |
| `terminal_game/domain/game_state.py` | `Score`, `Outcome`, `GameState` (START-4, SCORE-5, GAME-2) |
| `terminal_game/domain/opening_position.py` | `player_start_square`, `ghost_start_square`, `opening_position` (START-1, START-2) |

## The game state is a value, and that is load-bearing

`GameState` is a frozen dataclass. Nothing changes in place; every
`with_player_at`, `with_ghost_at`, `with_dots`, `with_score`,
`with_outcome` returns a new state.

That is not decoration. Three later requirements are *"this changes
nothing"* requirements — **CTRL-3** (a press towards a wall does nothing at
all), **END-5** (once ended, nothing moves), and **SCORE-3** (an eaten square
scores nothing) — and with a value each of them is asserted in a single line:

```python
self.assertEqual(before, after)
```

rather than by checking the square, then the score, then the dot field, then
the outcome, and hoping nothing was missed. WI-11 and WI-15 both lean on it.

**The order in which the rules of a turn apply is deliberately not here.**
This module offers only atomic moves; the fixed order lives in one named
readable place in WI-11, which is what caution C6 asks for.

## `Score` offers nothing that could lower it

SCORE-5 says the score never goes down. Rather than write that in a comment,
`Score` is a small immutable class whose entire public surface is `points`,
`zero` and `plus_one` — no setter, no `reset`, no bulk add, no subtraction —
and a negative score cannot be constructed at all. A test asserts that
surface is exactly those three names, so that adding a fourth has to be a
deliberate act with a failing test in front of it.

## START-2 is about the straight line, and the two measures really differ

The requirement says the ghost begins on the corridor square furthest from
the player *"measured across the grid rather than along the corridors"*. That
is not a redundant clarification. `tests/domain/test_opening_position.py`
builds a corridor that doubles back:

```
###########
#.........#
#########.#
#.........#
###########
```

From `(1, 3)`, the square furthest **along the corridors** is `(1, 1)` —
eighteen steps round the bend — and it is **two squares away across the
grid**. The furthest across the grid is `(9, 1)`, at a squared distance of
68. The test asserts both facts and then asserts the ghost starts at
`(9, 1)`, so a later change to corridor distance fails loudly rather than
quietly making the game easier.

## Ties, and a consequence worth a ruling

The requirements say *the* nearest square and *the* furthest square, as if
each were unique. On a real 19 × 29 maze neither is, and the ties are not
rare — they are the common case:

| | Measured over 200 generated mazes |
| --- | --- |
| Player start | `(9, 14)` in **115**, `(9, 13)` in **85** |
| Player ties | unique in 115, a two-way tie in 85 |
| Ghost start | `(1, 1)` in **115**, `(1, 27)` in **85** |
| Ghost ties | a **four-way** tie in 115, a two-way tie in 85 |

The middle of the grid falls on a connector square, so when that connector
is wall there are two corridor squares equally near it; and the furthest
square from something near the middle is a tie between corners.

**Ties are broken by taking the first square in row-major order.** It is
deterministic, so the same maze always opens the same way, which WI-19's
scripted game needs.

> **The consequence, stated plainly: the ghost always starts in the
> left-hand column** — top-left or bottom-left, never right. A random
> tie-break would spread it over all four corners, but that means handing
> this module a random source, and WI-6's description pointedly does not,
> where WI-5's and WI-7's both do. **I have not invented the requirement
> either way.** It is measured in `docs/findings/WI-6-start-squares.md`, and
> if it should be random it is a change to `ghost_start_square` and nowhere
> else.

## For the M1 consumers

**WI-12 (frame composer)** and **WI-13 (status line)** both depend on this
item:

- the picture needs `state.player`, `state.ghost`, `state.dots.has_dot(sq)`
  and `state.maze`;
- the status line needs `state.score.points` and `state.outcome`, which is
  `Outcome.UNDECIDED`, `Outcome.CAUGHT` or `Outcome.CLEARED` and nothing
  else — `Outcome` is where *"there is no third ending"* is enforced;
- **the ghost starts standing on a dot** and does not take it (SCORE-4),
  which is asserted here and is the case WI-12's "a dot under the ghost is
  still in the dot field" test composes over.

**A dot count of 259 to 271, mean 264.5**, is what a full game is worth: one
per corridor square less the player's. So the score at a win is a
three-digit number, which is the case WI-13's status line has to fit.

## Tests

`tests/domain/test_dot_field.py`, `tests/domain/test_game_state.py`,
`tests/domain/test_opening_position.py`, and one new shared fixture module.

The start-square rules are checked twice over: on hand-built mazes where the
answer can be worked out by hand and written into the test, and over the 200
generated mazes where the property is asserted against **every other corridor
square** rather than against a number somebody typed.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 221 tests in 3.5s

OK
```

**221 passed, 0 failed, 0 skipped** — 54 of them WI-6's, on top of 167 from
WI-1, WI-3 and WI-5.

**A note on that time.** WI-6's six 200-seed sweeps first took the suite from
3.3 s to **8.5 s**, because each sweep laid out its own 200 mazes. They now
share one set through `tests/domain/generated_mazes.py`, deliberately not
named `test_*` so discovery ignores it, and the suite is **3.46 s with 54
more tests in it than before**. Worth knowing for whoever adds the next
sweep.

## Deviations needing a ruling

- **The ghost's tie-break**, above. The only one that changes what a player
  sees.
- **`Outcome` lives here rather than in WI-11.** The turn resolver sets it,
  but WI-13 (status line) depends on WI-6 and not on WI-11, and it needs to
  know what the endings are called. Putting it here is what lets WI-13 start
  without waiting.
- **`GameState.with_*` helpers** are additive. They are atomic single-field
  replacements only; no rule and no ordering is implied by them.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
