# PR-MONITOR — the progress bar read 0 of 25 for a finished project

Risk: MEDIUM — no application code, but this is the instrument the run is watched through,
and a monitor that misreports is worse than one that says nothing.

Three defects in `orchestration/server.py` and one in the page it serves, plus tests. Tooling, not process: no work item, no
plan amendment, nothing in `docs/IMPLEMENTATION_PLAN.md` changes.

## Why

`server.py:225` gave every stamped log line **today's** date:

```python
today = datetime.datetime.now(datetime.timezone.utc).date()
entry["ts"] = datetime.datetime(today.year, today.month, today.day, h, mi, sec, ...)
```

An agent writes `HH:MM:SSZ` and no date, so something has to supply one — and *today* is right
only for a log being appended right now. It is wrong silently for every other one, because a
time is still a time either way.

That is not cosmetic, because three things are chained to it:

1. `run_clock()` takes the run's start from the conductor's `START` line.
2. `progress()` passes that to `git log --since` and counts a work item done only if its merge
   is reachable from the trunk inside that window.
3. Dated to today, run 7's `START` at `01:25:23Z` became **this morning**.

All 25 work items merged on 17 September, so every one fell outside the window. A finished
project reported **`0 of 25`**, with `S-1`, `S-2` and `WI-0` listed as what to do next.

**And it was structural rather than unlucky.** Since every stamp becomes today, the run start
is *always* today — so for any project whose work landed on an earlier day the bar can only
ever read zero. It could only count items merged today, after the conductor's start time.

The README already knows stamps land on today. It says so about the **timeline**, and judges
it not worth fixing there. Nobody noticed the same fact silently zeroed the bar.

## What changed

`date_stamped()` anchors the **last** stamped line to the file's mtime and walks backwards,
stepping the date back a day each time a stamp runs forwards as it goes — which is what
crossing a midnight looks like from the end.

The anchor is sound on the one real log available: run 7's last line reads `02:38:54Z`, the
file's mtime is 12:38 local, and `02:38:54Z` **is** 12:38 local. They agree to the minute.

**A live log still lands on today**, because its mtime is now. The old behaviour survives
exactly where it was right.

The `--since` scoping itself is untouched. The comment above it records why it exists: branch
names are reused across runs, and matching on item code alone once marked five unstarted items
done, two of them dispatched minutes earlier.

## Scrutiny

- `orchestration/server.py`, `date_stamped()` — the backwards walk, and **`MIDNIGHT_JUMP_S`**.
  An earlier draft assumed stamps within a file are non-decreasing except at midnight; they are
  not, and that assumption dated two lines of `r7-s-2-anchor-window.md` a day early. It also
  named `test_stamps_stay_in_order_across_that_boundary` as the guard, which could not fail for
  any input — stepping the day back on every forward jump makes the output sorted by
  construction.

  **Why twelve hours, since a bare constant explains nothing.** The rule reduces to *the mod-24
  forward gap between consecutive lines exceeds twelve hours*, which picks the nearer of the two
  possible readings of an undated gap. Twelve is the only midpoint; any other value is worse in
  one direction. Measured over every log in `docs/progress`:

  | | |
  | --- | --- |
  | largest backwards inversion anywhere | **12s** — the case that found this |
  | largest real gap between consecutive lines | **4951s (83 min)** |
  | threshold | **43200s** |
  | margin against noise | ~3600× |
  | margin against real gaps | ~9× |

  `progress-tracking.md` — *"Never go more than a few minutes without a line"* — is what makes
  the upper margin hold. **The log that would defeat it** is a genuine crossing with twelve
  hours of silence between consecutive lines: a run paused overnight. In that case the result is
  the behaviour this change replaced, so it is never worse than before, and no threshold can do
  better with only a time of day to go on.
- **mtime is the load-bearing assumption.** A log copied or touched carries a wrong mtime and
  would date wrongly — still better than *today*, but wrong. Worth deciding if that is
  acceptable.
- `tests/test_monitor_run_clock.py` — these assert which **day** a line lands on, not that a
  function was called. The out-of-order test reads `r7-s-2-anchor-window.md` **from the tree**
  rather than a fixture, and asserts a count of distinct days — so it is independent of the
  mtime git rewrites on checkout, and it fails on the code this PR replaces.

## Result

Against the same data, before and after:

```
before   run start 2026-09-21T11:25:23   "0 of 25 work items merged"    next: S-1, S-2, WI-0
after    run start 2026-09-17T11:25:23   "24 of 25 work items merged"   next: WI-19
```

**One observation, not a claim:** the remaining item is WI-19, and no `r7/wi-19-*` branch has
ever existed on the remote — so 24 of 25 may be true rather than a second defect. The
conductor's own `DONE` line says 25 landed. Somebody who knows what WI-19 became should say
which is right; this PR does not decide it.

## A second defect, found by the first one's cleanup

Removing thirteen stale agent worktrees did not reduce the monitor's tab count. The monitor
archives a removed worktree's `docs/progress` so that its record survives the worktree — which
is right — but it archives the **whole directory**: thirty files, every log the repository
already tracks, not just the one that agent wrote.

Two things followed, and both were visible on screen:

- **Every archived pane was titled `technical-lead`**, because the title is `logs[-1].stem` and
  `technical-lead.md` sorts last in all of them.
- **Each pane merged all thirty logs**, so one archived agent's tab carried every other agent's
  lines — 260 of them, for an agent that had written eight.

The agent's own log is the one it was still writing when the worktree went, so it is the
newest; the rest arrived with the checkout. Taking `max(logs, key=mtime)` fixes the title and
the mixing together.

```
before   technical-lead  (×13)                        260 lines each
after    code-reviewer-r7-amend-2-code-reviewer       18
         r7-wi-18-coverage-audit                      14
         code-reviewer-r7-amend-4-review-followups     9   …
```

One pane still reads `technical-lead`: an archived worktree that was never dirty and so wrote
no log of its own. The heuristic has nothing better to offer there, and it is honest about it.

## A third: the clock never stopped

The header read **`run elapsed 100h`**. `run_clock()` returned a start and no end, so the page
counted from it to *now* — and 17 September 01:25:23Z to today is 100.4 hours. That is how long
**ago** the run was, printed under a label that says how long it **took**.

A conductor's `DONE` is the run ending, so the clock now stops there and the header reads
`run took 1h 13m 31s · finished`.

**What run 7 actually took: 1:13:31**, and three independent sources agree.

- The conductor's own log: `START 01:25:23Z` → `DONE 02:38:54Z`.
- Every other agent's log falls inside that window — earliest line 01:27:03Z (the technical
  lead), latest 02:32:36Z.
- Git: 158 of the 168 commits made that day sit inside it. The first is the technical lead's
  `PLAN: adopt candidate 2` at 01:33:08Z, eight minutes after `START`; the last is WI-20's
  merge at 02:37:45Z, sixty-nine seconds before `DONE`.

## Two more, from Copilot

**An unstamped tail can drag the anchor past midnight.** `parse_log` keeps unstamped lines —
prose, a continuation, a note appended without reading the clock — and one written after the
final stamp carries the file's mtime forward with it. If that tail crossed a midnight, the
anchor sits a day ahead of the stamp it is pinning, and every stamped line is dated a day late.

A stamp cannot have been written after the file was, so a last stamp landing *ahead* of the
mtime is a stamp from the day before. A minute of slack absorbs the gap between reading the
clock and the write landing; a real crossing is hours.

**And nothing called `run_clock()`.** The tests parsed a `DONE` line; none of them asked
`run_clock` what it made of one — so a renamed field, an early `break` or an unset flag would
have passed the entire suite while the header went back to counting to now. Four tests with the
panes stubbed now pin it: a `DONE` freezes the clock, a live run has no end, the last `DONE`
wins, and a *developer's* `DONE` does not end a run.

## Suite

`.venv/bin/python -m pytest -q` → **1017 passed, 12 deselected**, with 18 tests in
`tests/test_monitor_run_clock.py`. No application code is touched.
