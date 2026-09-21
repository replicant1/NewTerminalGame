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
07:10:22Z  NOTE    Copilot: parse_log keeps UNSTAMPED lines, and one appended after the final stamp carries
                the file's mtime forward with it. If that tail crossed a midnight, the anchor sits a
                day ahead of the stamp it is pinning and every line in the log is dated a day late --
                which moves the whole run window with them
07:10:22Z  DECIDE  a stamp cannot have been written after the file was -> if the last stamp lands ahead of
                the mtime by more than a minute, it is a stamp from the day before. The minute absorbs
                the gap between reading the clock and the write landing; a real crossing is hours
07:10:22Z  NOTE    and nothing called run_clock() at all. The tests parsed a DONE line; none asked run_clock
                what it made of one, so a rename, an early break or an unset flag would have passed
07:10:22Z  VERIFY  16 tests in that file now, including run_clock with panes stubbed: DONE freezes the
                clock, a live run has no end, the last DONE wins, and a developer's DONE does not end
                a run. Suite 1015
07:10:22Z  VERIFY  live monitor unchanged by either fix: start 01:25:23Z, end 02:38:54Z, finished, 1:13:31
07:10:22Z  TEST    1015 passed, 0 failed, 12 deselected
07:16:44Z  NOTE    review round 1: the backwards walk read ANY forward jump as a midnight. Real logs are not
                monotonic -- r7-s-2-anchor-window.md in this repo runs 01:34:41, 01:35:10, 01:34:58,
                twelve seconds backwards -- so two lines landed a day early and an eleven-minute agent
                reported as 24h 11m. A NEW failure: the old "everything is today" code made order moot
07:16:44Z  NOTE    and my guard test could not fail for any input. Stepping the day back on every forward
                jump makes the output sorted by construction, so "stamps == sorted(stamps)" is true even
                for the wrongly dated file. A hollow assertion named in the summary as the guard
07:16:44Z  DECIDE  threshold at 12 hours -> a real crossing between consecutive lines is most of a day,
                because progress-tracking.md tells agents never to go more than a few minutes without
                writing. Noise is seconds. Twelve hours separates them with room in both directions
07:16:44Z  VERIFY  r7-s-2-anchor-window.md now lands on one day, span 0:11:16, measured against the file as
                it sits in the tree -- and that file is now a test
07:16:44Z  NOTE    rewrote test_two_midnights_step_back_twice: it used 10:00/02:00/01:00, which asserts two
                midnights with an 8h and a 23h gap between CONSECUTIVE lines. That log cannot exist,
                so the test pinned behaviour on input the system never produces
07:16:44Z  NOTE    the #elapsed hover still read "time since the first line" under a label saying "run took
                ... finished". Set from tickElapsed now, and the UI branches on run.finished, which
                run_clock sets and nothing read
07:16:44Z  TEST    1017 passed, 0 failed, 12 deselected
07:27:40Z  NOTE    round 2: one comment, and it is the unfinished documentation half of round 1's. The
                Scrutiny section still said the code assumes stamps are non-decreasing except at
                midnight -- the opposite of what it now assumes -- still named the hollow test as the
                guard after I had agreed it protected nothing, and never mentioned MIDNIGHT_JUMP_S,
                so main would carry no record of why a bare 12 is 12
07:27:40Z  VERIFY  reproduced the reviewer's threshold measurements myself over docs/progress: largest
                backwards inversion anywhere 12s, largest real gap between consecutive lines 4951s
                (83 min), threshold 43200s -- 3600x margin below, 9x above
07:27:40Z  NOTE    its reduction is better than my prose: the rule is "the mod-24 forward gap exceeds
                twelve hours", which picks the nearer of the two readings of an undated gap. Twelve
                is the only midpoint, not a tunable
07:27:40Z  TEST    1017 passed, 0 failed, 12 deselected
07:33:05Z  NOTE    round 3: the reduction I adopted on the reviewer's authority states the rule BACKWARDS,
                and the reviewer found it in its own sentence. Tested against the shipped parse_log:
                the 12s inversion -> code says one day, stated rule says midnight; 23:50/00:05 -> code
                says two days, stated rule says one; 01:00/14:00 -> code says one day, rule says
                midnight. The mod-24 is what breaks it -- an ordinary 1h gap has a mod-24 backwards
                jump of 23h, so the stated rule would fire on every normal line
07:33:05Z  DECIDE  use the wording server.py:198 already carries -- a stamp more than twelve hours later in
                the day than the one after it belongs to the previous day. Table and midpoint argument
                untouched, both were right
07:33:05Z  VERIFY  reviewer re-measured over 517 stamped pairs in 34 logs: my 4951s is the largest gap and
                its own round-2 figure of 4136s is now second. 18 test functions, no parametrisation
07:33:05Z  TEST    1017 passed, 0 failed, 12 deselected
