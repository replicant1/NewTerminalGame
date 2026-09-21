# PR-AMEND-4 — delete the cap machinery, and the approval nobody merges

Risk: MEDIUM — no production code, but it removes the rule that decides when a review is
abandoned and fixes the state in which a completed work item silently fails to land.

Amendment 4. **The first change in this sequence that makes the definitions smaller:**

```
                     base   head
code-reviewer.md     5243   2344    −2899
conductor.md         4471   4545      +74
technical-lead.md    4279   4174     −105
developer.md         6041   6264     +223
                    -----  -----   ------
                    20034  19327     −707
```

**Measured with `wc -w` at this branch's merge base (`0e1c785`) and at its head**, which is
the only pair a reader can reproduce. An earlier version of this table quoted a "before"
column taken mid-branch, after this branch had already added content — it made the headline
−60%, and it was not reproducible from any commit in the history. The reviewer caught the
discrepancy on one file and then found the whole column unverifiable; the numbers above are
what replaced it.

**They say something less flattering and more useful.** `code-reviewer.md` really did lose
55% of its words. But `conductor.md` and `developer.md` *grew*, because this branch also added
the unmerged-approval dispatch and the merge exception — real additions that the compression
headline was quietly netting against. Across the four files the change is −707 words, not −60%
of anything.

## 0. Why this is mostly a deletion

AMEND-2 shipped a round cap. **Nobody asked for one.** The brief was always "loop until the
reviewer approves"; the cap came from a termination-condition worry raised during design, and
once it existed AMEND-3 was needed to repair it, and part of this amendment to clean up after
that repair.

The cost was not only the ~650 words of it. The failure that recurred five times across these
three pull requests — *a rule stated in four places and changed in three* — **can only happen
in a document long enough to say things four times.** A meaningful share of the findings in
those reviews were the process reviewing damage the process had created. Every one of the nine
commits to `code-reviewer.md` before this one added words; none removed any.

So the two convergence tests, the six-round backstop, the three trigger names and their
restatements in three other files are **gone**, replaced by what the loop always was:

> Review, comment, the developer fixes, review again, approve when you have nothing left to
> say. If you and the developer disagree about a comment and have each had your say, stop and
> let the technical lead settle it. Nothing else ends the loop.

That is the whole escalation rule, stated once, in the reviewer's file. The other three
agents no longer restate it — they say what a `BLOCKED` verdict means to them and stop.

The rest of the file was compressed the same way: the rationale paragraphs behind each rule
became clauses, and the App installation steps left the agent's prompt entirely for
`docs/AGENTS-SETUP.md`, since the reviewer never installs anything. **No rule was dropped in
the compression** — the measured facts that each exist to prevent a specific failure are all
still there, in a line each instead of a paragraph each.

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

- **The deletion itself** — the thing to check is whether anything load-bearing went with it.
  Every rule removed was either the cap machinery or a restatement of a rule that survives
  elsewhere; if you find one that is now stated nowhere, that is the finding.
- `.claude/agents/code-reviewer.md`, "When you and the developer disagree" — the entire
  escalation rule. If a genuine deadlock can now run forever, this is where it happens.
- `.claude/agents/developer.md`, the merge exception — the failure mode is width. If it can be
  read as licence to merge anything a conductor mentions, it has undone the rule it qualifies.
- `.claude/agents/conductor.md`, the dispatch — check the brief cannot be read as the conductor
  certifying the gate. It knows the sha it was approved at; it does not know the head now.
- `.claude/agents/code-reviewer.md`, the new opening — it tells the reviewer its own
  instructions may be wrong. Check it does not license ignoring them generally.

## Suite

`.venv/bin/python -m pytest -q` → **986 passed, 10 deselected**, unchanged. No code.
