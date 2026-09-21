# PR-MONITOR — the progress bar read 0 of 25 for a finished project

Risk: MEDIUM — no application code, but this is the instrument the run is watched through,
and a monitor that misreports is worse than one that says nothing.

Two functions in `orchestration/server.py`, plus tests. Tooling, not process: no work item, no
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

- `orchestration/server.py`, `date_stamped()` — the backwards walk. It assumes stamps within a
  file are non-decreasing except at midnight. A log written out of order would be mis-dated,
  and `test_stamps_stay_in_order_across_that_boundary` is the guard.
- **mtime is the load-bearing assumption.** A log copied or touched carries a wrong mtime and
  would date wrongly — still better than *today*, but wrong. Worth deciding if that is
  acceptable.
- `tests/test_monitor_run_clock.py` — these assert which **day** a line lands on, not that a
  function was called.

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

## Suite

`.venv/bin/python -m pytest -q` → **994 passed, 10 deselected**, up from 986 by the 8 tests
here. No application code is touched.
