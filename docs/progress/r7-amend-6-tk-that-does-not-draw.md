# r7/amend-6-tk-that-does-not-draw

10:15:00Z  START   AMEND-6: the user asked for all the tests, including the ones pytest.ini excludes.
                1017 passed / 12 deselected, then 10 passed / 2 FAILED on -m needs_window. Both
                failures in test_pixels_reach_the_screen.py, the only two tests that read the screen
10:18:00Z  VERIFY  the CONTROL failed -- plain Tk, block glyphs, no project code in it. Its docstring
                says nothing below it means anything if it does, so the game was never the suspect
10:22:00Z  VERIFY  reduced away from the suite: a Toplevel with a #ff0000 canvas, lift + topmost +
                focus_force, photographed at 1s / 3s / 6s -> red=0 at all three, identical histograms
                to the pixel count. A full-screen capture at the same moment shows the window IS
                there, correctly placed and stacked, with a white interior. Tk maps it and paints
                nothing into it
10:25:00Z  VERIFY  ruled out the three alternatives rather than assuming them: screencapture
                photographs every OTHER application's windows (26,368 distinct colours in the same
                shot); there is ONE display, so tests/pixels.py's secondary-display hazard is not
                it; and 6 seconds across three captures inside a running loop give the same answer
10:27:00Z  NOTE    every other window test passes on a toolkit that draws nothing -- ten of the twelve
                assert what Tk was TOLD. This is the gap tests/pixels.py was written for, catching a
                second and larger instance of itself. The first was an application defect; this one
                is the toolkit, and no application code could have been written to pass it
10:31:00Z  DECIDE  the third option nobody costed -> `brew install python-tk@3.14` brings tcl-tk 9.0.4
                to the interpreter section 1.2 rejected for having no _tkinter at all. Same red probe
                on it: red=9009. Section 1.2's measurement was right and its conclusion was not
10:34:00Z  VERIFY  put the question to the user before installing anything, since it is human item 5 --
                closed by S-1 on 2026-09-17 and reopened by this. Answered: yes
10:41:00Z  VERIFY  re-ran S-1 section 6's scan VERBATIM on Tk 9.0.4, all 91 glyphs, sizes 8 to 36.
                Tk 8.5.9 took a point as a pixel; 9.0.4 applies the 96/72 a point is owed, so every
                nominal size is 4/3 larger and S-1's size-16 cell is now asked for as size 12
10:43:00Z  VERIFY  Menlo 12 on Tk 9.0.4 -> advance 10, linespace 19, window 400x570, bboxes [-1,0,11,19]
                and [9,0,21,19], 37-char row = 370. Every one identical to S-1's reading of Menlo 16.
                All 91 glyphs uniform, all report family Menlo, measure(g*40) == 40*measure(g) for all
10:44:00Z  VERIFY  the non-vacuity controls still differ, which is what stops the family check passing
                by accident: Devanagari KA -> Kohinoor 13, CJK -> PingFang 17, Tamil -> Sangam 24, and
                U+E000 still Menlo and still 18, caught by advance and not by family
10:46:00Z  DECIDE  FONT_SIZE 16 -> 12 and EXACT_GRID_CEILING 16 -> 12, because 12 is where the exact
                grid now ends: drift 4 to 38 px over 40 cells at every size from 13 to 36
10:47:00Z  NOTE    human item 3 (is the type comfortable) survives untouched -- the window is the same
                400x570 rectangle of the same 10x19 cell. FONT_SIZE is a number in the toolkit's
                units, not a size on the glass, and only the second was ever put to a person
10:52:00Z  VERIFY  re-measured two other claims the move could have stranded. root.update() RETURNS on
                a mapped Tk 9.0.4 window -- the S-2 hang was a Tk 8.5 defect. Kept the prohibition
                anyway (every repaint path is update_idletasks, which was never the problem) and
                annotated the claim so it is not read as current
10:53:00Z  VERIFY  the repaint cost surface.py records, re-read on the new toolkit: 6.3 ms for all 1200
                cells and 0.154 ms for a move's dozen, against 7.3 and 0.092 on Tk 8.5.9 and a 143 ms
                budget. Same order, same conclusion, both columns now in the scenario doc
10:56:00Z  VERIFY  ran the game and photographed it: blue maze, dots, player, status line, all drawing
10:57:00Z  TEST    1017 passed, 12 deselected; 12 passed on -m needs_window; 1029 passed with both
11:04:00Z  NOTE    review round 1, Copilot: 4 findings, 1 high 2 medium 1 low. Three valid and fixed
                -- the reviewer agent's setup block grew the venv command and not the brew formula
                that makes it work; README's later 3.9 section still said "the interpreter is 3.9",
                which my sweep missed by searching for 3.9.6; and the 3.9 syntax wall, which it was
                right that documenting the loss is not the same as accepting it
11:06:00Z  DECIDE  rebuild the wall with ast.parse(feature_version=(3,9)) rather than a 3.9 subprocess
                -> no second interpreter to depend on, and it is CPython's own parser. Syntax only,
                said in the test: functools.cache is an attribute access and no parser sees it
11:08:00Z  VERIFY  put a match statement in palette.py and the sweep failed naming the file and line
11:12:00Z  DISPUTE the fourth asked to pin Tk's patch version. Declined: a version string is a proxy
                for a measurement this project already takes, and 9.0.5 would fail the pin while
                measuring identically
11:14:00Z  VERIFY  the finding UNDER it is real and worse. exact_cell_grid() returns
                size <= EXACT_GRID_CEILING -- two constants, one set from the other, and it cannot
                fail while both are wrong. S-1 section 7 asked for the real measurement and nothing
                built it, so the ceiling moved 16 -> 12 in this PR on one scan with nothing standing
11:16:00Z  VERIFY  the measurement exists now and was proved able to fail: FONT_SIZE = 13 drifts all
                20 glyphs at 410 != 40 x 11, and the control asserts one size above the ceiling is
                NOT exact, so the ceiling is an edge and not a number we chose
11:18:00Z  TEST    1023 passed, 12 deselected; 12 on the marker; 1035 with both
