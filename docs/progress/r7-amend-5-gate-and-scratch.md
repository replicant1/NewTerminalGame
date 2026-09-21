# r7/amend-5-gate-and-scratch

07:06:01Z  START   AMEND-5: two ways a review can be read wrongly, both found during #113's sixth round
07:06:01Z  VERIFY  the merge gate returned one page. #113 had 31 reviews and gh returns 30 without
                --paginate; the approval was the 31st, so the gate said BLOCKED on a pull request
                that was properly approved. Every inline reply creates a COMMENTED review, so the
                longer the review the more certain the gate is to refuse -- exactly backwards
07:06:01Z  VERIFY  round 6's reviewer read a stale verdict.md from the SHARED scratchpad (46 entries of
                earlier reviews' litter) and posted an approval carrying round 4's REQUEST-CHANGES
                text. State was APPROVED and correctly bound throughout; only the body was wrong
07:06:01Z  DECIDE  the trap is the NAME, not the directory -> verdict.md is what every reviewer reaches
                for. Write it in the reviewer's own worktree, which is private and reaped, and name
                it VERDICT-<ITEM>-<round>.md, which cannot be another review's
07:06:01Z  DECIDE  and tell the reviewer to read its verdict back after posting -- that is the check that
                caught this one, and it was not required of it
07:06:01Z  TEST    998 passed, 0 failed, 12 deselected
