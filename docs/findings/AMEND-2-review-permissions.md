# AMEND-2: what a single GitHub account can and cannot do to its own pull request

Measured on 2026-09-21 against `replicant1/NewTerminalGame` PR #109, a throwaway pull request opened as a draft for this purpose and closed immediately afterwards. It was kept a draft deliberately: `AMEND-2-copilot-review-behaviour.md` establishes that Copilot never reviews drafts, so the probe cost no automatic review.

The code review workflow in `.claude/agents/` rests on these results. They are recorded because the first two cannot be re-derived without opening another pull request, and the third changed the design.

## An author cannot approve or request changes on their own pull request

Author `replicant1`, acting as `replicant1`:

```
$ gh pr review 109 --approve --body "probe: approve"
failed to create review: GraphQL: Review Can not approve your own pull request (addPullRequestReview)

$ gh pr review 109 --request-changes --body "probe: request changes"
failed to create review: GraphQL: Review Can not request changes on your own pull request (addPullRequestReview)
```

Both refused, at the API rather than in the UI. **This is why the code reviewer runs under a separate GitHub identity — a GitHub App of its own.** Every other agent on this project acts as `replicant1`, which is also the author of every pull request they open, so a reviewer sharing that account could not deliver a verdict GitHub recognises.

## An author *can* submit a COMMENTED review on their own pull request

```
$ gh pr review 109 --comment --body "REVIEW-VERDICT: probe comment-review"
$ gh api repos/replicant1/NewTerminalGame/pulls/109/reviews --jq '.[]|{user:.user.login,state,commit_id}'
{"commit_id":"ada9c3f6…","state":"COMMENTED","user":"replicant1"}
```

Accepted, and it carries a `commit_id` matching the head. So the single-account fallback is mechanically available — a verdict could be a COMMENTED review rather than an approval. It is **not** what this project does, because a COMMENTED review is advisory: nothing distinguishes it from any other comment, and a gate that depends on an agent choosing to read one is a gate that can quietly stop existing.

## `reviewDecision` is empty when nothing is required

```
$ gh pr view 109 --json reviewDecision,headRefOid
{"headRefOid":"ada9c3f6…","reviewDecision":""}
```

With a COMMENTED review present and no ruleset requiring review, `reviewDecision` came back **empty** — not `REVIEW_REQUIRED`, not anything. This repository has no branch protection and no ruleset, so **`reviewDecision` cannot be relied on as the merge check.** Whether it would populate as `APPROVED` once a second identity approves is untested; it cannot be tested without that identity.

The developer therefore checks the reviews list directly, which is well-defined regardless:

```
gh api repos/{owner}/{repo}/pulls/<n>/reviews \
  --jq '[.[]|select(.state=="APPROVED")|{user:.user.login,commit_id}]'
gh pr view <n> --json headRefOid --jq .headRefOid
```

An approval counts when one exists, its `user.login` is not the pull request's author, and its `commit_id` equals `headRefOid`. The last of those three is the staleness check: without branch protection GitHub does not dismiss an approval when new commits are pushed, so an approval keeps standing over code nobody approved unless somebody compares the two shas.

## Why the existing Copilot App cannot be reused

`copilot-pull-request-reviewer[bot]` is already reviewing pull requests here, and it is a GitHub App, so the question of reusing it comes up naturally. It cannot be used, for two reasons that are independent of each other:

- **Acting as an App means signing a JWT with that App's private key.** That key is GitHub's, not the repository owner's, and no API submits a review on another App's behalf. Even enumerating installations is refused to an ordinary token: `gh api /user/installations` returns 403, *"You must authenticate with an access token authorized to a GitHub App"*.
- **It never approves.** All 108 of its reviews on this repository are state `COMMENTED` — see `AMEND-2-copilot-review-behaviour.md`. It could not produce an `APPROVED` review even if it could be driven.

What it does establish is that the pattern works here and that a bot's login is its App slug plus `[bot]`. The code reviewer needs a second App of the same kind, owned by the repository owner, whose private key the operator holds.

## The App can do everything the role needs — measured end to end

Measured on 2026-09-21 against PR #110, a second throwaway draft, after the **NewTerminalGame Code Reviewer** App (id 5016462, slug `newterminalgame-code-reviewer`) was installed on the repository. It approves as `newterminalgame-code-reviewer[bot]`.

The name `Code Reviewer` was already taken across GitHub, which is why the slug carries the project name and why `tools/code_reviewer_token.py` asks `GET /app` for the slug instead of assuming one.

All four things the role needs work, under an installation token minted by that tool:

| Action | Result |
| --- | --- |
| `gh pr review --approve` | accepted — `{"state":"APPROVED","user":"newterminalgame-code-reviewer[bot]"}` |
| `gh pr review --request-changes` | accepted |
| inline comment via `POST /pulls/110/comments` | accepted, comment id 4059119014, attributed to the bot |
| minting a token | `GET /app`, `GET /repos/.../installation`, `POST /app/installations/{id}/access_tokens` all succeed; token good for one hour |

Note that a standalone inline comment is wrapped by GitHub in a review of state `COMMENTED`, so the reviews list accumulates entries the gate must filter past. The gate selects on `state == "APPROVED"`, so it does.

## A push does not dismiss an approval, and the sha check is what catches it

The sequence on #110, in order:

1. App approves at `97fcd3f5`, which was head. Gate: **MAY-MERGE**.
2. A commit is pushed. Head becomes `5d30c488`.
3. The review is **still** `{"state":"APPROVED","commit_id":"97fcd3f5"}` — GitHub did not dismiss it, because there is no branch protection to dismiss it under.
4. Gate: **BLOCKED**, because no approval exists *at head*.

**This is why the developer's third test exists.** Without comparing `commit_id` to `headRefOid`, a single approval would keep opening the gate over every commit pushed after it, forever.

## `reviewDecision` stayed empty in every state

Checked after the approval, after the push, and after the request for changes: `reviewDecision` was `""` throughout — including while a genuine `APPROVED` review by a non-author was present at head. It reports on branch-protection requirements, which this repository has none of, not on whether anybody approved.

**So `reviewDecision` must not be used as the merge gate here.** An earlier draft of `developer.md` did exactly that, and no pull request would ever have merged.

## Method note

The probes cost two pull request numbers (#109 and #110, both closed), three commits on branches since deleted, and no Copilot review — both were kept as drafts throughout. Repeating either costs the same.
