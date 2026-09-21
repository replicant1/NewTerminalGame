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
07:32:29Z  NOTE    round 3: the conductor's new query filtered on $CODE_REVIEWER_LOGIN inside the jq. It
                mints once at startup and shell state does not survive between tool calls, so by the
                sweep that variable is unset, the filter reads .user.login=="" and returns [] on an
                approved PR -- indistinguishable from a true "no approval", which is what the
                paragraph three lines below calls worse than not asking
07:32:29Z  VERIFY  measured both: filtered-on-empty gives [], the developer.md shape gives the approval
07:32:29Z  NOTE    round 2 saw this and passed it as low-stakes; round 3 reversed that, on the ground that
                the query had since become the conductor's ONLY way to see an approval. It declared
                it a late finding rather than a new one, which is the right way to reopen
07:32:29Z  DECIDE  the mint tool's "VAR=value; export VAR" stays for now and gets its own item. Three
                reviewers have mis-parsed it, but a 401 fails LOUDLY -- the opposite class from this
                amendment, which is about failures that look like success
07:32:29Z  TEST    999 passed, 0 failed, 12 deselected
07:37:25Z  NOTE    round 4: the closing paragraph counted three at its head and two in its body -- "all
                three ... and neither would have shown up in any test", then "in both cases ... a merge
                refused, and a verdict misrecorded". The omitted consequence is the third's, an
                approved PR filed as awaiting review, which this same amendment calls the worst
                outcome the gate has. The same failure as round 3: corrected where the new material
                went in, left stale in the sentence that generalises it
07:37:25Z  DECIDE  I asked to be told if the generalisation was glib and it was, in exactly one half.
                "A reading failure rather than a writing one" is contradicted by section 2 of this
                same document, whose lesson is stop WRITING into a shared directory. And "each caught
                by verification" is circular -- they were selected on that property
07:37:25Z  DECIDE  the property they actually share is that each produced a PLAUSIBLE WRONG ANSWER rather
                than an error: BLOCKED reads as not-yet-approved, a REQUEST-CHANGES body reads as a
                real rejection, [] reads as never-approved. Nothing anomalous is raised, logged or
                returned, which is why no test finds them -- and the verification point is now stated
                as a claim about the SHAPE rather than about these three
07:37:25Z  TEST    999 passed, 0 failed, 12 deselected
07:42:02Z  NOTE    round 5: table row 3 named the wrong consequence -- "[] is indistinguishable from a merged
                item that was never approved". Three things contradict it: a merged item with no
                approval is exactly what conductor.md tells the conductor to REPORT, so it is anomalous
                rather than invisible; section 3's own text says [] is what a genuinely UNAPPROVED pull
                request returns; and my own reply accepting round 4 named it as an approved PR filed as
                awaiting review. The one row that failed to exhibit the property its table exists for
07:42:02Z  NOTE    and "neither of those last two" pointed at items 2 and 3 where the query answers 1 and 3.
                Item 2 -- a REVIEW-REQUEST with no reviewer spawned -- returns [] from that query
                whether nobody was spawned or somebody was and requested changes. The same
                indistinguishable empty answer, a THIRD time, in the sentence introducing the corrected
                query. And gh pr view --comments does see half of it: the marker is a PR comment
07:42:02Z  DECIDE  item 2 is settled where it is visible -- the marker from the comments, the dispatch from
                the conductor's own DISPATCH lines
07:42:02Z  NOTE    the reviewer declined to comment on "which is why no test would have found any of them",
                because round 4 prescribed that wording -- but it is right that the reason is wrong. A
                test asserting a consequence against an independently sourced value IS an independent
                check. These escaped because they live in markdown nothing executes. Corrected anyway
07:42:02Z  TEST    999 passed, 0 failed, 12 deselected
07:45:35Z  NOTE    round 6: the paragraph I inserted last round sat between "That last sentence" and the
                sentence it referred to, so the deixis silently retargeted onto the inserted text --
                whose last sentence begins "These three", making it unambiguously a claim about the
                three defects, which the next line then denies. It also disarmed the anti-circularity
                guard those lines exist to be
07:45:35Z  DECIDE  replace the deixis with the clause it means rather than reorder the paragraphs -- a
                pointer that names its target cannot drift when something is inserted above it, and
                this document has now been broken twice by insertion
07:45:35Z  NOTE    the reviewer declined two things it could have raised and said why: row 3 names the
                misfiling where rows 1 and 2 name the innocent alternative -- but that wording was
                what its own round 5 comment prescribed, and changing the target after compliance
                would be grazing. And list item 1 also covers a standing REQUEST-CHANGES with a
                departed developer, which an APPROVED-only query cannot surface; the items-1-and-3
                mapping was its own, and the rework half is covered earlier in the file
07:45:35Z  TEST    999 passed, 0 failed, 12 deselected
08:14:58Z  NOTE    round 7: asked for a third drifted reference and it found a third AND a fourth. The
                finding said "the paragraph three lines below it" about a phrase that lives in
                conductor.md -- a cross-FILE count, so nobody diffing conductor.md would ever see it go
                stale. And conductor.md's "this paragraph calls the one most likely to end the run"
                named its own paragraph, which says no such thing, four lines after the document uses
                the same construction correctly
08:14:58Z  NOTE    plus "Look for those two" pointing at items 1 and 3 of a list four paragraphs above,
                past a paragraph about the middle one -- in an instruction file a conductor acts on,
                so the wrong two is a wrong sweep
08:14:58Z  DECIDE  all four drifts are one class: a reference that counts lines or gestures at a neighbour
                is true when written and false after the next insertion, and announces nothing. The
                rule is that durable prose should NAME its target -- recorded in the finding as the
                lesson, NOT added as an instruction at this amendment's seventh round. Its own item
08:14:58Z  VERIFY  swept all four files for counting or gesturing references; the only hits left are the
                quoted examples inside that note
08:14:58Z  TEST    999 passed, 0 failed, 12 deselected
08:20:15Z  NOTE    round 8: the note I wrote about miscounted references miscounted. It said four drifted
                "in it"; two of the four it quotes were in conductor.md, not the finding. And a fifth
                of the same shape was uncounted -- "Neither of those last two", fixed back in round 5,
                which my own round-5 log describes in the same terms
08:20:15Z  VERIFY  the reviewer also found one OUTSIDE this pull request and correctly refused to comment
                on it: technical-lead.md says the gate "is the code review described in the next
                section", where the next heading is "When a branch conflicts with main" and the review
                gate is 79 lines EARLIER. On main, wrong today, in a file an agent acts on
08:20:15Z  DECIDE  the note now names all five with their file and what was wrong, as a table -- and carries
                the technical-lead.md instance as the evidence that the class has already escaped this
                document. The rule still does not go into an agent file at round 8
08:20:15Z  NOTE    the reviewer's criticism of the deferral is fair and I am acting on it: "recorded in the
                finding" is weaker than it sounds, since nothing instructs an agent to read findings,
                and "deserves its own item" was a sentence in a commit message with no item behind it.
                The follow-up PR gets opened as soon as this merges, rather than promised
08:20:15Z  TEST    999 passed, 0 failed, 12 deselected
