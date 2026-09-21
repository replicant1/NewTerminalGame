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

**The trap is the name, not the directory.** `verdict.md` is what every reviewer reaches for,
so a shared directory accumulates a file that is always plausible and usually somebody else's.
Two changes follow: the body is written in the reviewer's own worktree, which is private and is
reaped after it; and it is named `VERDICT-<ITEM>-<round>.md`, which cannot be confused with
another review's. And the reviewer is now told to read its verdict back after posting, which is
the check that found this one.

## What these have in common

Both are a *reading* failure rather than a writing one, and neither would have shown up in any
test. The first was found by re-verifying a verdict an agent had reported; the second by an
agent verifying its own output rather than assuming the call had done what it was told. In
both cases the system was one unchecked assumption away from acting on something false — a
merge refused, and a verdict misrecorded.
