# WI-21 — the questions for a human

**Branch** `r6/wi-21-human-questions`, based on `main` at `238f4dd`.
**Suite** `/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"` →
**787 passed, 0 failed, 0 skipped** (740 on `main`, +47 here).

---

## What this item does, and what it deliberately does not

It makes five questions **cheap and unambiguous to answer**. It answers none of
them, and there is a test that says so: every `Question` carries `answer=None`,
and a structural check walks the module's syntax tree and fails if anything
anywhere could set one.

That discipline is the most valuable thing this run has produced — five
developers in a row have declined to convert a measurement into an answer, and
each was right. This item is the sixth refusal, made permanent.

## The one rule that shapes the whole item

**Section 4 rule 5 — no agent may run `/usr/bin/python3 -m terminal_game`.** The
finished game is unbounded by design, because `q` is the only way out of a
finished game (CTRL-4, END-6), so launched by an agent nobody is there to press
it. It is the user's to run.

So the work splits exactly as amendment 10 says it must, and **every answer will
say which of the two it came from**:

| | What it is | What it can answer |
| --- | --- | --- |
| **the harness** — `tools/the_questions.py` | `build_game` with everything at its default, at the real anchor, painted by the real surface, under a hard deadline | the titlebar, where the window landed, whether the type is comfortable |
| **the real game** — `/usr/bin/python3 -m terminal_game` | the shipped exit path, unbounded, **the user's to start** | a whole game played to an ending, a real `q` out of a *finished* game, a close button pressed by a hand, the process exiting |

The harness creates the window identically, which is why it answers the first
three faithfully. **It is not the shipped exit path** and the checklist says so
in as many words.

## Files

| File | What it is |
| --- | --- |
| `tools/the_questions.py` | the five questions and five rulings as data; the C-7 warning; option parsing with two caps; `a_sitting`, which opens one window on the real assembled game and reaps it |
| `tests/test_the_questions.py` | 47 tests. No window is created anywhere in it |
| `docs/findings/WI-21-the-five-questions.md` | the checklist written down, question by question, with what is open and what it would cost to change |
| `docs/progress/r6-wi-21-human-questions.md` | the log |

## What the suite owns here, per the plan

Two things, and they are the two the plan names.

**It cannot run unbounded.** A run with no deadline cannot be *asked* for:
`--seconds` must be positive and at most `MAXIMUM_SECONDS` (60), and a whole
run — every window added up — at most `MAXIMUM_RUN_SECONDS` (180). Both are
refused at parse time, before a window exists. Capping one window is not enough
on its own; four windows at the per-window maximum is four minutes of somebody's
screen and every one of them passes the first cap.

Beyond the parser, driven through WI-3's `RecordingToolkit` on virtual time:
the deadline is on the scheduler **before** the event loop is entered; with
**nothing pressed at all** the window is destroyed exactly once; and the virtual
clock at that moment is `<= seconds * 1000`, so it ended *by its stated time*
rather than merely eventually.

**It reaps its window on the failure path.** A surface that will not build —
a collaborator handed in by the test, with no production code altered anywhere —
still leaves `destroy_window` called exactly once, the failure reported in the
record rather than raised, and the event loop never entered.

## Three guards that are about the discipline rather than the code

- **No answer can be recorded.** Every `answer` is `None`; `Question`'s default
  is `None`; and nothing in the module constructs or assigns one.
- **The route to the unbounded game is structurally absent, not guarded.** The
  module imports no `subprocess`, no `multiprocessing`, no `pty`, and not
  `terminal_game.__main__`, and calls nothing that launches a process. Per
  amendment 6: an observation covers one run on one machine, an absence covers
  every run on every machine, and a guard is a flag somebody can flip.
- **No fifth copy of the state-to-frame binding.** WI-22 is consolidating the
  `compose_frame(state, status_row(...))` binding out of four call sites.
  `a_sitting` leaves `build_game`'s composer at its default, so the picture comes
  from the production join in `terminal_game/shell/game.py`; there is an AST test
  that this module never calls or imports either half.

## C-7 — the warning that has to come first

The checklist prints this **before** anything else, because otherwise the
behaviour reads as a bug and the obvious reaction is to grant a permission that
would change nothing:

> The window will open at the fixed fallback position (120, 120) on your
> **primary** display. It will **not** appear near your pointer. The toolkit
> reports the pointer in whole-desktop coordinates — measured `(-175, -448)`, a
> second display up and to the left — while describing only the primary at
> 1512 x 982. It knows the desktop is 5120 x 2422 but gives no origin, so there
> is no rectangle to bound the pointer into, and an unbounded anchor is treated
> as nothing seen. **Granting Accessibility would not change this.** The fix, if
> you dislike where it lands, is a better fallback position, not a permission.

There is a test that the warning names the position from the constant, says a
permission would not change it, and appears **above** the placement question.

## Proved against the real toolkit

Per "proved by a double is not proved", the one thing exercised against real Tk,
and what was observed, is in `docs/findings/WI-21-the-five-questions.md` §
*"What the harness did on a real screen"*, with the window count and the reap
count. Everything in this PR body that is a *decision* rather than an
observation is marked as such.

## Deviations needing a ruling

1. **The findings file is named `WI-21-the-five-questions.md`, not
   `WI-21-human-answers.md`** as the plan's WI-21 entry names it. A document
   called "human answers" containing five unanswered questions is the one
   filename most likely to be misread by whoever greps for it later. One line to
   flip if the technical lead prefers the planned name.
2. **The item is written as four questions to look at plus five rulings to
   decide, inside a five-question frame.** Section 13 and the conductor's brief
   enumerate the five slightly differently; nothing is dropped, and the split is
   by what answering costs — an observation needs an instrument, a ruling needs a
   blast radius. Question 5 is the rulings, so the count still reads as five.
3. **Two caps rather than one** (`MAXIMUM_SECONDS` and `MAXIMUM_RUN_SECONDS`).
   Additive; the plan asks only that the script cannot run unbounded.
4. **A new tool rather than an extension of `tools/play_the_game.py`.** Those four
   exercises are ~1.2 s machine measurements that print JSON; nobody can look at a
   1.2 s window. And `tools/the_look.py` opens at the *default* position, never
   the real anchor — so WIN-4 has never been shown to a person at all.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
