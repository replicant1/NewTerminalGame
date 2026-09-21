# r7/monitor-run-clock

05:34:00Z  START   the orchestration monitor's progress bar reads 0 of 25 for a finished project
05:34:00Z  READ    orchestration/server.py -- parse_log, run_clock, progress
05:34:00Z  VERIFY  server.py:225 dates every stamped line to TODAY, because an agent writes HH:MM:SSZ and no
                date. run_clock takes the conductor's START from that, progress passes it to git log as
                --since, so anything merged on an earlier day is excluded. Structural: for any project
                whose work landed before today, the bar can only read 0
05:34:00Z  WEIGH   where to get a real date : file mtime | first ISO line in the log | git log of the branch
05:34:00Z  DECIDE  anchor the LAST stamped line to the file's mtime and walk backwards -> mtime is a date the
                filesystem remembers, and a live log still lands on today because its mtime is now
05:34:00Z  VERIFY  run 7's last line is 02:38:54Z and its mtime is 12:38 local; 02:38:54Z IS 12:38 local.
                They agree to the minute, so the anchor is sound on the one real log available
05:34:00Z  TEST    994 passed, 0 failed, 10 deselected (8 new)
05:34:00Z  VERIFY  restarted the monitor against the same data: run start 2026-09-17T11:25:23, "24 of 25 work
                items merged", 96%. Was "0 of 25 ... next S-1, S-2, WI-0"
05:34:00Z  NOTE    WI-19 is the one it still does not count, and no r7/wi-19-* branch has ever existed on the
                remote -- so that may be true rather than a second defect. Not mine to decide
05:41:52Z  NOTE    removing 13 stale worktrees did not reduce the tab count: the monitor archives a removed
                worktree's docs/progress so its record survives, and the archive carries the WHOLE
                directory -- 30 files, every log the repo already tracks
05:41:52Z  VERIFY  every archived pane was titled "technical-lead", because the title is logs[-1].stem and
                technical-lead.md is alphabetically last in all of them; and each pane merged all 30
                logs, so one archived agent's tab held every other agent's lines
05:41:52Z  DECIDE  take the newest log by mtime as the agent's own -> it is the one it was still writing when
                the worktree went; the rest arrived with the checkout
05:41:52Z  VERIFY  panes now read code-reviewer-r7-amend-2-code-reviewer, r7-wi-18-coverage-audit and so on,
                with 4 to 18 lines each instead of 260
05:41:52Z  TEST    994 passed, 0 failed, 10 deselected
05:47:51Z  NOTE    the header read "run elapsed 100h". run_clock returned start and no end, so the UI counted
                to now: 17 Sept 01:25:23Z to today is 100.4 hours, which is how long AGO the run was,
                under a label saying how long it TOOK
05:47:51Z  VERIFY  run 7 took 1:13:31 -- START 01:25:23Z to DONE 02:38:54Z. Corroborated three ways: every
                other agent log falls inside that window (earliest 01:27:03Z, latest 02:32:36Z); 158 of
                the 168 commits that day sit inside it; the first is the lead's PLAN at 01:33:08Z and the
                last is WI-20's merge at 02:37:45Z, 69 seconds before DONE
05:47:51Z  DECIDE  a conductor's DONE ends the run -> clock stops there, header reads "run took" and "finished"
05:47:51Z  TEST    996 passed, 0 failed, 10 deselected (2 more)
