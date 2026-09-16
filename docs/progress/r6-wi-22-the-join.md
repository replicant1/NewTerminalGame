05:32:09Z  START   WI-22 build the frame/status join in Presentation, point four call sites at it
05:33:33Z  PLAN    add terminal_game/presentation/picture.py holding frame_for, then delegate the four call sites to it; a new test module owns the join only
05:33:36Z  WEIGH   where the join lives : inside WI-12 frame_composer.py, another lane landed file, vs a new presentation module of my own
05:33:39Z  DECIDE  where the join lives -> new module presentation/picture.py, because the sanctioned exception covers the four call sites only and a new file edits nobody elses landed work
05:34:13Z  NOTE    conductor says main moved to 238f4dd while I read; fast-forwarded my base, diff is docs only so the 740 baseline still stands
05:34:54Z  TEST    747 passed, 0 failed, 0 skipped  after the join landed and the four call sites were pointed at it
05:35:18Z  COMMIT  9db697c WI-22: the join - one Presentation function owns the whole picture
05:35:34Z  NOTE    draft PR 64 open, url ends pull/64
05:35:50Z  COMMIT  772aa30 WI-22: completion record and progress log
05:36:53Z  MERGE   PR 64 merged as 95d4b3b; origin/main brought back to the branch
05:36:56Z  TEST    747 passed, 0 failed, 0 skipped  on the branch with origin/main merged back in, after PR 64 landed
05:36:59Z  DONE    WI-22 r6/wi-22-the-join 95d4b3b
05:37:11Z  NOTE    three early lines never reached this file - two READs and the baseline TEST - because the brace-group append form I used silently wrote nothing. Not backfilled. Restating the lost measurement below with the time I am writing it, not the time I took it.
05:37:14Z  VERIFY  baseline before any edit, measured at about 05:33Z on main at 238f4dd -> 740 passed, 0 failed, 0 skipped
05:37:17Z  READ    restating what was read: IMPLEMENTATION_PLAN sections 1, 2, 3, 4 and WI-22 under amendment 10; the four call sites at the_look.py, scripted.py, window_manners.py, shell/game.py
05:38:01Z  TEST    747 passed, 0 failed, 0 skipped  on r6/wi-22a-close-the-log, a documents-only follow-up
