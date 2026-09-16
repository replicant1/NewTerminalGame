05:41:39Z  START   WI-22a rewrite two re-deriving assertions against frame_for, and unstale the presentation package docstring
05:41:59Z  TEST    747 passed, 0 failed, 0 skipped  baseline on r6/wi-22a-join-assertions, main at b11a8a6
05:42:21Z  READ    amendment 11 in the plan, section 4 rule "a duplicate assertion is not a redundant test", and both tests as they stand
05:43:06Z  TEST    747 passed, 0 failed, 0 skipped  after both assertions were rewritten against frame_for and the package docstring unstaled
05:43:18Z  VERIFY  grep for compose_frame paired with status_row over a state -> one hit, picture.py line 71. No test re-derives the join any more.
