# M4 — developer A — completion record, and lane A's whole run

**Iteration:** M4, *Seen by a human*. **Lane:** A. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-ad9b18e196f2c349f`.
**Recorded** 17 September 2026, 02:37Z. **Lane A is complete.**

## The suite as I leave it

```sh
.venv/bin/python -m pytest -q
967 passed, 0 failed, 0 skipped, 10 deselected

.venv/bin/python -m pytest -q -m "needs_window or not needs_window"
977 passed, 0 failed, 0 skipped, 0 deselected
```

On `main` at `1580b37`. **Crash reports 14 at the start of my first item and 14 now.**

## Every item, and where it landed

| Item | PR | Merged as |
|---|---|---|
| **S-1** toolkit feasibility | [#72](https://github.com/replicant1/NewTerminalGame/pull/72), [#75](https://github.com/replicant1/NewTerminalGame/pull/75), [#77](https://github.com/replicant1/NewTerminalGame/pull/77) | `5c1d54c`, `c76bc37`, `d033ff4` |
| **WI-3** wall glyph resolution | [#80](https://github.com/replicant1/NewTerminalGame/pull/80), [#82](https://github.com/replicant1/NewTerminalGame/pull/82) | `ead97a7`, `105553b` |
| **WI-4** frame composition | [#84](https://github.com/replicant1/NewTerminalGame/pull/84) | `5850eb4` |
| **WI-4b** the composer produces the surface's field | [#88](https://github.com/replicant1/NewTerminalGame/pull/88) | `d06c71b` |
| **WI-9** the ghost's movement policy | [#86](https://github.com/replicant1/NewTerminalGame/pull/86) | `b3437ca` |
| **WI-11** the session controller | [#91](https://github.com/replicant1/NewTerminalGame/pull/91) | `a356a86` |
| **WI-7** the walking skeleton | [#94](https://github.com/replicant1/NewTerminalGame/pull/94) | `45c86f1` |
| **WI-14** the live game | [#97](https://github.com/replicant1/NewTerminalGame/pull/97) | `da9ec9c` |
| **WI-14b** call the placement WI-15 decided | [#100](https://github.com/replicant1/NewTerminalGame/pull/100) | `a4245a2` |
| **WI-14c** let the anchor reader be injected | [#101](https://github.com/replicant1/NewTerminalGame/pull/101) | `874e0ca` |
| **WI-17** the human-verification pack | [#104](https://github.com/replicant1/NewTerminalGame/pull/104), [#105](https://github.com/replicant1/NewTerminalGame/pull/105) | `4d16e794`, `c57fce3` |
| **WI-20** release readiness | [#107](https://github.com/replicant1/NewTerminalGame/pull/107) | `1580b37` |

All merged by me. No `gh` command was ever refused. **PR #78 was never touched.**

## The findings that outlived their items

- `docs/findings/S-1-tk-headless.md` — Tk 8.5 is testable headlessly; Menlo 16, cell 10 × 19, window 400 × 570. Closed assumption P8 and human item 5.
- `docs/findings/WI-7-box-drawing-ink.md` — the box-drawing glyphs are designed to tile, measured from the font's own outlines because Tk will not talk about ink.
- `docs/findings/WI-17-human-verification.md` — the pack.
- `docs/findings/WI-20-release-readiness.md` — both counts, and the requirement rows a reader will misread.

## Deviation needing a ruling

**Per-iteration completion records were written for M0 and M4 only.** The plan allows one
per lane per iteration; M1, M2 and M3 have none. Items were dispatched continuously across
iteration boundaries rather than in batches, so there was never a moment that read as "the
end of M2" — but that is a reason and not an excuse, and every item does have its PR
summary and progress log. Flagged rather than back-filled, because a record written at the
end of the run and dated to the middle of it would be worth less than its absence.

**WI-20 changed product code**, which its bar did not anticipate: the mandated full run
found a real defect and a release item cannot report green over a red test.

## The four things still open, none of them mine to close

1. **WIN-4** — not met, wired to the fallback. A decision for the user, with a cost.
2. **WIN-5, END-5, END-6** — contradiction C-1. 34 tests pin assumption P1, not the
   requirement.
3. **WIN-2's comfort, WIN-3's titlebar, CTRL-1/2/4/5 by physical key, SCRN-3's
   appearance** — the five human checks.
4. **PR #78** — thirteen rulings, a work item and four structural rules live only there.

## And the thing that matters most

**Nobody has yet seen this game.** It opened on this desktop five times across four of my
items and closed itself in about a second every time, unwatched. **977 tests pass and not
one of them has seen a pixel.** Everything anyone knows about how it looks is inferred
from data structures and font outlines.

## Window hygiene

Four items of mine put real windows on a real person's desktop — WI-7, WI-14, WI-17 and
WI-20, the last with all ten window tests at once. **Crash reports 14 before the first and
14 after the last. No window was ever left behind, no permission dialog was raised, no
modal sheet appeared, and the visible-application list was identical before and after
every run.** One pattern, used five times: window id from the toolkit and never by title,
a watchdog through `after` inside `mainloop`, a belt-and-braces second close, reaping in a
`finally`, a deadline in a parent process rather than in pytest, and the crash-report
directory counted either side because the command output is not a crash detector.
