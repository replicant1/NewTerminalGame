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
