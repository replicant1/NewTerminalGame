# AMEND-2: how Copilot's automatic review actually behaves on this repository

Measured on 2026-09-21 against every pull request `replicant1/NewTerminalGame` has raised — 108 of them, numbers 1 to 108. The review process in `.claude/agents/` depends on these facts, so they are recorded here rather than being inferred a second time by whoever next reads the workflow.

## Method

```
gh pr list --state all --limit 200 --json number,createdAt,reviews
gh api repos/replicant1/NewTerminalGame/issues/<n>/timeline --jq '.[]|select(.event=="ready_for_review")'
```

For each pull request: its creation time, the time of its `ready_for_review` event if it had one, and the submission time and body of every review on it.

## It does not review drafts

**92 of the 108 pull requests had a draft phase**, and in **none** of them did a review arrive before the `ready_for_review` event. The longest draft phase was PR #13, at 73 minutes; PR #78 spent 60 minutes as a draft and PR #9 spent 33. Every one of them was reviewed only after it was marked ready.

The trigger is `gh pr ready`, not `gh pr create`. `developer.md` opens pull requests as drafts deliberately, so there is nothing to poll for until the work item is finished and marked ready.

## Latency from ready-for-review

Measured from `ready_for_review` where there was one, from creation otherwise, to the first review:

| | seconds |
| --- | --- |
| minimum | 83 |
| median | 232 |
| 90th percentile | 384 |
| maximum | 491 |

**All 108 were reviewed. None was missed.** A fifteen-minute give-up window is roughly twice the slowest case ever observed here.

## It never approves

Every one of the 108 reviews was submitted in the `COMMENTED` state. Not one was `APPROVED` or `CHANGES_REQUESTED`. Waiting for an approval from Copilot would wait forever; the verdict is in the body instead.

The body opens with one of three headers:

| Header | Count |
| --- | --- |
| `### 🟡 Changes recommended` | 77 |
| `### 🟢 Approval recommended` | 24 |
| `### 🔵 Needs a closer look` | 7 |

and carries its own count of findings on a `**Comments generated:** N` line — 24 reviews generated none, and the largest generated nine.

## Two different names

The reviewer you **request** is `Copilot` (a `Bot`, id 175728472, as recorded by the `review_requested` timeline event). The account that **posts** the review is `copilot-pull-request-reviewer`. They are not interchangeable: filter on the second, request the first.

## It cannot be re-run, and it has never re-reviewed

**No pull request on this project has more than one Copilot review**, and on 2026-09-21 four routes to asking for a second one were tried on PR #111. None registers a request — no `review_requested` event appears on the timeline afterwards:

| Route | Result |
| --- | --- |
| `gh pr edit 111 --add-reviewer Copilot` | `GraphQL: Could not resolve user with login 'copilot'` — `gh` resolves the name as a *user*, and Copilot is a Bot |
| `POST /pulls/111/requested_reviewers` with `reviewers[]=Copilot` | HTTP 200, `requested_reviewers: []`, no timeline event. Accepted and ignored |
| the same with `reviewers[]=copilot-pull-request-reviewer` | HTTP 422, *"Reviews may only be requested from collaborators"* |
| `GET /users/copilot-pull-request-reviewer` | resolves to an **Organization**, id 213165537 — not the Bot that was requested (`Copilot`, id 175728472) |

The timeline's own record of the automatic request names `Copilot`, a `Bot`, which is not a login any of these endpoints will take from this account.

**So Copilot's pass is a baseline and not a per-head condition.** It reviews a pull request once, when it is first marked ready. It does not follow the fixes made in answer to it, and no agent on this project can make it. A human can use the re-request control on the pull request page; nothing in the workflow may depend on that happening.

## The automatic review is an account setting, not a repository setting

It is switched on, and it is switched on somewhere the repository cannot see.

Every one of the 108 pull requests has a `review_requested` event: actor `replicant1`, requested reviewer `Copilot`, on all 108. On the 92 that had a draft phase, that request fires **0 to 1 seconds after `ready_for_review`** — one second on 71 of them, zero on 21. Nothing clicks a button within a second of an API call, 108 times running; that is automation.

It is not configured on the repository:

- `gh api repos/replicant1/NewTerminalGame/rulesets?includes_parents=true` returns `[]`, so no ruleset requests it.
- `branches/main/protection` returns 404, branch not protected.
- There is no `.github` directory, in the working tree or on the remote.

So it comes from the account-level Copilot preference, which applies to pull requests the owner opens in their own repositories and records the owner as the actor. **There is no API that reports it** — `/user/copilot`, `/user/settings/copilot` and `/user/copilot/settings` all 404 — so this inference from behaviour is the only evidence available, and it is the reason this document exists.

One consequence, and it is favourable: every agent on this project acts as `replicant1`, so every pull request an agent opens is one of the owner's own and is covered. Nothing extra needs enabling for the developers.

One caveat: because the setting lives on the account, **nothing in a checkout records that the first review pass exists at all**. A reader of this repository has no way to discover it except by observing it happen.

## What this repository does not have

`gh api repos/replicant1/NewTerminalGame/rulesets` returns nothing. There is no branch protection and no required status check, so **nothing mechanically prevents a pull request from being merged unreviewed**. Every gate in this workflow is a rule on an agent, not an enforcement by GitHub.

That matters in one concrete way: 77 of the 108 pull requests carried a `Changes recommended` verdict, and all of them merged anyway. Whether the comments were right is not the point — nobody was required to answer them.

The repository is **public** (`"visibility": "public"`, owner a User, sole collaborator `replicant1`), so rulesets and branch protection are available on it at no cost, should anyone want the gate enforced rather than followed. It is not enforced today, and enforcing it would collide with the LOW-risk tier, which is designed to merge without a reviewer: a required-approval rule applies to every pull request and cannot be made to skip one.
