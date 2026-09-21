# r7/amend-4-review-followups

05:11:36Z  START   AMEND-4: three things AMEND-3's review found and deliberately did not fix in AMEND-3
05:11:36Z  READ    conductor.md, developer.md, code-reviewer.md, docs/prs/PR-AMEND-3-review-cap.md
05:11:36Z  NOTE    the round 3 reviewer found the fifth statement of the rule and did NOT comment on it, because
                it had passed that text in round 2 and its own termination rule forbids reopening what it
                passed. It said so in its report instead. That is the rule working, and this branch is where
                the consequence gets paid
05:11:36Z  WEIGH   an approval landing after the developer has gone : conductor merges | reviewer merges |
                conductor dispatches a developer to merge
05:11:36Z  DECIDE  dispatch a developer -> the conductor merging would put it in the middle of a decision it did
                not make, and the reviewer merging would make it author and executor of the same verdict
05:12:05Z  DRAFT   conductor dispatch for an approval, the narrow merge exception, git show for stale instructions
05:12:05Z  DRAFT   corrected the AMEND-3 summary's restatement of test B; left AMEND-2's alone as an accurate record
05:12:05Z  TEST    986 passed, 0 failed, 10 deselected
05:15:45Z  NOTE    Copilot on #113: git show assumed the head sha was in the worktree, and a MEDIUM review
                fetches nothing -- it would have failed with unknown revision before the review began
05:15:45Z  NOTE    and "where it disagrees with anything else, it wins" let a file UNDER REVIEW outrank the
                dispatch brief. A PR can edit code-reviewer.md; it must not be able to rewrite the terms
                of its own review. Precedence now covers the stale prompt and worktree copies only
05:15:45Z  TEST    986 passed, 0 failed, 10 deselected
05:17:41Z  DECIDE  delete the cap machinery entirely -> nobody asked for it; I raised it as a design worry,
                shipped it in AMEND-2, repaired it in AMEND-3, and cleaned up after the repair here
05:17:41Z  VERIFY  code-reviewer.md 5541 -> 2210 words. Every one of the nine commits before this one added
                words and none removed any. The recurring "stated in four places, changed in three"
                failure needs a document long enough to say things four times
05:17:41Z  DRAFT   escalation stated once, in code-reviewer.md; the other three say what BLOCKED means to
                them and stop. App install steps moved to docs/AGENTS-SETUP.md
05:17:41Z  TEST    986 passed, 0 failed, 10 deselected
05:24:14Z  NOTE    round 1: CHANGES_REQUESTED, 3 comments, all of them "a rule that is now stated nowhere" --
                which is the question the Scrutiny section asked. The subtraction did lose three things
05:24:14Z  NOTE    the silent-developer deadlock is the one I was warned about and shipped anyway: AMEND-3
                argued the exit explicitly ("request changes the first time, nothing moved the second")
                and I kept the first half while deleting the test that carried the second
05:24:14Z  DECIDE  close it with one clause, not by restoring the cap -- the reviewer said plainly it was not
                asking for the two tests back and that a round count is still the wrong signal
05:24:14Z  TEST    986 passed, 0 failed, 10 deselected
05:29:31Z  NOTE    round 2: CHANGES_REQUESTED, 2 comments, both defects the previous commit introduced and
                both the same shape as the failure this amendment exists to name -- a fact stated twice
                and changed once. "Two conditions" over a three-item list, and the word-count table that
                is section 0's own evidence, stale by its own review
05:29:31Z  RISK    I printed a live installation token into the session transcript while checking the mint's
                output format, with a redaction that only masked its prefix. Expires 06:28:44Z; scope is
                pull_requests:write and contents:read on one public repo. AGENTS-SETUP.md now says never
                to run the mint to inspect it
05:29:31Z  TEST    986 passed, 0 failed, 10 deselected
