# AMEND-5 — two ways a review can be read wrongly

Measured on 2026-09-21, both during the sixth review round of PR #113. Neither was found by
looking for it: one turned up because a verdict was verified rather than believed, and the
other because a reviewer read back what it had posted.

## 1. The merge gate returned one page

`developer.md` told a developer to read the reviews list with:

```
gh api repos/{owner}/{repo}/pulls/<number>/reviews
```

`gh` returns **thirty** and stops. Measured on #113 at its sixth round:

```
reviews without --paginate: 30
reviews WITH --paginate:    31     <- the approval is the thirty-first
```

**The approval was real, at the right head, by the right login — and the gate reported
`BLOCKED`.**

Thirty is not a lot. **Every inline reply creates a `COMMENTED` review**, so a pull request
with a genuine conversation on it crosses that in a few rounds; #113 did it in six. The longer
the review, the more certain the gate is to refuse the merge — which is exactly backwards.

It fails towards not merging, which is the right direction, but it says nothing about why: a
developer would see a valid approval on the page in front of it and a gate insisting there
was none.

## 2. A plausible filename in a shared directory

`code-reviewer.md` said to write the verdict body to a scratch file and pass it to
`--body-file`. The example name was `verdict.md`, and the session scratchpad is shared between
agents; by this point it held 46 entries of previous reviews' litter, including several files
of exactly that name.

Round 6's reviewer reached for one by reflex and **posted an approval whose body carried round
4's `REVIEW-VERDICT: REQUEST-CHANGES … — 3 comments`**. The review *state* was `APPROVED` and
bound to the right commit throughout, so the gate would have opened on a record that read as a
rejection.

It was caught for one reason: that reviewer read its own posted body back, saw the wrong first
line, and corrected it with `PUT /pulls/113/reviews/<id>`.

**The directory is the defect; the name was only the reflex that walked into it.** An earlier
draft of this finding had that the wrong way round, and the reviewer of the amendment corrected
it: in a directory only one reviewer can reach, even `verdict.md` cannot collide, so the
certainty comes entirely from moving the file into the reviewer's own worktree — which is
private, and reaped after it. The `VERDICT-<ITEM>-<round>.md` naming is belt and braces, and
worth having for the same reason a labelled measurement beats an unlabelled one, but it is not
what makes the collision impossible.

That distinction matters because it is the lesson the next amendment will reason from. "Give the
thing a better name" would have left the hazard in place for anything else written into a shared
directory; "stop writing into a shared directory" does not.

And the reviewer is now told to read its verdict back after posting, which is the check that
caught this one — **by id, never out of the reviews list**, which is paginated and oldest-first
and would hand back an earlier round's verdict.

## 3. And the query written to catch it, failing the same way

The conductor's new query filtered on `$CODE_REVIEWER_LOGIN` inside the `jq`. The conductor
mints once at startup and shell state does not survive between an agent's tool calls, so by the
time it sweeps, that variable is unset — the filter becomes `.user.login==""`, matches nothing,
and returns `[]` on a pull request that is approved.

```
--jq '[.[]|select(.state=="APPROVED" and .user.login=="")]|map({commit_id})'   -> []
--jq '[.[]|select(.state=="APPROVED")|{user,commit_id}]'                       -> the approval
```

**`[]` is what a genuinely unapproved pull request returns too**, so the two are
indistinguishable — which is what the paragraph three lines below it calls *worse than not
asking*. It asks for the approvals and compares the login itself now, which is the shape
`developer.md` already used.

Found by a reviewer that reversed an earlier round's judgement on it, having measured rather
than reasoned: round 2 had seen it and passed it as low-stakes, when the query was one of
several things the conductor might do. Round 3 pointed out it had since become the only way the
conductor can see an approval at all.

## What these have in common

**Each produced a plausible wrong answer rather than an error.** That is the property they
actually share, and it is what made all three survivable long enough to reach a pull request:

| | what it produced | what that is indistinguishable from |
| --- | --- | --- |
| the unpaginated gate | `BLOCKED` | a pull request nobody has approved yet |
| the stale verdict file | a review reading `REQUEST-CHANGES` | a real rejection |
| the empty-login query | `[]` | an approved pull request still awaiting review |

None of them raises, logs or returns anything anomalous. A wrong answer that looks exactly
like a right one cannot be caught by watching for failures, so each was caught instead by
somebody checking a result they had every reason to believe — a verdict re-verified rather than
taken, an agent reading back its own output, a query run both ways.

**No test would have found any of them either, though not for that reason.** A test that
asserts a consequence against an independently sourced expected value *is* an independent
check, and would catch a plausible wrong answer — that is this project's own doctrine in
`tests-that-can-fail`. These three escaped because they live in agent-instruction markdown,
which nothing executes.

**That each was caught by somebody checking a result is not a claim about these three defects.**
It is a claim about the shape: an output indistinguishable from a correct one fires no
anomaly-watcher, so only an independent check can reach it. Said of the three, it would be
circular — they entered this document by having been found that way.

An earlier draft called all three "reading failures rather than writing ones", which section 2
of this document contradicts directly: the lesson there is *stop writing into a shared
directory*, and the hazard is located in the write. The common property is the plausible wrong
answer, not where in the cycle it arises.
