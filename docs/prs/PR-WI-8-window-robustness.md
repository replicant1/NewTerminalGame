# WI-8 — window robustness, the failure-path close, and the launch smoke

**Branch** `wi-8-window-robustness` · **base** `main` · **lands no new
requirement codes**; it hardens WIN-1..5, which WI-2 landed.

> **Draft.** In progress. This body is rewritten before the PR is marked ready.

WI-2 proved the happy path, and the happy path is not what loses somebody's
work. This item makes every failure path end with the window closed, the user's
other windows untouched, and a message saying what happened.

## Still being written

- the failure-path test module and its recording fake
- `./launch-smoke`
- the findings document recording the timeout
- the window census, before and after

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
