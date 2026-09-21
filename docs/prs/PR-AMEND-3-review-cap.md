# PR-AMEND-3 — the round cap counted the wrong thing

Risk: MEDIUM — no production code, but this governs when a review is abandoned and handed
to the technical lead, so a mistake in it either stalls work that was converging or lets a
real deadlock run forever.

Amendment 3 to the agent definitions. **Four files** — the rule was stated in four places and
changing it in three would have left it unchanged — plus three tidy-ups the round 3 reviewer
of AMEND-2 flagged for the technical lead rather than the pull request. **No change
to `docs/IMPLEMENTATION_PLAN.md`** — the cap was never in it — and none to the work items or
the schedule.

## Why

AMEND-2 shipped a rule that said three rounds is the cap, and justified it like this:

> A loop that has gone three rounds has a disagreement in it that more rounds will not resolve.

**That is false, and the review of AMEND-2 itself disproved it.** Three rounds, seven
reviewer comments, **14 replies of `REVIEW-REPLY: FIXED` and one `DISPUTE`** — and that one
dispute was about a file outside the change, which the reviewer agreed with. There was no
disagreement between reviewer and developer at any point. Every finding was accepted. The
findings got smaller each round: four comments, then three, then none.

A fourth rejection would have posted `BLOCKED — review did not converge` and escalated a
review in which nothing was in dispute.

Both the user and the round 3 reviewer reached this independently.

## What the rule is now

**The loop ends when the reviewer approves. It escalates when it stops converging, which is
observed rather than counted.** Two tests, either sufficient:

- **A disagreement that has had its exchange** — comment raised, disputed with reasoning,
  held once with reasons, disputed again. Neither party decides it.
- **A round in which nothing moved** — at least one comment carried in, and none of them
  fixed, none withdrawn, and no reasoning offered that had not already been given. Note the
  framing: the test asks whether anything *entered* the loop, not whether anything was
  *settled*. An exchange where the developer disputes and the reviewer answers settles
  nothing and moves a great deal, so it does not fire this.

Six rounds remains as a backstop against a runaway, explicitly not as the mechanism.

The plan already draws this distinction, about maze repair of all things, and the words fit:
*"a generator told only 'not sound' cannot tell whether its last repair helped, and that is
the difference between converging and thrashing."* A round count is that impoverished signal
— it says a round happened and nothing about whether it helped.

## Scrutiny

- `.claude/agents/code-reviewer.md`, "The loop ends when you approve" — the two tests. The
  failure mode to look for is one that never fires: if neither test can be evaluated from
  what is on the pull request, the backstop becomes the mechanism again by default.
- `.claude/agents/conductor.md` — the inference that a fourth round *meant* opposite
  positions is removed. Check nothing downstream still counts rounds.
- `.claude/agents/developer.md` — the developer must not hurry or count rounds either; a
  gate is only as good as the least patient party to it.
- `.claude/agents/technical-lead.md` — the fourth copy, which Copilot found and the author
  had missed. It budgeted three rounds and escalated after three. Check that what replaced
  it gives the lead something it can actually plan against, having removed the number it
  used to plan against.

## The three tidy-ups

All three were reported by the round 3 reviewer, none as a merge blocker:

- **"the review document" dangled in three places** (lines 56, 80, 204) after AMEND-2
  withdrew the fifth document shape. The reviewer warned the phrasing invites a future
  reviewer to re-invent the withdrawn shape. Those observations now go in the report.
- **`code-reviewer.md` line 123** said "if that call is refused, do not work around it"
  without the *by GitHub* qualifier its sibling at line 198 gained in the same commit — so a
  *shell* refusal read as something not to route around, while the file gives the API route
  for that exact endpoint 66 lines later.
- **This branch has a progress log**, written from its first minute. AMEND-2's had none,
  which §1.7 requires; the reviewer declined to demand one retrospectively on the grounds
  that a backfilled log is worse than none, and it was right. The practice changes here
  rather than the rule.

## Suite

`.venv/bin/python -m pytest -q` → **986 passed, 10 deselected**, unchanged. This PR touches
no code.
