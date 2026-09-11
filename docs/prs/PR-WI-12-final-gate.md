# WI-12 — the final gate and the human-check run

**Branch** `wi-12-final-gate`, cut from `origin/main` at `bb651e0`.
**Lane** Dev B · **Iteration** M3 · **Depends on** everything.

This work item adds **no code**. Its whole output is evidence about a finished
`main`, which is why plan §6 says it merges last.

---

## What it produces

| File | What it is |
| --- | --- |
| `docs/completions/COMPLETION-M3-DEV-B.md` | The traceability confirmation — all 49 requirement codes, each with the test or the human check that demonstrates it, plus everything still unverified |
| `docs/findings/WI-12-human-check-results.md` | The answer sheet for H1–H6. Every verdict field deliberately empty |
| `docs/progress/wi-12-final-gate.md` | The progress log |
| `docs/prs/PR-WI-12-final-gate.md` | This file |

---

## The gate

**The suite**, at the pinned command from plan §2.2, run from the repo root:

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 749 tests in 12.673s

OK (skipped=2)
```

**`./verify`**, WI-10's harness, verbatim:

```
$ ./verify
[1/3] the test suite ... ok (12.5s)
[2/3] the launch smoke ... ok (10.1s)
[3/3] the scripted play-through ... ok (0.1s)

========================================================================
VERIFICATION PASSED -- 3 of 3 stages, 22.6s
  ok   the test suite -- Ran 749 tests in 12.186s; OK (skipped=2)
  ok   the launch smoke -- run 1: PASS in 9.6s
  ok   the scripted play-through -- 3 scripted games, each ending on the recorded picture
========================================================================
This is the half of 'right' a machine can check. The other half is
docs/findings/WI-10-human-checks.md, and it needs a person.
```

**Window census** around the smoke stage, which opens one real Terminal window
on the user's screen (plan §2.6):

```
before   visible  367, 2486          all  367, 2486, 2420, 2440
after    visible  367, 2486          all  367, 2486, 2420, 2440, 4656
```

The visible list is **identical** before and after. The all-windows list gained
`4656` — the smoke's own window, opened, closed and now invisible — which is
exactly the behaviour `docs/findings/WI-10a-census-output-shape.md` records: a
closed window never leaves `id of every window`, it only goes invisible. The
census reconciles. **Nothing that was on the user's screen before is missing
from it.**

---

## The two honest answers this item exists to give

### The six human checks were not run, and nothing pretends otherwise

**0 of 6 run. 6 of 6 awaiting the user.** The user was not reachable from the
session that produced this; the technical lead has put the request to them.
Every verdict field in `docs/findings/WI-12-human-check-results.md` is visibly
blank so that somebody fills it in rather than discovering later that it was
quietly guessed.

**H1 is a permanent exclusion, not a missed run.** It asks where the game's
window lands *relative to the window `./play` was typed in*. Every agent here
runs without a controlling tty, so that reference window does not exist on an
agent's side of the seam. No agent on this project can ever make check H1,
however the code changes. WI-10's `./check-window-placement` reduces it to one
command for the user, and that is as far as any amount of engineering can take
it.

**A green `./verify` is not evidence for a human check** and has not been
recorded as one anywhere in either document.

### The three open questions are open, and are not written as decided

Plan §9's **A1**, **A2** and **A3** are with the user and **unanswered**. The
code proceeds on the architect's assumptions; **an assumption is not a ruling**.
All three are listed by name in the completion's "still unverified" section,
each saying which way the code currently behaves and that the question is open.
**WI-11, which exists only to apply those answers, is held open.**

---

## Traceability

**49 of 49** codes are covered. The completion document gives, for each, the
named test or the human check that demonstrates it, and says plainly where a
code rests on a human check rather than implying a test exists.

Every mapping was audited against the **assertion**, not against the comment: a
requirement code appearing in a test file is a claim until the body of the test
has been read. The audit's findings — including any test that does not hold up —
are in the completion document.

---

## Deviations from the brief

The brief says *"walk the user through all six human checks and record their
answers, verbatim."* **That could not be done**: the user is not reachable from
this session. What has been delivered instead is the answer sheet with a line
for every one of H1–H6, each marked not run, with what the user must do and what
they should write back — which is the part of the brief that was achievable
without them. The brief's "done when" is met on its literal terms (*"the
human-check results file has a line for each of H1–H6"*), but the checks
themselves are still outstanding and the project's definition of done (plan §13,
item 4) is **not** met until the user has run them.

No `MUTATE` line appears in the progress log and the report's mutation section
reads `not applicable — not part of this workflow`, per plan §2.7.

---

## Testing

This item adds no code, so it adds no tests. The suite it gates is quoted above
verbatim, at the pinned command, from the repo root.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
