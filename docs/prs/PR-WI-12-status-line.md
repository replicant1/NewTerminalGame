# WI-12 — the status line

Row 29: the exact content, in cyan, and nothing else on that row. Plan section 5,
iteration M2, lane C. Depends on WI-8, merged.

## What is here

| File | |
|---|---|
| `terminal_game/presentation/status.py` | `status_text(outcome, score)` and `status_for(state)` — the whole of row 29, plus the row index and the colour |
| `tests/test_status.py` | 83 tests |

Pure Presentation: no toolkit, no clock. It reads WI-8's `Outcome` vocabulary and produces
a string.

## The interface, as I gave it to lane A

**WI-12 produces the whole row-29 string — including ruling C-4's leading space — and hands
it with `palette.STATUS`. The composer does `field.write(0, STATUS_ROW, text,
STATUS_COLOUR)` and decides nothing.** That satisfies the lead's constraint exactly: every
character of row 29 is composed here and nowhere else, and the write is mechanical.

`STATUS_ROW` is `ROWS - 1`, derived rather than typed, and `STATUS_COLOUR` is re-exported
so a caller asks this module for everything about the row, colour included.

## `status_for(state)` — asking the function, never the field

The conductor warned, while this was open, that `GameState.outcome` is a **stale cache**
and everything must ask `turn.outcome_of(state)` instead. `status_text` was already immune,
because it takes the outcome as a *parameter* and never touches a `GameState` — but the
trap simply moves to whoever calls it.

So there is now **`status_for(state)`, which asks `outcome_of` itself**. That makes the
right thing the easy thing rather than a rule someone has to remember, and it is legal:
plan 1.3 lets Presentation import Application.

**The test that matters is the one lane A's failure mode describes.** A hand-built board
with both actors on one square and the stored field left at `UNDECIDED`:

- `state.outcome is Outcome.UNDECIDED` — the stale stamp
- `outcome_of(state) is Outcome.CAUGHT` — the truth
- `status_for(state)` renders the **caught** form, with no arrows

and the converse too — a playable board stamped `CAUGHT` renders the *playing* form — so
the test is not passing merely because "decided wins". `status_text` still takes an outcome
directly, because a test that wants a particular form should be able to say so without
building a state that produces it.

## C-4 is confirmed by measurement, and then refined

**Confirmed.** I parsed the specimen out of `docs/FUNCTIONAL_REQUIREMENTS.md` rather than
trusting the ruling: the bottom row is `' score 0    arrows, q quits'` — 27 characters, one
leading space, and exactly `" " + <the STAT-2 literal>`. A test re-reads it on every run, so
the literals here cannot drift from the document they came from.

**Refined, and this is the deviation that needs a ruling.** C-4 says the three literals
"pad differently from one another … so there is no column discipline to infer". **There is
one, and the specification's own three examples determine it uniquely: the score sits
left-aligned in a field of 5 characters.**

| Form | Built as | Printed in the spec as |
|---|---|---|
| playing, 0 | `score ` + `0␣␣␣␣` | `score 0    arrows, q quits` |
| caught, 37 | `CAUGHT␣␣score ` + `37␣␣␣` | `CAUGHT  score 37   q quits` |
| cleared, 274 | `CLEARED␣␣score ` + `274␣␣` | `CLEARED  score 274  q quits` |

**Width 5 reproduces all three verbatim. Width 4 and width 6 reproduce none.** The
apparently inconsistent gap that C-4 noticed — `q quits` at column 19 in the caught form
and 20 in the cleared — comes entirely from `CAUGHT` being one character shorter than
`CLEARED`, not from the padding.

**Why I chose it over the literal reading.** Fixed separators copied out of each example
also reproduce all three, because the two readings differ only at score widths the
specification never prints. But **STAT-2 says the score is kept up to date**: with a fixed
separator, `arrows, q quits` slides right every time the score crosses a power of ten, and
the player watches it happen all game. With the field it stays at column 12 for every score
from 0 to the 551 dots a 19 × 29 grid can hold — and there is a test that says so.

**If the literal reading is preferred it is one constant and the tests that quote it.** Both
readings pass the three verbatim tests, which are the ones that matter most.

## What the tests establish

- **STAT-2, STAT-3 as exact strings** — all three printed examples, verbatim, and again as
  "the requirement's own text with one leading space".
- **Against the specimen itself**, read from the requirements document at run time.
- **STAT-2 at nine scores** from 0 to 551, including that the tail does not move.
- **STAT-3 says which ending happened** — a loss never reads as a win, a win never as a
  loss, and both drop the arrows, which the requirement's own text does because the arrows
  do nothing once the game is decided (END-5) and only `q` is left (END-6).
- **STAT-1** — the row written reads back as the status and then blank, and nothing of it
  lands on any other row. Every form at the highest reachable score still fits in 40.
- **SCRN-6** — every cell of the written row is cyan.
- **The vocabulary is whole** — three outcomes, three forms, and a fourth is a `TypeError`.
- **SCORE-5** — a negative score is refused, and so is `True`, because `bool` is an `int`
  in Python and `score True` would otherwise render as `score 1`.

## Suite state

```
.venv/bin/python -m pytest -q          →  788 passed, 0 failed, 0 skipped, 2 deselected
```

Run from the repository root, `.venv` from `/usr/bin/python3` 3.9.6 with pytest 8.4.2.
Run after `git merge origin/main` (`2599b1a`, which brought WI-11 and WI-13) — no conflict. Baseline when this branch was cut from `ea00019` was **586**; WI-12 adds **83** and the merge brought the rest. The layer
rule sees `terminal_game.presentation.status` and reports no violations. No window is
opened by any of this; `lsappinfo visibleApplicationCount` 7 before and after, and no new
crash reports.

## What needs a human

Nothing new from WI-12. **Human item 6 is now cheaper to answer**, if the user cares: ruling
C-4's leading space is pinned by three assertions plus a live comparison against the
specimen, so flipping it is one constant. And the score-field refinement above is a
question for the technical lead rather than the user.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
