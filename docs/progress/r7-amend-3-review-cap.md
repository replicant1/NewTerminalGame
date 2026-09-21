# r7/amend-3-review-cap

04:39:10Z  START   AMEND-3: the round cap counts the wrong thing, plus three tidy-ups the round 3 reviewer flagged
04:39:10Z  READ    .claude/agents/code-reviewer.md, developer.md, conductor.md — the three copies of the cap
04:39:10Z  NOTE    written from the branch's start, not afterwards. AMEND-2's branch had no log at all and the
                round 3 reviewer flagged it against IMPLEMENTATION_PLAN.md 1.7; a retrospective one would
                have been worse than none, so this is the practice changing rather than the rule
04:39:10Z  WEIGH   what the cap should measure : rounds elapsed | unresolved disagreement | rounds that resolved nothing
04:39:11Z  DECIDE  escalate on failure to converge -> two observable tests plus a backstop, because the evidence
                says a round count cannot tell a working review from a stalled one
04:39:11Z  VERIFY  PR #111, the review of AMEND-2 itself -> 3 rounds, 7 reviewer comments, 14 REVIEW-REPLY: FIXED,
                1 DISPUTE (on a file outside the change, which the reviewer agreed with). Zero disagreement
                between reviewer and developer, yet a fourth rejection would have posted BLOCKED
04:40:30Z  NOTE    IMPLEMENTATION_PLAN.md already draws this distinction about maze repair, section 5 WI-2:
                "a generator told only 'not sound' cannot tell whether its last repair helped, and that
                is the difference between converging and thrashing". A round count is that same
                impoverished signal. Borrowed the words rather than inventing parallel vocabulary
04:40:30Z  DRAFT   the two convergence tests, in code-reviewer.md, developer.md and conductor.md
04:40:30Z  DRAFT   three tidy-ups from the round 3 reviewer: the dangling "review document" at 56/80/204,
                the missing "by GitHub" qualifier at 123, and this log
04:40:30Z  VERIFY  the cap is in no part of IMPLEMENTATION_PLAN.md -> no amendment row needed, agent files only
04:40:30Z  TEST    986 passed, 0 failed, 10 deselected
04:40:46Z  NOTE    PR #112 opened as a draft and marked ready; Copilot's baseline pass starts from ready
04:46:21Z  NOTE    Copilot: 2 findings, both valid. There was a FOURTH copy of the rule, in technical-lead.md,
                which my greps for "three rounds is the cap" and "three rounds have passed" did not match
                because it said "up to three" and "after three rounds". Changing a rule in three of its
                four homes leaves the rule unchanged
04:46:21Z  NOTE    and code-reviewer.md's older dispute paragraph still escalated after ONE dispute, which
                contradicts the two-dispute sequence the new rule defines
04:46:21Z  TEST    986 passed, 0 failed, 10 deselected
04:50:28Z  NOTE    code review round 1: CHANGES_REQUESTED, 3 comments. Test B fired on the exchange test A
                governs -- developer disputes with reasoning, reviewer answers once, nothing is "resolved",
                so test B escalates the very round line 235 says is not a deadlock. It reinstated the
                escalate-after-one-dispute behaviour Copilot's finding had just removed, one screen above
04:50:28Z  DECIDE  test B asks whether anything ENTERED the loop, not whether anything was settled -> an
                exchange moves information both ways even though it resolves nothing
04:50:28Z  NOTE    and the six-round backstop named no stopping action, while every other file now says not to
                count rounds -- so the only runaway guard in the system did nothing
04:50:28Z  TEST    986 passed, 0 failed, 10 deselected
05:02:10Z  NOTE    round 2: CHANGES_REQUESTED, 2 comments. The same failure a FOURTH time -- the BLOCKED trigger
                is restated in conductor.md, technical-lead.md and developer.md, and I changed the rule in
                code-reviewer.md only. All three still said "nothing was resolved", the wording this very
                commit removed as wrong, and all three named two triggers where there are now three
05:02:10Z  NOTE    consequence worth recording: a BLOCKED --- six rounds would reach a lead told "both parties
                have said their piece", which is exactly what the backstop case is not
05:02:10Z  NOTE    and the PR body on GitHub was never resynced from the file -- developer.md requires the two
                to match and nothing in the process does it for you. gh pr edit, no commit, head unmoved
05:02:10Z  DECIDE  a silent resubmit gets "request changes again" the first time, "nothing moved" the second,
                because escalating a developer that was careless once spends the escalation on a sentence
05:02:10Z  TEST    986 passed, 0 failed, 10 deselected
05:10:27Z  MERGE   r7/amend-3-review-cap into main -- 986 passed, 10 deselected, by the developer after APPROVED @da5582f
