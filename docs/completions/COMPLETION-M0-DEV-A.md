# M0 — developer A — completion record

**Iteration:** M0, *Ground to stand on*.
**Lane:** A. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-ad9b18e196f2c349f`.
**Recorded** 17 Sep 2026, 01:42Z.

## What was finished

**S-1 — toolkit feasibility.** Lane A's other M0 item, **WI-3 (wall glyph resolution)**,
was dispatched to me as this record was being written; it is not covered here and **this
document will be extended in WI-3's own pull request** rather than duplicated, since the
plan allows one completion record per lane per iteration.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#72](https://github.com/replicant1/NewTerminalGame/pull/72) | S-1: toolkit feasibility — Tk 8.5 is testable headlessly; Menlo 16 is the cell grid | `main` | `5c1d54c` |
| [#75](https://github.com/replicant1/NewTerminalGame/pull/75) | S-1: progress log tail — merge record and post-merge suite count | `main` | `c76bc37` |

Both merged by me. Branch `r7/s-1-tk-feasibility`, cut from `main` at `4015c96`.

**Files added:**

- `docs/findings/S-1-tk-headless.md` — the verdict and every number behind it.
- `docs/prs/PR-S-1-tk-feasibility.md`, `docs/prs/PR-S-1-progress-log-tail.md`.
- `docs/progress/r7-s-1-tk-feasibility.md`.

## The verdict

> **Yes — the Presentation layer can be tested headlessly on Tcl/Tk 8.5.**
> **Assumption P8 holds in both halves.** WI-5, WI-6, WI-7, WI-14 and WI-16 proceed as
> written, and **human item 5 of section 9 does not open.** Nothing was installed.

**Recommended:** **Menlo, size 16 — cell 10 × 19 px, so a 40 × 30 window is 400 × 570 px.**
16 is the largest Menlo size at which a 40-column row laid out per cell and the same row
drawn as one string land on identical pixels, which is why it is the recommendation.

## State of the test suite as I left it

```
.venv/bin/python -m pytest -q      # from the repository root
56 passed in 0.06s
```

**56 passed, 0 failed, 0 skipped, nothing deselected**, on `r7/s-1-tk-feasibility` at
`c76bc37`, which is `origin/main`. All 56 are WI-0's; **S-1 added none** — see the
deviation below.

At the moment PR #72 itself merged the count was **0 passed, 0 failed, 0 skipped**, because
no suite existed: WI-0 had not landed and `.venv/bin/python` did not exist.

## Deviation needing a ruling

**S-1 committed no test, although its bar in plan section 5 says one should exist if the
conclusions can be pinned headlessly — and they can.** WI-0 was creating the package layout
in parallel; a test written here would have guessed at it and raced it. **The conductor
ruled it be left to WI-5.** The four assertions WI-5 should write, including the control
that stops the substitution check passing vacuously, are set out in section 7 of the
finding.

## Two things for a human

1. **A "Python" tile appears in the Dock whenever a Tk root is built**, including in a
   headless test run. Not a window, never takes focus, but visible and nobody agreed to it.
   Steps and what a good answer looks like are in section 5 of the finding.
2. **Whether Menlo's box-drawing ink spans the full cell** — so a run of `═` reads as one
   unbroken double line — could not be measured. Only *advance* was measurable. The first
   chance to see it is WI-7's window; WI-17 should put it in front of a person.

## Window hygiene

No Terminal window was opened, so none needed reaping. No window was ever mapped. Every
probe carried a `SIGALRM` hard deadline, contained no `mainloop`, and could not block. No
permission dialog was raised; `/usr/bin/lsappinfo`, which needs none, was the only thing
that touched the desktop.
