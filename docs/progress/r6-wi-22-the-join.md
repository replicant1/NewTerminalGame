05:32:09Z  START   WI-22 build the frame/status join in Presentation, point four call sites at it
05:33:33Z  PLAN    add terminal_game/presentation/picture.py holding frame_for, then delegate the four call sites to it; a new test module owns the join only
05:33:36Z  WEIGH   where the join lives : inside WI-12 frame_composer.py, another lane landed file, vs a new presentation module of my own
05:33:39Z  DECIDE  where the join lives -> new module presentation/picture.py, because the sanctioned exception covers the four call sites only and a new file edits nobody elses landed work
05:34:13Z  NOTE    conductor says main moved to 238f4dd while I read; fast-forwarded my base, diff is docs only so the 740 baseline still stands
05:34:54Z  TEST    747 passed, 0 failed, 0 skipped  after the join landed and the four call sites were pointed at it
