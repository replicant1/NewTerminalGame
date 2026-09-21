# PR-AMEND-2 — a code reviewer in front of `main`

Risk: MEDIUM — no production code changes, but this governs how every future work item
reaches `main`, and a mistake in it either lets unreviewed code land or stalls every
developer at their merge.

Amendment 2. One new agent, three amended, one tool with its tests, three findings, and
two changes to `docs/IMPLEMENTATION_PLAN.md` — a fifth document shape in §1.7 and a new
§1.9 for risk floors. **No change to the work items, the lanes, the effort totals or the
gantt.**

## Why

Non-local mode had no gate at all. `gh pr merge` runs on the server, so a developer
opened its own pull request, marked it ready and merged it, and the only thing that had
looked at the code in between was Copilot — whose comments nobody was required to
answer.

**Seventy-seven of this repository's hundred and eight pull requests carried a
`🟡 Changes recommended` verdict, and every one of them merged anyway.** Whether those
comments were right is not the point. Nothing asked.

## What lands

A **code-reviewer** agent reviews MEDIUM and HIGH risk pull requests once Copilot is
clean, and its verdict is a real GitHub review. A developer may not merge until an
`APPROVED` review by the reviewer exists *against the commit being merged*. LOW risk
merges on Copilot and a green suite alone.

- `.claude/agents/code-reviewer.md` — new. Read-only: it never writes code, commits,
  pushes or merges. Approving is the one thing it does to a pull request.
- `.claude/agents/developer.md` — rates the risk, drives the Copilot pass, requests
  review, answers or disputes each comment, and merges only through the three-part gate.
- `.claude/agents/technical-lead.md` — sets a risk floor per work item, budgets the
  review rounds into the schedule, and settles reviews that do not converge.
- `.claude/agents/conductor.md` — verifies the reviewer's identity before dispatching
  any work, spawns a reviewer per round, and distinguishes *awaiting review* from
  *stalled*.
- `tools/code_reviewer_token.py` — mints the App installation token. Standard library
  and `openssl`; `requirements.txt` is unchanged.

## Scrutiny

The four places most worth a reviewer's attention:

- `tools/code_reviewer_token.py:73` — JWT construction. A ten-minute lifetime is
  GitHub's ceiling and the 60-second backdating absorbs clock skew; both are load-bearing.
  Verified by having `openssl dgst -verify` check a signature against its public key.
- `tools/code_reviewer_token.py:151` — the `except Failed` block prints **nothing** to
  stdout, because the call site is `eval "$(...)"`. A partial line would be eval'd as a
  success. Pinned by `TestAFailedMintPrintsNothing`.
- `.claude/agents/developer.md`, "Then merge it yourself" — the three-part gate. The
  third test (approval's `commit_id` equals `headRefOid`) is the only thing standing
  between a stale approval and an unreviewed merge; there is no branch protection here
  to dismiss approvals on push. Measured on PR #110.
- `.claude/agents/conductor.md`, "The review gate" — the startup identity check. If it
  is wrong, every MEDIUM and HIGH work item reaches the end of its review before anyone
  discovers the verdict cannot be delivered.

## Four decisions, and why

**The loop travels on the pull request, not between agents.** A developer cannot spawn
an agent, message one, or receive a message while it runs. Comments, replies and
verdicts live on the PR, where they also survive an agent ending mid-round.

**The reviewer is a GitHub App.** GitHub refuses both `--approve` and `--request-changes`
from a pull request's author, and every other agent acts as the repository owner, who is
that author. Without a separate identity the verdict could only be a comment asking to be
read as an approval — a gate that has quietly stopped existing.

**The technical lead sets the risk floor; the developer may raise it and never lower it.**
An author deciding whether its own work gets reviewed is the one place where its interest
and the project's point in opposite directions.

**Three rounds is the cap, and round *n* may only raise comments about the delta since
round *n-1*.** Both exist so the loop terminates. A reviewer that finds something new
every round is grazing, not reviewing.

## What is measured rather than assumed

Three findings, each with its method, because none of it can be re-derived without
opening another pull request:

- `docs/findings/AMEND-2-copilot-review-behaviour.md` — across all 108 pull requests:
  Copilot does not review drafts (92 had a draft phase, one for 73 minutes; none was
  reviewed before `ready_for_review`); it arrives a median 232s after ready, worst ever
  491s; it never approves — all 108 reviews are `COMMENTED`; the reviewer you *request*
  (`Copilot`) is not the account that *answers* (`copilot-pull-request-reviewer`); and
  the automatic review is an **account** setting, so nothing in a checkout records that
  the first pass exists at all; and **it cannot be re-run** — four routes to requesting a
  second pass were tried on this very pull request and none registers a request, which is
  why Copilot's pass is a baseline rather than a per-head condition.
- `docs/findings/AMEND-2-review-permissions.md` — an author cannot approve or request
  changes on their own PR (exact errors recorded); the App can do both, plus inline
  comments; a push does **not** dismiss an approval, so the sha check is what catches it;
  and `reviewDecision` is empty in every state on this repository, so it must not be used
  as the gate.

Both probes were kept as drafts throughout, so neither cost a Copilot review. PRs #109
and #110, closed, branches deleted.

## Suite

`.venv/bin/python -m pytest -q` → **985 passed, 10 deselected**, up from 967 by the 18
tests in `tests/test_code_reviewer_token.py`. No application code changes.

Those tests pin what the hand checks could not: the JWT claims, that the signature
verifies under `openssl`, that every spelling of the origin remote parses, that a DNS or
timeout failure becomes `Failed` rather than a traceback, and that a failed mint writes
nothing to stdout. The three API calls were exercised end to end against the installed
App on PR #110 and are not re-tested here; nothing in the suite touches the network.

## What needs a human

The App is installed and working, but its two environment variables are not in the
repository and cannot be: `CODE_REVIEWER_APP_ID` and `CODE_REVIEWER_PRIVATE_KEY` must be
exported wherever the agents run, or the conductor will refuse to start a non-local run.
The `.pem` lives outside the tree; `*.pem` is now ignored as a second line of defence,
because this repository is public.
