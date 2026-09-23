# RECORDS: run 8's leftover completion records

Risk: LOW. Documentation only: completion records and post-merge progress-log lines. No code, tests or plan.

This lands the records that could only be written after their own work item had merged. Each developer pushed them on a branch with no PR, and the conductor ruled they would go in together in one PR at the end of the run instead of one PR each.

## What it carries

| Branch | Commit | Files |
|---|---|---|
| `r8/m2-dev-a-completion` | `80ab180` | `docs/completions/COMPLETION-M2-DEV-A.md`, and post-merge lines in `docs/progress/r8-wi-8-ghost-policy.md` and `r8-wi-10-frame-composer.md` |
| `r8/wi-12-session-control` | `1dc330c` | `docs/completions/COMPLETION-M3-DEV-B.md`, and post-merge lines in `docs/progress/r8-wi-12-session-control.md` |
| `r8/completion-m1-dev-c` | `4fa1f21` | nothing new: `COMPLETION-M1-DEV-C.md` already reached `main` inside WI-13 (#136) |

**Not carried, because nobody wrote them:** lane C's completion records for M2 (WI-9) and M3 (WI-13). They are recorded as missing. Writing them now, after the fact, would be worth less than their absence.

## Claims

| Claim | Evidence | Output shows | Control |
|---|---|---|---|
| RECORDS/A1: the diff touches only `docs/completions/`, `docs/progress/` and this brief in `docs/prs/` | `git diff --stat origin/main...HEAD` | 6 files, all under those three directories, with 0 deletions | n/a: docs-only |
| RECORDS/A2: each file is byte-identical to its source branch's copy | `for b in r8/m2-dev-a-completion r8/wi-12-session-control; do git diff origin/$b HEAD -- $(git diff --name-only origin/main...origin/$b); done` | prints nothing | n/a |
| RECORDS/A3: the default suite is unchanged | `.venv/bin/python -m pytest -q` | 558 passed, 0 failed, 1 skipped, 24 deselected, as on `main` `0ee0532` | n/a |

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->
