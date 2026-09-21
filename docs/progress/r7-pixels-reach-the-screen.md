# r7/pixels-reach-the-screen

06:15:40Z  START   a test that reads the screen, after the user found the game's window blank
06:15:40Z  READ    docs/IMPLEMENTATION_PLAN.md (human item 9), docs/findings/WI-17-human-verification.md
06:15:40Z  VERIFY  the plan's premise "no agent on this machine can capture the pixels" is FALSE -- four
                captures already taken today returned real window content, chrome and title text
06:15:40Z  VERIFY  a 20-line Tk control owing nothing to this project -- one #2121de rectangle on a black
                canvas -- photographs as 17195 of 17200 sampled pixels pure white. Tk 8.5.9 maps
                windows here and paints nothing. The blank game is not an application defect
06:15:40Z  NOTE    my own earlier probe read 698 glyphs back through itemcget and I reported the game was
                painting. That reads Tk's bookkeeping, not the framebuffer -- the same trap the whole
                suite is in
06:15:40Z  DECIDE  two tests, not one -> a control that owes nothing to the project, so which one fails
                says whether the fault is the toolkit or ours. Section 7: a guard needs a control
06:15:40Z  BLOCKED root.update() hung the first probe for two minutes -- the defect WI-5/WI-6 measured and
                the surface module bans. Capture from an after callback inside mainloop instead
06:15:40Z  NOTE    first draft created its own tkinter.Tk(); this build can crash on a second interpreter
                in one process, and it hung the run. Use the session tk_root and quit(), never destroy
06:15:40Z  TEST    986 passed, 10 deselected by default; needs_window: 10 passed, 2 failed as designed
