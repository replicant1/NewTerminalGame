# WI-3 — progress log tail and the M0 lane A completion record

**Branch:** `r7/wi-3-wall-glyphs` (the same branch as PR #80, carried on past the merge).
**Base:** `main`. Nothing executable.

Plan section 8 step 6 asks for a `MERGE` line in the progress log with the test count, and
the log committed alongside the work — but the merge and the post-merge confirmation of
`main` necessarily happen *after* the work-item PR has landed, so those lines cannot be in
it. This is the tail, and it carries the completion record with it.

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**81 passed, 0 failed, 0 skipped**, nothing deselected.

## What it records

- **WI-3 merged** as `ead97a7` (PR #80), with 81 passed at the moment of merge. `main`
  confirmed green afterwards by `git fetch origin && git merge origin/main` — which
  fast-forwarded `5324ec4..ead97a7` — and a full suite run on the branch.
- **`docs/completions/COMPLETION-M0-DEV-A.md` now covers both of lane A's M0 items, S-1
  and WI-3**, rather than being duplicated: the plan allows one completion record per lane
  per iteration. **M0 lane A is complete.**

It carries forward, so that none of it lives only in a PR body nobody reads twice:

- **two deviations** — S-1 committed no test (by the conductor's ruling, because WI-0 was
  creating the package layout in parallel), and WI-3's additive `ALL_WALL_GLYPHS`;
- **one contradiction** — **SCRN-3's colour has no owner.** Section 4 traces SCRN-3 to WI-3
  alone, but WI-3's own bar asks only about glyphs and section 7 gives WI-4 the whole field
  of glyph-and-colour. PR #80's body has the full argument and the two ways to settle it;
- **two things that need a human** — the "Python" Dock tile that appears during any test
  run that builds a Tk root, and whether Menlo's box-drawing ink actually spans the cell so
  a run of `═` reads as one unbroken line.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
