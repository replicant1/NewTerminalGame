# WI-13 — close the gaps the final gate found

**Branch** `wi-13-close-the-gaps`, cut from `origin/main` at `d49f046`
(the merge of PR #15, WI-12).
**Nothing in `termgame/` changes.** Every commit here adds or repairs an
*assertion*, plus one wrong line in `docs/ARCHITECTURE.md`.

WI-12 audited all 49 requirement codes and deliberately fixed nothing, on the
grounds that a gate that edits what it gates is not a gate. This is the
repair pass. **Every finding was re-checked against the code before it was
acted on** — none was taken on trust — and every new assertion was broken on
purpose and observed to go red for the right reason.

*(This section is filled in as the work lands.)*

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
