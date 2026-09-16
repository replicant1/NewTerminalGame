# M5 — DEV-A — complete

**Work item:** WI-21, *the questions for a human*, as amendment 10 rewrote it.
**Branch:** `r6/wi-21-human-questions`, based on `main` at `238f4dd`, with
`origin/main` merged in twice as WI-22 and amendment 11 landed underneath it.
**Pull request:** [#66](https://github.com/replicant1/NewTerminalGame/pull/66).
**Mode:** non-local.

## What was finished

| File | What |
| --- | --- |
| `tools/the_questions.py` | new — the five questions and five rulings as data, the C-7 warning, option parsing with two caps, and `a_sitting`, which opens one bounded window on the real assembled game and reaps it |
| `tests/test_the_questions.py` | new — 49 tests. No window is created anywhere in it |
| `docs/findings/WI-21-the-five-questions.md` | new — all five questions recorded as **open**, each with its exact command, what to look for, and the one file a reversal lands in |
| `docs/prs/PR-WI-21-the-questions-for-a-human.md` | the PR body |
| `docs/progress/r6-wi-21-human-questions.md` | the log |

**No production code was touched.** `terminal_game/` is untouched on this
branch except by the merge of `origin/main` that brought WI-22's `frame_for` in.

## What it answers, and what it deliberately does not

**It answers nothing.** All five questions are still open after a whole run of
refusing to close them, and this item is the sixth refusal. Every `Question`
carries `answer=None`, the run's JSON report prints all five as `null`, and a
test walks the module's syntax tree and fails if anything anywhere could set
one. What it produces instead is that each question is now **cheap and
unambiguous to answer**: one command, one thing to look at, and one file if the
answer is no.

**Section 4 rule 5 was obeyed.** `/usr/bin/python3 -m terminal_game` was never
run. The real window was shown through a bounded harness over the same
`build_game`, and the command for the real game is handed to the user with a
list of what only it can answer. The findings say, question by question, which
of the two an answer would come from.

## The state of the test suite as I left it

From the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| When | Result |
| --- | --- |
| `main` at `238f4dd`, before this item | **740 passed, 0 failed, 0 skipped** |
| `main` at `b11a8a6` (WI-22 + amendment 11), merged into this branch | **747 passed, 0 failed, 0 skipped** |
| `r6/wi-21-human-questions` with this item's 49 tests | **796 passed, 0 failed, 0 skipped** |

The counts reconcile: 747 + 49 = 796.

This document is committed on the branch, so it is written before the merge.
The post-merge run — `git fetch origin && git merge origin/main`, then the same
command again — is reported in the handback and in the progress log, because it
cannot be written here without being written before it happened.

## The screen

**Nine windows opened, nine reaped, no modal sheet raised.** Short-first, as
every lane on this run has been: one 2-second window to prove the mechanics and
the reap before anything longer. Afterwards `pgrep` found no tool process under
any of the six names this project has used, and System Events counted **0**
processes named "Python". The project ledger goes from 30/30 to **39/39**.

Six of the nine were this item's own. **Three were not**: WI-22 changed two
on-screen tools and had no desktop slot, so both of its call sites were run
here, this being the last screen turn of the run. `the_look.py --view game`
painted **698** canvas items and `--view joinery` **714** — exactly the figures
WI-16 recorded before the change — and `window_manners.py --exercise keys`
behaved identically to WI-17's record. Its judgement that `frame_for` is
character-for-character the expression it replaced holds on a real screen as
well as in the suite.

## One thing the real screen caught that the suite would not have

The sitting originally scheduled **one** deadline, `owner.end_session`. Window 1
came back with the session's phase still `playing` — the deadline had taken the
window out from under the session rather than asking it to stop, which is the
same shape of defect WI-17 measured on the close button and WI-18 fixed.

It now schedules **two**, both before the event loop is entered:
`session.quit` at N seconds, which is what `--seconds` already does on the
production entry point and which leaves the phase `ended`; and
`owner.end_session` 1.5 s under it, which asks nobody's permission. **A faithful
route and an unconditional route are not the same route.** Window 2 onwards
reached `ended` with nothing pressed, and the suite pins it.

## Deviations needing a ruling

1. **The findings file is `WI-21-the-five-questions.md`, not
   `WI-21-human-answers.md`** as the plan's WI-21 entry names it. A document
   called "human answers" containing five unanswered questions is the one
   filename most likely to be misread. WI-20b has been told the name on the PR
   and told that I would post there first if it changes. One line to flip.
2. **Four questions to look at plus five rulings to decide, inside a
   five-question frame.** Section 13 and the conductor's brief enumerate the
   five slightly differently; nothing is dropped, question 5 is the rulings, and
   the split is by what answering costs — an observation needs an instrument, a
   ruling needs a blast radius.
3. **Two caps rather than one** — `MAXIMUM_SECONDS` (60) per window and
   `MAXIMUM_RUN_SECONDS` (180) per run. Additive; the plan asks only that the
   script cannot run unbounded, and capping one window still permits four
   minutes of somebody's screen.
4. **A new tool rather than an extension of `tools/play_the_game.py`.** Those
   four exercises are ~1.2 s machine measurements that print JSON; nobody can
   look at a 1.2 s window. And `tools/the_look.py` opens at the *default*
   position, never the real anchor — so before this item, WIN-4 had never been
   put in front of a person at all.
