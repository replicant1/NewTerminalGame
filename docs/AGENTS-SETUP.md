# Setting up the code reviewer's GitHub identity

> **From run 8 this identity belongs to the verifier** (`.claude/agents/verifier.md`), which
> replaced the code reviewer. The App, its name, its slug, `tools/code_reviewer_token.py` and
> the `CODE_REVIEWER_*` variables are unchanged. The verifier also edits the status block in a
> pull request's body, which uses the same *Pull requests: write* permission as its reviews.

This is an operator's task, done once. It is here because nothing else in the repository
records it: the configuration lives outside the tree and cannot be committed.

## Why an App at all

GitHub refuses both `--approve` and `--request-changes` from a pull request's author, with
the exact errors recorded in `docs/findings/AMEND-2-review-permissions.md`. Every agent on
this project acts as the repository owner, who is also the author of every pull request they
open — so a reviewer sharing that account could not deliver a verdict GitHub recognises.

A GitHub App gives the reviewer an identity of its own, and its approvals are attributed to a
bot login rather than to a person.

## The App

1. **Create a GitHub App** owned by the repository owner. `Code Reviewer` was not free, so
   this project's is **NewTerminalGame Code Reviewer**, slug `newterminalgame-code-reviewer`,
   App id **5016462**, approving as `newterminalgame-code-reviewer[bot]`.
2. **Permissions — exactly three.** Pull requests: *Read and write*. Contents: *Read-only*.
   Metadata: *Read-only*. Nothing else: it never pushes, never merges, never administers.
3. **Webhook: uncheck Active.** Otherwise the form demands a URL that has no use here, and
   the "Subscribe to events" section disappears with it, which is correct.
4. **Install it** on the repository, *Only select repositories*.
5. **Generate a private key** and keep the `.pem` outside the repository — this repository is
   public, so a committed key is a published key. `*.pem` is git-ignored as a second defence.

## The two variables

```
export CODE_REVIEWER_APP_ID=5016462
export CODE_REVIEWER_PRIVATE_KEY=~/.config/newterminalgame/code-reviewer.pem
```

Both must be set wherever the agents run. **Without them the conductor refuses to start a
non-local run** — deliberately, because the alternative is every MEDIUM and HIGH work item
reaching the end of its review before anybody discovers the verdict cannot be delivered.

## Checking it

```
eval "$(/usr/bin/python3 tools/code_reviewer_token.py)"
echo "$CODE_REVIEWER_LOGIN"
GH_TOKEN="$CODE_REVIEWER_GH_TOKEN" gh api /installation/repositories \
  --jq '.repositories[].full_name'
```

A successful mint proves three things at once: the key signs, the App exists and is installed
on this repository, and GitHub issued a token for it. A failure prints nothing to stdout and
explains itself on stderr — the call site is `eval`, so a partial line would be eval'd as a
success.

**Never run the mint just to look at what it prints.** Its stdout is a live installation
token; echoing it puts a working credential wherever that output lands — a terminal, a log,
a transcript — and redacting it afterwards does not unsend it. `eval` it, or read
`$CODE_REVIEWER_LOGIN` afterwards, and check the token only with `test -n`. If one is
exposed it expires within the hour, but do not wait it out — **revoke it**:

```
curl -X DELETE -H "Authorization: Bearer <the exposed token>" \
  https://api.github.com/installation/token
```

That is one call, it needs no App admin, and it invalidates that token alone. Only if the
token is no longer to hand, uninstall and reinstall the App, which invalidates every token
issued to that installation — heavier, and it needs a human with admin rights.

**The login is discovered, not assumed.** App names are unique across GitHub, so the slug you
are given decides the login; nothing hardcodes it.
