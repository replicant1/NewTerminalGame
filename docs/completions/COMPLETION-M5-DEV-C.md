# M5 — DEV-C's completion record

**Lane:** DEV-C. **Iteration:** M5. **Work item:** **WI-20b** — the
specification sweep, second landing. **Mode:** non-local, real pull requests.

| | |
| --- | --- |
| Worktree | `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-ad7803d81764149da` |
| Branch | `r6/wi-20b-spec-sweep-final` |
| Based on | `main` at `06da112`, with `origin/main` merged at `03d0913` |
| Pull request | **#68** |
| Suite | `/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"` |
| Result | **815 passed, 0 failed, 0 skipped** (796 on `main` after WI-21 and WI-22a landed, +19) |

---

## What was finished

**`docs/TRACEABILITY.md` is complete.** The same file WI-20a created, written
a second time in place. The *"first of two landings"* notice is gone, section
14's to-do list is gone, and **no row is waiting on a work item** — every work
item of the run has landed, so there is nothing left for a row to wait for.

| File | What it is |
| --- | --- |
| `docs/TRACEABILITY.md` | 49 rows, every one naming its evidence; the two untestable Shell functions declared in a section of their own; 13 open questions each with what a person must do |
| `tests/test_spec_sweep.py` | 21 → 40 tests. The new 19 are about what the finished document **claims**, not about what exists. They caught two real citation drifts during this item alone |
| `docs/prs/PR-WI-20b-spec-sweep-final.md` | the PR body |
| `docs/progress/r6-wi-20b-spec-sweep-final.md` | the log |

## The state of the coverage, as left

**35** pinned outright · **9** caveated by a named assumption · **1** pinned as
formatting only · **3** pinned in part with a half needing a human · **1**
honoured in part with a named gap (CTRL-5) · **0** awaiting a work item ·
**0** with no test and no named human check at all.

**Thirteen things still want a person**, each with what to run and what the
answer would cost, in section 13 of the sweep.

**35 + 9 + 1 + 3 + 1 = 49**, no row counted twice. **17 rows** additionally
observed on a real screen, against 4 at the first landing.

## The five things this landing refused to do

1. **It did not answer any open question.** Eight assumptions, one
   contradiction and three smaller items are recorded as open. Five developers
   in a row declined to convert a measurement into an answer; this is the sixth
   refusal and there are now tests that keep it from being undone quietly.
2. **It did not close SCRN-3 / A10.** Uniform advance widths settle the spacing
   and say nothing about whether the strokes meet.
3. **It did not tick CTRL-5.** A modified arrow moves the player, deliberately.
4. **It did not claim test coverage for the two Shell functions no test can
   reach.** They are declared as *covered by observation, not by test*.
5. **It did not run the finished game.** Section 4 rule 5. No window was opened
   by this item and none was needed.

## Deviations needing a ruling

1. **SCRN-5 carried as open** — additive; declared in
   `docs/findings/WI-16-the-look.md` §4 and not carried by the first landing.
2. **END-3 recounted as caveated by A8** — changes the published count from 8
   to 9 caveated; no code, no test, no claim about behaviour.
3. **WI-21's findings document cited by its own name**,
   `WI-21-the-five-questions.md`, not the plan's `WI-21-human-answers.md`.
   Asked WI-21 directly on PR #66 rather than guessing; it confirmed that is
   the one and only file it would add.
4. **Section 13 gained two columns** — *what a person does*, *what the answer
   costs*.
5. **A category added to the legend** — *covered by observation, not by test*,
   from amendment 9, which postdates WI-20a.

## Contradictions found

**None new.** C-1 to C-7 are all recorded and all still true as written. This
item re-derived none of them.

## One relayed correction that did not survive checking

The conductor relayed that WI-21's second window *"reached phase `ended` with
nothing pressed"*, as a correction to *"nobody has played a whole game"*, and
told me to check rather than take it as final. **I checked and the original row
stands.** `ended` is the session's phase — the harness's own scheduled `quit` —
not a game outcome; WI-21 records **zero dots eaten** on each of its six
windows and says in its §8 that nobody has ever played a game to an ending. The
sweep now states the distinction explicitly, because it is exactly the sort of
thing that gets rounded up on a second reading.

## The screen

**Zero windows opened by this lane, for this item.** None was needed and the
screen gate was never requested. Every claim about a real screen is cited from
the thirteen findings. The run's final ledger, unchanged by this lane:
**39 windows opened, 39 reaped, no modal sheet ever raised.**
