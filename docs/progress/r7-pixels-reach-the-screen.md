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
06:15:40Z  TEST    986 passed, 12 deselected by default; needs_window: 10 passed, 2 failed as designed
06:26:24Z  NOTE    Copilot: 4 findings, 3 mine. The capture blocked the loop that owns the watchdog, so a
                hung screencapture would have taken the test's only independent exit with it -- the
                exact thing the watchdog exists to prevent, defeated by the call it guards
06:26:24Z  NOTE    and the watchdog handle was never cancelled. These are booked on the SHARED interpreter
                and a pending after outlives the widget that scheduled it, so it would have fired in
                the middle of the next needs_window test and quit that test's loop. The game's own
                _on_window_closed exists for this exact fact and I did not apply it
06:26:24Z  DECIDE  disputed the fourth: "the blue a wall is drawn in" is idiomatic English, not a typo
06:26:24Z  VERIFY  ran -m needs_window twice in a row: 10 passed 2 failed both times, nothing left behind
06:26:24Z  TEST    986 passed, 0 failed, 12 deselected
06:33:30Z  NOTE    review round 1: 4 comments, all valid. The best of them: the control filled a RECTANGLE
                while the game's wall ink only ever arrives through create_text -- so on a build that
                can fill and cannot draw glyphs, the control would pass, the check would fail, and the
                pair would blame the application for a toolkit failing at the very primitive the check
                depends on. The control now draws glyphs
06:33:30Z  NOTE    and every capture failure became a skip, including "not on the screen", which IS the
                defect. A guard that skips itself whenever it is about to be useful. capture() now says
                whether a failure is the environment's, and only those skip
06:33:30Z  NOTE    third instance of the watchdog class: once() cancelled the watchdog on its first line,
                so the capture and the close -- the only two steps that can fail -- ran with no
                independent exit. Cancelled after mainloop returns now
06:33:30Z  DECIDE  WALL_BLUE derived from palette.WALL; a duplicated colour would fail this test on a
                palette edit with "the maze did not arrive on the screen"
06:33:30Z  RISK    blank()'s threshold and near()'s tolerance have never been exercised in the PASSING
                direction and cannot be until something here paints. Recorded in the module docstring:
                re-check both the first time either test goes green
06:33:30Z  TEST    986 passed, 0 failed, 12 deselected; needs_window 10 passed, 2 failed as designed
06:39:40Z  NOTE    review round 2: 3 comments. The second is my own round-1 fix creating a new defect --
                swapping the control's rectangle for box-drawing glyphs dropped its ink from 62% of
                the canvas to about 2%, which is blank()'s own threshold. The control could have
                failed on a Tk that draws correctly, which is the worst verdict this pair can give:
                it says "Tk cannot draw" about a Tk that can. Full blocks now, above by construction
06:39:40Z  DECIDE  the reviewer is right that half the docstring's claim was false -- blank() and near()
                are pure functions of a colour count and can be exercised today with no screen. Only
                "are 0.98 and 24 right for a real maze" is genuinely open
06:39:40Z  VERIFY  wrote tests/test_pixels.py, twelve tests, default suite. They failed on first run and
                found a real defect: histogram stopped at len(data) - step and never read the last
                pixel. A census of four pixels returned three. Both verdicts rest on that function
                and the reviewer had flagged it as untested without making it a condition
06:39:40Z  TEST    998 passed, 0 failed, 12 deselected; needs_window 10 passed, 2 failed as designed
