# Integrating the queue that built up behind the merge lockout

**Date:** 2026-09-14 · **Integrated by:** the user's Claude Code session, from the
primary working tree · **Base:** `c4171fb` → **Result:** `8d7eeca`

## Why this was not done by the technical lead

In local mode the technical lead merges. It could not. The harness placed both
the technical lead and the conductor inside developer worktrees, and `main` is
checked out in the primary tree, so git refused to let either reach it. Neither
routed around the refusal, which is what their instructions require; the queue
therefore grew until somebody with access to the primary tree acted.

`main` did not move from `c4171fb` while nine branches accumulated, every one of
them measured and green against its own base, none blocked on a decision.

## The risk this carried, and how it was handled

The technical lead's warning, recorded before the queue landed:

> WHEN THE QUEUE LANDS IT WILL BE MERGING EIGHT BRANCHES INTO A `main` NOBODY HAS
> EVER RUN THE SUITE AGAINST IN THAT COMBINATION.

Each branch had been measured against its own parent, or against a stacked
approximation of the others — not against the combination. So the queue was
merged the way the plan prescribes for a single work item: **one branch at a
time, in plan order, `--no-ff`, with the full suite run after every merge and a
hard stop at the first red or the first conflict.**

No branch conflicted. No merge turned the suite red. Had either happened, the
merge would have been reset and the queue halted rather than resolved here:
nobody resolves a conflict in code they did not write.

## What was integrated, in order

| # | Branch | Tests after | Commit |
|---|---|---|---|
| 1 | `m0-dev-b-completion` | 256 | `6bd54ab` |
| 2 | `wi-3-end-to-end-join` | 303 | `679a629` |
| 3 | `wi-7-game-state` | 356 | `c708a39` |
| 4 | `wi-5a-wall-glyphs` | 399 | `89e5d0a` |
| 5 | `wi-8-player-move` | 429 | `6694d56` |
| 6 | `wi-9-ghost-policy` | 464 | `ee0b954` |
| 7 | `wi-10-rules-outcome` | 496 | `80db293` |
| 8 | `wi-6-status-line` | 525 | `2289933` |
| 9 | `wi-5b-frame-composition` | 575 | `8d7eeca` |

Suite command: `/usr/bin/python3 -m unittest discover` from the repo root, the
command the plan pins. Baseline at `c4171fb` was 256 passing; the final tree is
**575 passing, 0 failed, 0 skipped**.

## Not integrated

`wi-11-game-loop` was left alone. It is dispatched and still being worked on —
its most recent commit is its developer merging `main` in as branches landed, not
a completion. It is the developer's to finish and report.

## What this does not settle

The lockout itself is unfixed. The next merge round will hit it again unless the
technical lead can be given the primary working tree, because the reason local
mode assigns merging to the technical lead — that developers in worktrees cannot
check out `main` — applies equally to a technical lead that is also in a worktree.
`developer.md` declares `isolation: worktree`; `technical-lead.md` declares
nothing, and got one anyway.
