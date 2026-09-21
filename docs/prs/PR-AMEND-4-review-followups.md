# PR-AMEND-4 — the approval nobody merges, and two records that lied

Risk: MEDIUM — no production code, but one of these is the state in which a completed work
item silently fails to land, and it is the state the review gate is most likely to end in.

Amendment 4 to the agent definitions. Three files plus one corrected record. **No change to
`docs/IMPLEMENTATION_PLAN.md`**, the work items, or the schedule.

All three came out of AMEND-3's own review, and none was fixed there: two because correcting
them would have moved the head and invalidated a valid approval, and one because the reviewer
had already passed that text and its own termination rule forbids reopening what it passed.
It put them in its report instead. That is the rule working; this is where the consequence
gets paid.

## 1. The approval that nobody merges

**The gap.** `conductor.md` says what to do when a verdict lands on a pull request whose
developer has finished and gone: dispatch a developer for the rework round. That is written
for a *rejection*. Nothing covered an **approval** — and an approval is the likelier case,
because a developer that has finished its work and reported is exactly the one most likely to
have ended, and the approval is what arrives last.

So the ordinary shape of a completed MEDIUM or HIGH work item is an `APPROVED` review landing
on a pull request with nobody left to merge it. The reviewer has finished and never merges;
the conductor does not merge; the developer has gone. GitHub holds an approved pull request
open indefinitely without complaining.

**A pull request sitting on an approval is the one state that looks like success and is not.**

The conductor now dispatches a developer to merge, with the PR number, the branch and the sha
the approval was given against — and is told to say it is approved rather than that it may
merge, because that is not the conductor's to certify.

## 2. The exception that follows, kept narrow

`developer.md` says *"Merge only your own PR. Never merge, approve or close another
developer's."* A dispatched merge is exactly that, so the exception is now written down
rather than left for someone to infer or to route around:

- it is the conductor's to invoke, not the developer's to assume;
- the developer **runs the three tests itself** — the conductor certifies nothing, and between
  its dispatch and the merge somebody may have pushed, which the third test catches;
- the developer **changes nothing**. If the gate does not pass, report and stop. Merging is
  not adopting: you did not write the code, and the reviewer did not review yours.

## 3. Neither the prompt nor the working tree is reliable

Across four reviews the reviewer's own instructions were stale twice, in opposite ways: a
system prompt rendered from the commit *before* the fix it was reviewing, and a worktree that
arrived at the merge base carrying the rule the pull request had removed. Each time the
reviewer only got the right text because the dispatch brief told it to go and find it.

`code-reviewer.md` now opens by saying so, and names the one copy that is authoritative:

```
git show <head sha>:.claude/agents/code-reviewer.md
```

This matters here more than it would elsewhere: **this project amends agent definitions as
work items**, so the rules a reviewer is handed are exactly the thing most likely to be out of
date, and a reviewer enforcing a withdrawn rule is worse than one enforcing none.

## 4. A record that misdescribed what it shipped

`docs/prs/PR-AMEND-3-review-cap.md` restated the second convergence test as *"a round that
resolved nothing … none argued to a conclusion"* — the resolution framing AMEND-3 itself
removed as wrong. Under that wording a dispute-then-answer exchange fires the test; under the
shipped wording it does not. It was the fifth statement of the rule and the only one still
carrying the superseded framing.

`PR-AMEND-2`'s "three rounds is the cap" is **left alone deliberately**: that is an accurate
record of what AMEND-2 shipped. This one was not.

## Scrutiny

- `.claude/agents/developer.md`, the merge exception — the failure mode is width. If it can be
  read as licence to merge anything a conductor mentions, it has undone the rule it qualifies.
- `.claude/agents/conductor.md`, the dispatch — check the brief cannot be read as the conductor
  certifying the gate. It knows the sha it was approved at; it does not know the head now.
- `.claude/agents/code-reviewer.md`, the new opening — it tells the reviewer its own
  instructions may be wrong. Check it does not license ignoring them generally.

## Suite

`.venv/bin/python -m pytest -q` → **986 passed, 10 deselected**, unchanged. No code.
