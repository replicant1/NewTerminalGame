# COMPLETION — M2, DEV-A

**Run:** 6 · **Iteration:** M2, *the rules and the picture*
**Lane:** DEV-A · **Work items in this lane this iteration:** WI-11, and nothing else
**Mode:** non-local — real pull requests, merged by the developer

---

## What was finished

**WI-11 — The turn resolver.** Branch `r6/wi-11-turn-resolver`. Pull request
**#39**, merged by DEV-A as `7eb6ff0` once green.

**It was opened as a stacked PR and then unstacked.** WI-11 depends on WI-7,
which was out of draft but not merged when the branch had to be cut, so the
branch was taken from `r6/wi-7-ghost-policy` at `c47f1c4` and the PR opened
`--base r6/wi-7-ghost-policy`. WI-7 merged shortly after; the PR was
retargeted to `main` with `gh pr edit 39 --base main`, `origin/main` merged
onto the branch cleanly, and the whole suite re-run before it was marked
ready. **No merge-order constraint remains.**

| File | What it is |
| --- | --- |
| `terminal_game/domain/turn_resolver.py` | `resolve_move` and `resolve_tick` — the fixed order of the rules of a turn, in one readable place |
| `terminal_game/domain/game_state.py` | gains `ghost_heading: Optional[Direction]` and `with_ghost_heading`, so GHOST-2 has a line to remember |
| `tests/test_turn_resolver.py` | 25 tests, including END-3 asserted directly |
| `docs/prs/PR-WI-11-turn-resolver.md` | the pull request's body |
| `docs/progress/r6-wi-11-turn-resolver.md` | the progress log |

Requirements: **GAME-2**, **CTRL-1**, **CTRL-2**, **CTRL-3**, **SCORE-1**,
**SCORE-2**, **SCORE-3**, **SCORE-4**, **END-1**, **END-2**, **END-3**,
**END-5**.

## How END-3 is held up, since it is the reason this item exists

Two independent things, and neither of them is discipline:

1. **The step order lives in one visible place** (caution C6) — a five-line
   function body with the collision test between the move and the win.
2. **An outcome, once decided, cannot be replaced.** Every ending goes
   through one guard that refuses to overwrite, so a win cannot replace a
   collision decided a moment earlier **even if the two tests were
   reordered**.

The precedence case is asserted directly, together with a second test that
the winning condition really did hold in that same turn — without which the
first could pass for the wrong reason.

**No mutation test was written and no working code was broken to watch a
test go red.** That is prohibited, the technical lead deliberately imposed
no such obligation, and none was invented.

## The state of the test suite as it was left

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 349 tests in 3.8s

OK
```

**349 passed, 0 failed, 0 skipped**, on `main` at `7eb6ff0`. **25 are
WI-11's.** No test opens a window, reads a clock, or reaches for a global
random source.

## The cross-lane exchange, because it worked and is worth recording

DEV-B raised on PR #32 that `GameState` had nowhere to carry the ghost's
heading, which `next_step` returns precisely so it can be carried between
ticks. They recommended putting it in `GameState`, said it was my file, and
did not touch it. **Their recommendation was taken as given**, implemented
here, and answered on PR #33 so the answer sits with their work as well as
mine.

The plan's rule that **DEV-A owns the maze's query surface** was not tested
in the end: DEV-B reported that WI-7 needed no new query, because
`Maze.ways_on` and `Direction.opposite` were already the ghost's questions.
The offer stands for WI-12 and WI-19.

## What the next item in this lane inherits

**WI-15 (the session controller)** gets two functions and no rules of its
own to invent: `resolve_move(state, direction)` for an arrow and
`resolve_tick(state, random_source)` for the clock. Both already refuse to
do anything once `state.is_over`, so END-5's *"the arrow keys do nothing and
the ghost stands still"* costs WI-15 nothing.

**`resolve_move` takes a `Direction`, not an intent**, deliberately — the
Domain names nothing in Presentation. Mapping WI-9's Move intent to a
direction is one line in WI-15.

## One thing wanting a ruling

**On the losing turn, the dot is still eaten and still scores.** The plan's
order is move, collision, eat, win — eat comes *after* the collision rather
than instead of it. Measured: one dot left on the ghost's square, score 6,
the losing move gives outcome `CAUGHT`, **score 7**, dots 0. The other
reading also satisfies END-3 and differs by one point on the `CAUGHT` status
line. Pinned in a test; one line in `resolve_move` if it should be the other
way.

The **ghost's start-square tie-break** from WI-6 is also still with the
user, and unchanged: it was not touched here.
