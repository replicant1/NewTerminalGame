# r7/pixels-tidy

06:46:25Z  START   the four observations the PIXELS round 3 reviewer recorded without making them conditions
06:46:25Z  NOTE    it approved #115 and said explicitly not to resubmit for these, so they come as their own
                change rather than as a fourth round on a valid approval
06:46:25Z  DECIDE  rated LOW -> four cosmetic items in test code, visible and local; section 1.9 says LOW
                merges on Copilot and a green suite, without the code reviewer. First LOW in this run
06:46:25Z  NOTE    the reviewer asked to be overruled on the first of them and it was right to: a failure
                message saying "box-drawing glyphs" about U+2588 is the same stale-description class it
                did raise in round 2
06:46:25Z  TEST    999 passed, 0 failed, 12 deselected
07:08:17Z  NOTE    Copilot: my boundary test passed threshold=0.98 explicitly, so it pinned a number the
                test supplied rather than the default the screen checks run on. Both assertions would
                go on passing after the default changed, while the summary claimed this guarded the
                boundary -- the hollow assertion this project has a rule about, written into the test
                that exists to close a gap
07:08:17Z  DECIDE  omit the keyword, as TestNear already does, and say in the docstring why
07:08:17Z  TEST    999 passed, 0 failed, 12 deselected
