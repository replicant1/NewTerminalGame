# PR-AMEND-5 — the gate read one page, and the verdict read the wrong file

Risk: MEDIUM — no application code, but one of these decides whether a merge is allowed and
the other decides what a verdict says. Both were live on `main` before this.

Amendment 5. Three agent files and a finding. **No change** to `docs/IMPLEMENTATION_PLAN.md`,
the work items or the schedule.

## Why

Both were found during PR #113's sixth review round, and neither by looking for it.

### The gate returned one page

`developer.md` had the developer read the reviews list with `gh api …/pulls/<n>/reviews`,
which returns **thirty** and stops. On #113 at round six:

```
reviews without --paginate: 30
reviews WITH --paginate:    31     ← the approval is the thirty-first
```

**The approval was real, at the right head, by the right login — and the gate said `BLOCKED`.**

Thirty is not many, because **every inline reply creates a `COMMENTED` review**. The longer and
more thorough the review, the more certain the gate becomes that nobody approved. It fails
towards not merging, which is the right direction, but it leaves a developer looking at a valid
approval while the gate insists there is none.

Found by verifying a verdict an agent reported rather than believing it.

### The verdict read the wrong file

`code-reviewer.md` said to write the verdict body to a scratch file for `--body-file`, and
called it `verdict.md`. The session scratchpad is shared between agents, and by round six held
46 entries of earlier reviews' litter — several of them that name.

Round 6's reviewer reached for one by reflex and **posted an approval whose body carried round
4's `REVIEW-VERDICT: REQUEST-CHANGES … — 3 comments`**. The state was `APPROVED` and correctly
bound throughout, so the gate would have opened on a record that reads as a rejection.

Caught for one reason: that reviewer read its own posted body back.

## What changes

- **`--paginate` on both gate queries** in `developer.md`, with the measurement beside them so
  nobody removes it as noise. **And the conductor gets a reviews query at all** — it is told to
  find a pull request sitting on an approval and a merged MEDIUM or HIGH with none, and neither
  `gh pr list` nor `gh pr view --comments` can answer either. An earlier draft of this summary
  claimed `--paginate` "on the conductor's query"; there was no query behind it.
- **The verdict body is written in the reviewer's own worktree** — private, and reaped after it
  — **and named `VERDICT-<ITEM>-<round>.md`**. The trap is the *name*: `verdict.md` is what
  every reviewer reaches for, so a shared directory accumulates a file that is always plausible
  and usually somebody else's.
- **The reviewer reads its verdict back after posting — by id.** That is the check that caught
  this, and nothing had required it. **By id specifically**: the reviews list is paginated and
  oldest-first, so on #113 an unpaginated read returns five `REQUEST-CHANGES` verdicts and no
  approval. A read-back there would hand an earlier round's line to a reviewer that had just
  approved. The first defect in this amendment, reappearing inside the instruction written to
  catch the second.

## Scrutiny

- `.claude/agents/developer.md`, both gate queries — the second is the one the merge turns on.
  Check `--paginate` is on *both*, since the first is only a poll and the temptation is to fix
  the visible one.
- `.claude/agents/code-reviewer.md`, the read-back — check it says to compare the **first line**
  against what was intended, not merely that a body exists. A read-back that asserts nothing is
  the hollow assertion this project has a rule about.
- The naming rule — belt and braces only. **The certainty comes from the worktree**, which is
  private and reaped; in a directory one reviewer alone can reach, even `verdict.md` cannot
  collide. The finding says so now, because the wrong diagnosis ("give it a better name") would
  leave the hazard in place for anything else written into a shared directory.

## Suite

`.venv/bin/python -m pytest -q` → **998 passed, 12 deselected**, unchanged. No code.
