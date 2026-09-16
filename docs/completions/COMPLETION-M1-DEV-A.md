# COMPLETION — M1, DEV-A

**Run:** 6 · **Iteration:** M1, *the pieces of the game*
**Lane:** DEV-A · **Work items in this lane this iteration:** WI-6, and nothing else
**Mode:** non-local — real pull requests, merged by the developer

---

## What was finished

**WI-6 — The opening position.** Branch `r6/wi-6-opening-position`, cut from
`main` at `d07a5f7`. Pull request **#32**, opened as a draft on the first
commit and merged by DEV-A as `edcb5a3` once green.

Started early, at the conductor's instruction, rather than at the M0/M1
boundary, because DEV-A holds the whole critical path.

| File | What it is |
| --- | --- |
| `terminal_game/domain/dot_field.py` | `DotField` — which corridor squares still hold a dot; taking one takes it for good (START-3, SCORE-1, SCORE-3) |
| `terminal_game/domain/game_state.py` | `Score` (START-4, SCORE-5), `Outcome` (GAME-2), `GameState` — a value, so that "this rule changed nothing" is one assertion |
| `terminal_game/domain/opening_position.py` | `player_start_square` (START-1), `ghost_start_square` (START-2), `opening_position` |
| `tests/test_dot_field.py` | the dots, and that taking twice takes once |
| `tests/test_game_state.py` | score, outcome, and that every `with_` changes one thing |
| `tests/test_opening_position.py` | the start squares, by hand and over 200 generated mazes |
| `tests/generated_mazes.py` | the 200 seeded mazes, shared by every sweep; not named `test_*` |
| `docs/findings/WI-6-start-squares.md` | where the two actors actually start, measured |
| `docs/prs/PR-WI-6-opening-position.md` | the pull request's body |
| `docs/progress/r6-wi-6-opening-position.md` | the progress log |

Requirements this item is responsible for: **START-1** (nearest the middle),
**START-2** (furthest by straight-line grid distance), **START-3** (a dot
everywhere but the player's square), **START-4** (score zero). It also lands
the vocabulary for **SCORE-1**, **SCORE-3**, **SCORE-5**, **GAME-1** and
**GAME-2**; the rules that use it are WI-11's.

## The state of the test suite as it was left

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 282 tests in 3.6s

OK
```

**282 passed, 0 failed, 0 skipped**, on `main` at `edcb5a3` with WI-1, WI-2,
WI-3, WI-5 and WI-6 all in it. **54 are WI-6's.** No test opens a window,
reads a clock, or reaches for a global random source.

## Measurements worth carrying forward

In `docs/findings/WI-6-start-squares.md`:

- **the ghost always starts in the left-hand column** — `(1, 1)` in 115 of
  200 mazes and `(1, 27)` in the other 85, because the furthest square from
  the middle is always a tie between corners and the tie is broken in
  row-major order. **This is the one thing in WI-6 that wants a ruling**;
- the player starts at `(9, 14)` in 115 and `(9, 13)` in 85, because the
  exact middle of the grid is a connector square that is corridor only when
  the two cells either side of it happen to be joined;
- **a full game is worth 259 to 271 points, mean 264.5**, which WI-13 and
  WI-19 both need;
- the suite's 200-seed sweeps now share one set of mazes; six independent
  sweeps had taken the suite from 3.3 s to 8.5 s.

## What the next item in this lane inherits

**WI-11 (the turn resolver)** has the whole vocabulary and none of the rules,
which is deliberate: the fixed step order belongs in one named readable place
(caution C6), and nothing in WI-6 pre-empts it. It gets atomic
`with_player_at`, `with_ghost_at`, `with_dots`, `with_score`,
`with_outcome`; `state.actors_share_a_square` for END-1's condition;
`state.dots.is_empty` for END-2's; and `GameState` equality, so *"a move into
a wall changes nothing at all"* is asserted as `assertEqual(before, after)`.

**The maze's query surface is still DEV-A's**, and WI-7 and WI-8 are the
items that may want to add to it. Nobody has asked yet.

## Nothing is left open in this lane

No `ASK` was raised and nothing in WI-6 needs a human to look at a screen.
The one thing that needs a **decision** — the ghost's tie-break — is measured
and written down, and the change is confined to one function if it goes the
other way.
