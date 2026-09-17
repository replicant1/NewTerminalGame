# M2 — developer C — completion record

**Iteration:** M2, *The rules, and the window in its place*.
**Lane:** C. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-a319e57ac3a444133`.
**Recorded** 17 Sep 2026, 02:30Z.

## What was finished

**WI-12 — the status line**, and **WI-12b — row 29 as cells**, an item dispatched off the
back of a gap I found while reading ahead. Lane C's other M2 item, **WI-15 (where the
window lands)**, was **moved to lane B** under the lead's standing instruction to shed from
lane C rather than add to it. It is not recorded here.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#93](https://github.com/replicant1/NewTerminalGame/pull/93) | WI-12: the status line | `main` | `54a32cf` |
| [#96](https://github.com/replicant1/NewTerminalGame/pull/96) | WI-12b: row 29 as cells | `main` | `dc6fce3` |

Both merged by me. Neither branch conflicted.

**Files added:** `terminal_game/presentation/status.py`, `tests/test_status.py` (94 tests),
the two PR summaries and the two progress logs.

## Ruling C-4 confirmed, then refined

**Confirmed by measurement rather than trust.** I parsed the specimen out of
`docs/FUNCTIONAL_REQUIREMENTS.md`: the bottom row is `' score 0    arrows, q quits'` — 27
characters, one leading space, exactly `" " + <the STAT-2 literal>`. A test re-reads it from
the document on every run, so the literals cannot drift from their source.

**Refined.** C-4 says the three literals *"pad differently from one another … so there is no
column discipline to infer"*. **There is one, and the specification's own three examples
determine it uniquely: the score sits left-aligned in a field of 5.** Width 5 reproduces all
three verbatim; widths 4 and 6 reproduce none. The apparently inconsistent gap — `q quits`
at column 19 in the caught form and 20 in the cleared — comes entirely from `CAUGHT` being
one character shorter than `CLEARED`.

**Chosen over the literal fixed-separator reading** because STAT-2 keeps the score up to
date all game: with fixed separators `arrows, q quits` slides right every time the score
crosses a power of ten and the player watches it happen. With the field it stays at column
12 from 0 to the 551 dots the grid can hold. **Both readings pass the three verbatim tests**,
so this is one constant if the literal reading is preferred. The lead re-ran the claim and
confirmed it.

## Two affordances rather than two rules

**`status_for(state)`** asks `turn.outcome_of` and never reads `GameState.outcome`.
`status_text` was already immune — it takes the outcome as a parameter — but the trap moves
to the caller, so the right thing is now the easy thing. Pinned by a board with both actors
on one square and the field left at `UNDECIDED`, and by its converse so it is not passing
merely because "decided wins".

**`status_cells(outcome, score)`** — WI-12b. `compose_frame` took exactly 40 `Cell`s,
`status_text` returned a `str`, and **nothing bridged them**, so WI-14 would have had to pad
row 29 itself — and padding row 29 *is* composing part of row 29, which the lead ruled must
happen nowhere but WI-12. Found by reading ahead between items; closed inside my own module
so no lane A code was touched and the text-and-colour signature stayed open.

## Suite state

```
.venv/bin/python -m pytest -q          →  788 passed  (WI-12, on 54a32cf)
.venv/bin/python -m pytest -q          →  868 passed  (WI-12b, on dc6fce3)
```

Both 0 failed, 0 skipped. **WI-12 adds 83 and WI-12b adds 11.** No window is opened by any
of it.
