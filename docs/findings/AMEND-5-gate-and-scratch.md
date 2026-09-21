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

## What these have in common

Both are a *reading* failure rather than a writing one, and neither would have shown up in any
test. The first was found by re-verifying a verdict an agent had reported; the second by an
agent verifying its own output rather than assuming the call had done what it was told. In
both cases the system was one unchecked assumption away from acting on something false — a
merge refused, and a verdict misrecorded.
