# WI-6 — Player movement, dots, score, and the endings the player's move decides

**Branch** `wi-6-player-dots-endings`, cut from `main` (`4d88d47`, the WI-8 merge).
**Base** `main`. **Iteration** M1, Dev A, round 4.

## What this adds

One function, in the module WI-5 already started:

- `termgame/rules.py` — `move_player(state, direction) -> GameState`, the total
  pure transition for one arrow-key press.
- `tests/test_rules_player.py` — its tests, every board hand-written and small.

Nothing else is touched. The loop still calls `termgame.standins.move_player`;
wiring the real one in is WI-9's job, not this item's, so `loop.py`,
`standins.py` and their tests are left exactly as they were.

## The shape of the transition

```
move_player(state, direction):
    outcome is not PLAYING   -> return state              END-5
    target is wall/off-grid  -> return state              CTRL-3
    dot on target            -> dots - {target}, score+1  SCORE-1, SCORE-2
    no dot                   -> dots, score unchanged     SCORE-3
    target == ghost          -> CAUGHT                    END-1
    elif no dots left        -> CLEARED                   END-2
    else                     -> PLAYING
```

Two details that are requirements rather than style:

- **Both "nothing happens" cases return the identical object**, not a fresh
  `GameState` that compares equal. CTRL-3's own words are "nothing at all", and
  the tests assert `is`, so a future refactor that rebuilds the state cannot slip
  past as "equal anyway".
- **One square, then return.** There is no loop in the function and no repeat or
  momentum state anywhere in `GameState` for a caller to wind up, which is CTRL-2
  in full.

## END-3 — the requirement flagged as fragile (plan §2.7)

END-3 is correct only because `if target == state.ghost` is evaluated before
`elif not dots`. Swap the two and the game silently *wins* the position the
specification bothers to disambiguate, on a board rare enough that no ordinary
play would show it.

Three things guard it:

1. The two branches are adjacent, in that order, with a comment above them saying
   the order is the requirement and not to reorder them.
2. The module docstring states END-3 as an ordering rather than a special case.
3. **A named test:**
   `test_END_3_eating_the_last_dot_on_the_ghosts_square_is_a_loss_not_a_win`,
   in class `EndThreeTheOrderOfTwoBranches`, with the requirement quoted in its
   docstring and a comment saying it must not be deleted. A board with exactly
   one dot left, that dot on the ghost's square, the player one step away; the
   result is `CAUGHT`.

A companion test in the same class runs the same board with the ghost moved out
of the way and gets `CLEARED`, so the pair pins that the ghost is what decides it
and that the losing board really is one where the win branch would otherwise
fire — the dot *is* eaten, the score *does* go up, and `dots` *is* empty.

Per plan §2.7 and the conductor's dispatch, no mutation check was run on this:
the user has decided that is not part of this workflow. Report section 5 reads
"not applicable".

## What the tests establish

`tests/test_rules_player.py`, 36 tests, one class per group of requirements:

| Class | Requirements | What it pins |
|---|---|---|
| `TheBoardHelper` | — | the pictures really do say what their comments say |
| `TheMoveItself` | CTRL-1, CTRL-2 | all four directions; one square per press; five presses land on the fifth square and the sixth (into a wall) changes nothing; the ghost and its heading are untouched; the state handed in is not mutated; totality over every square of a board |
| `APressTowardsAWall` | CTRL-3 | the identical object comes back, no field changes, the score in particular does not, off-the-grid presses behave the same, and a wall press between two real moves loses nothing |
| `DotsAndTheScore` | SCORE-1, SCORE-2, SCORE-3, SCORE-5 | the dot is eaten and scores exactly one, the other dots stay put, the eaten dot is gone for good, re-entering scores nothing, a seven-dot lap scores seven, and the score is non-decreasing at every step of a two-lap scripted run |
| `HowAGameEnds` | END-1, END-2, GAME-2 | walking onto the ghost loses with dots still on the board; the last dot on an empty square wins; two dots left wins nothing; and both endings are reached off one board by two different routes |
| `EndThreeTheOrderOfTwoBranches` | END-3 | see above — four tests, including the named one |
| `AfterTheGameHasEnded` | END-5 | after a loss and after a win, every direction returns the identical object; the helper first asserts the player's square has an open way out, so the test cannot pass vacuously |

## Suite

From the worktree root:

```
/usr/bin/python3 -m unittest discover -s tests
Ran 515 tests in 10.278s
OK (skipped=2)
```

`main` was at `Ran 479 tests … OK (skipped=2)` at the branch point; 36 of the
515 are new and the two skips are the pre-existing ones. WI-1's AST purity guard
covers `rules.py` automatically and did not fire.

## Notes for the merge

- **WI-7 shares this module.** Dev B is adding the ghost transition to
  `termgame/rules.py` in the same round. This item adds only `move_player`, its
  entry in `__all__`, and a "the player's move" section to the module docstring;
  it changes none of WI-5's existing functions. A WI-7 conflict should be
  confined to `__all__` and the docstring and should be mechanical. No shared
  helper for "is this corridor" or "which neighbours are open" was added — WI-1's
  maze value answers both (`is_wall`, `open_directions`), and nothing else was
  needed in common.
- `orchestration/static/index.html` is **not** in this diff. `git diff --stat
  origin/main...HEAD` lists exactly four files: `termgame/rules.py`,
  `tests/test_rules_player.py`, this summary and the progress log. The user's own
  unpushed work under `orchestration/` has been left completely alone.

## Deviations and open points

- **No deviations from the plan's WI-6 brief.** Everything in its "Tests must
  establish" list is covered, and nothing outside the item was touched.
- **Additive, and worth a ruling if you disagree:** the tests include a few
  assertions the brief does not ask for — totality over every square of a board,
  a purity check that the state handed in is not mutated, and the board-helper
  tests. They are cheap and they are the kind of thing a later refactor breaks
  first; say the word and they come out.
- **No contradictions found** between the plan, the architecture and the
  requirements for this item. The architecture's §5.4 pseudocode for
  `move_player` and the plan's §5 prose agree with each other and with FR
  CTRL-1..3 / SCORE-1..3,5 / END-1..3,5 / GAME-2, and the implementation follows
  the pseudocode branch for branch.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
