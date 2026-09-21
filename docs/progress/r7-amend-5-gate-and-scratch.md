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
07:21:48Z  NOTE    review round 1: the read-back named no command, and the obvious one is the query this
                amendment exists to fix. Measured on #113: unpaginated, the reviews list returns five
                of the reviewer's own REQUEST-CHANGES verdicts and ZERO approvals, because the list is
                oldest-first and the approval was the 31st. A reviewer reading back there would find
                round 5's line and "correct" a verdict that was right
07:21:48Z  DECIDE  fetch the review by the id the create response returns -> one object cannot truncate
07:21:48Z  NOTE    and the conductor is told to find a PR sitting on an approval and a merged MEDIUM/HIGH
                with none, with no query that can answer either. My summary claimed --paginate "on the
                conductor's query"; there was no query. It has one now
07:21:48Z  DECIDE  the finding had the diagnosis backwards: the DIRECTORY was the defect, the name only the
                reflex that walked into it. In a directory one reviewer alone can reach, even
                verdict.md cannot collide. "Give it a better name" would leave the hazard for anything
                else written into a shared directory; "stop writing into one" does not
07:21:48Z  NOTE    the reviewer also caught that no REVIEW-REQUEST marker existed -- I dispatched it
                directly and skipped the step the conductor is supposed to watch for
07:21:48Z  TEST    999 passed, 0 failed, 12 deselected
07:28:20Z  NOTE    round 2: 2 comments, both introduced by round 1's own fix. The "What changes" bullet still
                asserted "the trap is the name" twenty lines above the paragraph in the same commit
                that calls that the wrong diagnosis -- and it is the half describing what the amendment
                DID that carried the withdrawn version
07:28:20Z  NOTE    and the suite line still said 998 where the head runs 999; the merge of main moved it
                inside this delta, the progress log and commit message were updated and that line was
                not. It matters because MEDIUM tells the reviewer to take the count from that document
07:28:20Z  VERIFY  the reviewer executed both round 1 fixes rather than reading them: the read-back by id
                against #113's approval returned APPROVE round 6 on the one pull request where the list
                lies, and the conductor's query returned the approval paginated and [] unpaginated
07:28:20Z  TEST    999 passed, 0 failed, 12 deselected
