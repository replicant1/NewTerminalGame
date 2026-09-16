05:41:39Z  START   WI-22a rewrite two re-deriving assertions against frame_for, and unstale the presentation package docstring
05:41:59Z  TEST    747 passed, 0 failed, 0 skipped  baseline on r6/wi-22a-join-assertions, main at b11a8a6
05:42:21Z  READ    amendment 11 in the plan, section 4 rule "a duplicate assertion is not a redundant test", and both tests as they stand
05:43:06Z  TEST    747 passed, 0 failed, 0 skipped  after both assertions were rewritten against frame_for and the package docstring unstaled
05:43:18Z  VERIFY  grep for compose_frame paired with status_row over a state -> one hit, picture.py line 71. No test re-derives the join any more.
05:43:39Z  COMMIT  69b862f WI-22a: rewrite the two assertions that re-derived the join
05:43:53Z  NOTE    draft PR 67 open, url ends pull/67
05:45:06Z  MERGE   PR 67 merged as 07fb9a7; WI-21 PR 66 landed beside it as 03d0913
05:45:09Z  TEST    796 passed, 0 failed, 0 skipped  on the branch with origin/main merged back in - 747 of mine plus 49 that arrived with WI-21
05:45:12Z  DONE    WI-22a r6/wi-22a-join-assertions 07fb9a7
05:46:12Z  NOTE    I first wrote this closing PR doc to docs/prs/PR-WI-22a-close-the-log.md, which already existed from PR 65 and was silently overwritten. Restored from origin/main and the new one renamed to PR-WI-22a-close-assertions-log.md before anything was pushed.
