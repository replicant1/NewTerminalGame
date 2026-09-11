# WI-12a — re-gate the project after WI-13

**Branch** `wi-12a-regate`, cut from `origin/main` at `62ae038`, the merge of
**PR #16 (WI-13)**.
**Changes** `docs/completions/COMPLETION-M3-DEV-B.md` and
`docs/progress/wi-12a-regate.md`. **Nothing else.**

No code. No tests. `termgame/` untouched and byte-identical to `62ae038`; no
test added, removed, renamed or weakened. This is a gate, and a gate that edits
what it gates is not a gate.

---

## Why

WI-12 gated the project at 749 tests and found four requirement clauses that
nothing anywhere demonstrated. It refused to fix them, correctly. WI-13 — a
**different developer** — closed them, merging as PR #16 at 774 tests with
`git diff -- termgame/` empty.

**That made the completion document false.** It still said, of clauses that are
now covered, *"No test demonstrates this requirement"*, *"nothing demonstrates
it"*, *"nothing demonstrates it, anywhere"* and *"the metric itself is not
pinned"*, and its totals still read 45 of 49.

This work item re-measures the gate and brings the document up to date. **A
third developer does it, so that WI-13's evidence is checked by somebody who did
not produce it.**

---

## The evidence, quoted exactly

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 774 tests in 13.870s

OK (skipped=2)
```

```
$ ./verify
[1/3] the test suite ... ok (13.6s)
[2/3] the launch smoke ... ok (10.0s)
[3/3] the scripted play-through ... ok (0.1s)

========================================================================
VERIFICATION PASSED -- 3 of 3 stages, 23.7s
  ok   the test suite -- Ran 774 tests in 13.256s; OK (skipped=2)
  ok   the launch smoke -- run 1: PASS in 9.5s
  ok   the scripted play-through -- 3 scripted games, each ending on the recorded picture
========================================================================
This is the half of 'right' a machine can check. The other half is
docs/findings/WI-10-human-checks.md, and it needs a person.
```

**Window census either side of `./verify`**, which opens a real window on the
user's desktop:

| | visible | all |
|---|---|---|
| before | `367, 2486` | `367, 2486, 2420, 2440` |
| after | `367, 2486` | `367, 2486, 2420, 2440, **4725**` |

The visible list is identical. The all-list gained only the window the smoke
stage opened and closed. **Nothing that was on the user's screen before is
missing, and nothing was left behind.**

`./verify --only corner` was **not** re-run — see *Deviations*.

---

## The totals

| | WI-12, at `bb651e0` | WI-12a, at `62ae038` |
|---|---|---|
| Demonstrated by tests alone | 37 | **39** |
| Test plus a human check | 8 | **9** |
| Human check alone | 2 | **1** |
| Test plus a gap nothing covers | 2 | **0** |
| **At least one genuine test** | **45 of 49** | **48 of 49** |

Four codes moved: **START-2** and **CTRL-5** from test-plus-gap to test;
**SCRN-6** from human-check-alone to test-plus-human; **SCRN-7** from
test-plus-gap-plus-human to test-plus-human. **WIN-3** is the one code with no
test at all — nothing in this project has ever read a real window's title.
SCRN-3, SCRN-4, SCRN-5 and WIN-2 stayed where they were but each gained the
clause it was missing. **No code moved backwards and none lost evidence.**

---

## What was corroborated, and how

The brief was to **judge** WI-13's assertions, not count them. Every number
below was recomputed or observed here, not read out of WI-13's PR summary.

**SCRN-6 — the status line is cyan.** The obvious fix would have been to assert
the index is `51`, which restates the code and cannot tell you the code is
wrong. WI-13 instead decodes the index into the xterm 6×6×6 cube and asserts
the **hue**. I did that arithmetic independently for all five styles:
`51 → (0,5,5)` cyan, `33 → (0,2,5)` blue, `178 → (4,3,0)` gold,
`226 → (5,5,0)` bright yellow, `213 → (5,2,5)` pink. The decoder has a
guard-on-the-guard rejecting greys and system colours, so it cannot decode a
hue that is not there. The colour is then followed to `init_pair`'s argument and
to the `ESC [ 38;5;51 m` bytes a real terminal received. **Three independent
levels. Genuine.**

**START-2 — the metric.** Two hand-built boards, each asserting the metrics
disagree *before* asserting which square the code picks. I recomputed both
tables: board 1, from the player at `(1,1)`, has `(1,6)` at 25 / 5 / 5 and
`(4,4)` at 18 / 6 / 3, so Euclidean and Chebyshev pick `(1,6)` and Manhattan
picks `(4,4)`; board 2 has `(5,5)` at 32 / 8 / 4, so Euclidean and Manhattan
pick `(5,5)` and Chebyshev picks `(1,6)`. Both tables are right, and neither
board alone would do — a third test pins exactly which rival each board is blind
to. **Genuine.**

**SCRN-7 — the hidden cursor.** `curs_set(0)` called from inside the game's own
`session()` returns the *previous* visibility, so `0` is the state the game left
behind, not one the probe set. That is exactly the distinction the old hollow
test got wrong. **Genuine.**

**CTRL-5 — the echo.** The valuable part is what WI-13 found while writing it,
and I re-read its reasoning against `termgame/screen.py` and agree: the tty's
own `ECHO` bit is useless here, because `initscr()` clears it unasked and
`curses.echo()` never sets it back — ncurses echoes in software from inside
`wgetch`. **WI-13's own first version of the test read that bit, could not fail,
and WI-13 caught it and rewrote it.** The test that shipped enters the real
`session()`, reads three `z`s through the real `Screen.read_key` with nothing
painted, and asserts no `b"z"` reaches the terminal — with the pty's own
line-discipline echo cleared first, so a `z` could only be the game's doing.
**Genuine**, with one limit named below.

**WIN-2, and the three smaller fixes.** The pty is now sized from
`termgame.model` and asserted against `termgame.window` — two independent
literals, `model.py:42-43` and `window.py:42-43`, which I checked really are
independent — with `(30, 40)` pinned besides so they cannot drift together. The
maze test's lying name was fixed **by raising the sweep to 1000 seeds rather
than lowering the name to 200**. The supervisor tautology was replaced with
`count(...) == 1` per operation, which catches a supervisor that opened two
windows and left one on the user's screen — a better test than the one the
tautology was pretending to be. The unmapped `z` moved from second-to-last to
second, so "it did not quit" can now fail.

**Nothing failed to hold up.** Four things are named as doubts anyway, in §9.3
of the completion document: CTRL-5 is demonstrated at the session rather than on
a painted maze (and *cannot* be demonstrated on one — C1 swallows the echo); the
colour tests are only as sound as the xterm palette assumption, which is what
H6 is for; WIN-2's pty test still does not measure a window Terminal actually
opened; and SCRN-7's test would also fail on a terminal that cannot hide a
cursor, which its renamed companion exists to tell apart.

---

## What did **not** change, and must not be read as having changed

- **All six human checks are still NOT RUN.**
  `docs/findings/WI-12-human-check-results.md` was re-read and **deliberately
  left unedited** — nothing in it had become untrue. A green `./verify` is not
  evidence for a human check and is recorded as none.
- **A1, A2 and A3 are all still open and unanswered. WI-11 is still held.**
  Nothing in this PR may be read as deciding any of them.
- **Plan §8 still assigns no human check to SCRN-6.** That was a planning gap,
  not a testing one, and no amount of WI-13 could close it. It still needs a
  ruling.

**One thing about the open questions did change, and it is worth the lead's
attention: A2 is now verifiable.** Before WI-13, if the user had answered
*"Manhattan"* and WI-11 had changed the one expression in
`rules.starting_ghost`, the entire suite would have stayed green — and it would
have stayed green if WI-11 had changed nothing at all. Nobody could have told
whether the change had taken. Two named tests now go red until their expected
squares are changed with the expression, deliberately, by whoever applies the
answer. **That is the difference between WI-11 being a change and WI-11 being a
change you can check.**

---

## Deviations needing a ruling

1. **Five checks were made by temporarily breaking one line of `termgame/`, and
   the practice was prohibited outright while this item was running.** The user
   has ruled it out under every name. Everything was restored before the ruling
   was acknowledged — `git diff HEAD -- termgame/` empty, `md5` matched the
   pre-edit copy of every file, and both the suite and `./verify` were re-run
   green afterwards, so the figures quoted above are from *after* all five. The
   results are recorded in §9.2 of the completion document **because they
   happened**, not as a method to repeat; the ruling itself directs that the
   record not be tidied. **No `BROKE` lines were added after it arrived, and
   everything checked afterwards was checked by reading and by independent
   arithmetic.**
2. **`./verify --only corner` was not re-run.** The brief asked for `./verify`;
   `--corner` puts a second window on the user's screen; and `git diff bb651e0
   62ae038 -- termgame/` is empty, so the program whose corner behaviour WI-12
   measured is byte-for-byte the one here. §1 of the completion document marks
   that block as WI-12's measurement rather than presenting it as fresh.
   **WI-12's standing request for a ruling on whether agents should run
   `--corner` is repeated, not withdrawn.**
3. **The findings in §4 are kept, not deleted.** Each is left as WI-12 wrote it
   with a `CLOSED` block beneath saying what closed it. A gate document that
   quietly loses its own findings once they are fixed is worth less than one
   that records them as closed: what was nearly shipped undemonstrated is the
   part nobody can reconstruct later.

---

## Contradictions in the plan and the architecture

- **`ARCHITECTURE.md:642` is fixed, and fixed the right way.** WI-13 rewrote
  the false *"measured: `noecho` set in `Screen.__enter__`"* row — a method that
  has never existed — and kept a visible `Correction, WI-13` block recording
  what it used to say, on the ground that a false record of verification is
  worse than a missing one. Agreed.
- **`IMPLEMENTATION_PLAN.md` §11 is now stale in two places**, which is the safe
  direction but is worth a line of the lead's time. It still credits START-2 to
  the exhaustive recount alone, and the recount is still metric-blind; the
  metric is carried by a class §11 does not mention. And its CTRL-5 row's *"echo
  is off"* is now true but still attributed to WI-4 / M0 rather than WI-13.
  **Whoever runs WI-11 will read §11 first.**

---

## Still needing a human

Unchanged from WI-12, and no test can change it:

1. **All six human checks, H1–H6.** H1 can never be run by an agent at all.
2. **A1, A2 and A3.** WI-11 is held on them.
3. **Plan §8's missing human check for SCRN-6.**
4. **Whether the title bar reads *Terminal Game*** — WIN-3, the one code with
   no test.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
