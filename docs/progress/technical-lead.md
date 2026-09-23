02:05:44Z  START   technical lead, run 8: plan for candidate 2, 3 developers (lanes A-C), real pull requests
02:05:44Z  READ    docs/FUNCTIONAL_REQUIREMENTS.md (49 codes)
02:05:44Z  READ    docs/ARCHITECTURE.md (candidates 1 and 2, assumptions A1-A6, cautions C1-C7, section 8)
02:05:44Z  READ    .claude/agents/developer.md (brief format, verifier-status block, five document paths)
02:05:44Z  READ    .claude/shared/progress-tracking.md
02:11:48Z  READ    .claude/agents/verifier.md (amendment checks AMEND/1-4; venv built with /usr/bin/python3)
02:11:48Z  READ    .claude/shared/ask-a-human.md, docs/AGENTS-SETUP.md, .gitignore (already names .venv and the suite command)
02:11:48Z  VERIFY  /opt/homebrew/bin/python3.14 -> CPython 3.14.7, tkinter TkVersion 9.0 (my measurement, 02:06Z)
02:11:48Z  VERIFY  /usr/bin/python3 -> CPython 3.9.6, TkVersion 8.5 (Apple's deprecated system Tk) (my measurement, 02:06Z)
02:11:48Z  VERIFY  a fresh 3.14 venv installs pytest 9.1.1; existing suite on it: 36 passed, 1 skipped (02:06Z)
02:11:48Z  VERIFY  git worktree list -> primary tree holds [main]; no merge by me in non-local mode, so not BLOCKED; developers merge server-side
02:11:48Z  VERIFY  git ls-files at 099b803 -> no docs/findings/ at all; WI-17-human-verification.md and AMEND-2/AMEND-6 findings cited by developer.md/verifier.md are absent
02:11:48Z  DECIDE  architecture -> candidate 2, single-process windowed character grid, because the user chose it (relayed by the conductor); not re-deliberated
02:11:48Z  WEIGH   runtime : /usr/bin/python3 3.9.6 + Tk 8.5 | /opt/homebrew/bin/python3.14 3.14.7 + Tk 9.0
02:11:48Z  DECIDE  runtime -> CPython 3.14 at /opt/homebrew/bin/python3.14 with Tk 9.0 in a project .venv, because Apple's Tk 8.5 is deprecated and the toolkit painting is the riskiest part of candidate 2
02:11:48Z  RISK    Homebrew python3.14 could lose _tkinter again (it lacked it on 17 Sep); cost: every desktop claim unprovable. Mitigation: WI-1/C2 makes the suite name the wrong interpreter plainly
02:11:48Z  CONTRADICT verifier.md builds its venv with /usr/bin/python3 -> the plan pins 3.14 (VERIFY above); the verifier must use the plan's venv command, which the conductor must relay
02:11:48Z  CONTRADICT ARCHITECTURE.md candidate 2 diagram draws Session Controller -> Frame Composer and Status Line Renderer -> contradicts its own rule Presentation -> Application -> Domain; the plan puts the shell on top and keeps application free of presentation imports
02:11:48Z  CONTRADICT ARCHITECTURE.md section 5 'Reversed during implementation' cites terminal_game/shell/grid_surface.py and three tests -> none exist on main at 099b803 (git ls-files); it is run 7's code and binds nothing here
02:11:48Z  CONTRADICT developer.md cites docs/findings/WI-17-human-verification.md as the needs-eyes model -> absent at 099b803; the plan gives the script shape itself
02:12:03Z  ASK     Q1 (arch A1/section 8): does the titlebar of the running window read exactly 'Terminal Game'?
02:12:03Z  ASSUME  candidate 2 sets the title directly, so a toolkit read-back is the machine claim (WI-3/C6) and the user glances at the titlebar under WI-3/C16 (needs eyes); a bad answer changes only WI-3
02:12:03Z  ASK     Q2 (arch A3): WIN-5 against END-5/END-6: does the window close the moment the outcome is decided, or when the player presses q after seeing it?
02:12:03Z  ASSUME  A3 reading, as run 7: outcome decided -> final picture stays -> q -> window closes itself and process exits. Rests on it: WI-12/C4-C6, WI-13/C5-C7. Flipping it is a small change to WI-12 and WI-13 claims
02:12:03Z  ASK     Q3 (arch A4/A5): is the chosen font size comfortable? (a terminal profile no longer arises: candidate 2 owns its window)
02:12:03Z  ASSUME  the developer of WI-3 picks a fixed point size; the user judges it under WI-3/C15 (needs eyes); a bad answer changes one constant
02:12:03Z  ASK     is the status line's leading blank in the specimen (' score 0    arrows, q quits') intended, and does it apply to the CAUGHT/CLEARED lines too?
02:12:03Z  ASSUME  the specimen is normative (arch A6): one leading blank on all three status forms; rests on WI-5/C1-C3 and WI-13/C1, C5, C6 only
02:12:03Z  ASK     END-3: when the last dot is on the ghost's square, is that dot eaten (score +1) before the loss, or not?
02:12:03Z  ASSUME  'meeting the ghost is decided first' -> the move ends the game at the collision and the dot is not eaten; the final score excludes it. Rests on WI-11/C9 only
02:12:03Z  ASK     START-1/START-2: are distances measured in grid squares or on screen (a square is two columns wide)?
02:12:03Z  ASSUME  straight-line distance in grid squares, not screen cells; rests on WI-7/C1-C2 only
02:12:03Z  ASK     WIN-4: 'whatever window the player was last looking at' in any application, or the terminal's front window (arch A2)?
02:12:03Z  ASSUME  the window that was frontmost at start-up, in any application, found without any permission prompt; started from Terminal this is the Terminal window. Rests on WI-9 and WI-13/C8, C13
02:12:30Z  DECIDE  layer rule -> shell (only place tkinter or platform APIs appear) -> presentation -> application -> domain, downward only, because it removes the architecture's session->composer cycle and keeps F4/F5 testable
02:12:30Z  DECIDE  desktop tests -> opt-in by a marker, default suite opens no window, because a person is at that desktop and F5 requires it
02:12:30Z  WEIGH   iteration shape : one early integration HIGH item plus a final one | a single final integration with WI-3 painting the specimen as its end-to-end proof
02:12:30Z  DECIDE  iteration shape -> WI-3 proves the medium end to end in M1 (window, paint, keys, timer, close) with the specimen as test card; one final assembly WI-13, because each window-opening item is HIGH and brings the user
02:12:30Z  DECIDE  HIGH items -> WI-3 and WI-13 only (2 of 13); needs-eyes claims only on those two, so no extra user visits
02:12:30Z  DRAFT   docs/IMPLEMENTATION_PLAN.md section 1 (ground rules, runtime, layer rule, 1.9 tier table)
02:16:08Z  VERIFY  scripted check of the specimen (scratchpad spec_check.py): WI-4/C1 glyph table + joining-cell rule reproduce every wall square and joining cell of the specimen, 0 mismatches; rows 37 wide, cols 38-39 blank
02:16:08Z  VERIFY  specimen: 264 corridor squares, 262 dots shown (player square empty, ghost square hides one); no dead ends; no 2x2 corridor block; status row ' score 0    arrows, q quits'
02:16:08Z  VERIFY  specimen: centre (9,14) is wall; nearest corridor squares are (9,13) and (9,15) at 1.0, but the player is drawn at (10,13), 1.41 away; the ghost at (1,27) IS the furthest square from (10,13) (16.64)
02:16:08Z  CONTRADICT the specimen picture places the player at grid (10,13), which is not the corridor square nearest the centre (START-1): (9,13) and (9,15) are nearer -> scripted measurement above. The requirement text governs start positions; the specimen governs only the drawing (arch A6)
02:16:32Z  DRAFT   docs/IMPLEMENTATION_PLAN.md sections 2-7 (iterations, gantt, 13 work items with claims, dependencies, dispatch, traceability, risks)
02:16:32Z  ITEM    WI-1 Project scaffold and the layer guard (0.5d, risk MEDIUM, depends on nothing)
02:16:32Z  ITEM    WI-2 Maze generation (2.0d, risk MEDIUM, depends on nothing (merge `main` once WI-1 lands, before requesting verification))
02:16:32Z  ITEM    WI-3 Window and character grid (2.5d, risk HIGH, depends on nothing (merge `main` once WI-1 lands, before requesting verification))
02:16:32Z  ITEM    WI-4 Wall glyphs (0.5d, risk LOW, depends on WI-1)
02:16:32Z  ITEM    WI-5 Status line (0.5d, risk LOW, depends on WI-1)
02:16:32Z  ITEM    WI-6 Input translation (0.5d, risk LOW, depends on WI-1)
02:16:32Z  ITEM    WI-7 Game setup (1.0d, risk MEDIUM, depends on WI-2)
02:16:32Z  ITEM    WI-8 Ghost movement policy (1.0d, risk MEDIUM, depends on WI-2)
02:16:32Z  ITEM    WI-9 Anchor and placement (1.0d, risk MEDIUM, depends on nothing)
02:16:32Z  ITEM    WI-10 Frame composer (1.5d, risk MEDIUM, depends on WI-2, WI-4, WI-5)
02:16:32Z  ITEM    WI-11 Turn resolution (1.5d, risk MEDIUM, depends on WI-7)
02:16:32Z  ITEM    WI-12 Session control (1.5d, risk MEDIUM, depends on WI-6, WI-8, WI-11)
02:16:32Z  ITEM    WI-13 Application assembly (1.5d, risk HIGH, depends on WI-3, WI-9, WI-10, WI-12)
02:16:32Z  CLAIM   WI-1/C1 Following the README's setup steps in a fresh clone, with the pinned interpreter, gives an environment in which the default suite command runs and reports the existing infrastructure tests passing.
02:16:32Z  CLAIM   WI-1/C2 Run under any interpreter other than the pinned one, or under one without a working Tk 9, the suite says so plainly, naming the interpreter and Tk it found and the ones it wants, instead of passing or failing for some unrelated reason.
02:16:32Z  CLAIM   WI-1/C3 The layer check reports every import that breaks the layer rule of §1.4: given a sample tree containing such an import, it names the importing module and what it imported; on the real tree it reports none.
02:16:32Z  CLAIM   WI-1/C4 The layer check cannot pass vacuously: it reports how many modules it examined in each layer, and fails when it examines no module in a layer the tree declares.
02:16:32Z  CLAIM   WI-1/C5 A test marked as a desktop test is not run by the default suite command and is run by the desktop command.
02:16:32Z  CLAIM   WI-1/C6 A test that would create a toolkit window without the desktop mark fails, naming the test, instead of opening a window.
02:16:32Z  CLAIM   WI-2/C1 Every generated maze is 19 grid squares across and 29 deep, and every square is either wall or corridor.
02:16:32Z  CLAIM   WI-2/C2 Over at least 1,000 mazes from distinct seeds, every square of the outer ring is wall, so nothing can leave the maze and there are no tunnels through the sides.
02:16:32Z  CLAIM   WI-2/C3 Over the same mazes, every corridor square has at least two corridor neighbours among north, south, east and west: there are no dead ends.
02:16:32Z  CLAIM   WI-2/C4 Over the same mazes, every corridor square can be reached from every other corridor square by steps north, south, east and west.
02:16:32Z  CLAIM   WI-2/C5 Over the same mazes, corridors are one square wide: no 2 × 2 block of squares is all corridor.
02:16:32Z  CLAIM   WI-2/C6 The same seed always gives the same maze, and 1,000 distinct seeds give 1,000 distinct mazes.
02:16:32Z  CLAIM   WI-2/C7 Generation always finishes: over the same 1,000 seeds, no maze takes longer than one second to generate.
02:16:32Z  CLAIM   WI-3/C1 Started from a terminal, the program opens exactly one new window of its own, and writes nothing to the terminal it was started from during a normal session.
02:16:32Z  CLAIM   WI-3/C2 The window's drawing area is exactly 40 cells wide and 30 cells deep for the fixed-width typeface in use, with no extra margin, measured in the real window.
02:16:32Z  CLAIM   WI-3/C3 The person cannot resize the window: after an attempt to resize it, the drawing area is still exactly 40 × 30 cells.
02:16:32Z  CLAIM   WI-3/C4 If the preferred typeface is not available, the window uses another fixed-width typeface and still measures exactly 40 × 30 of that typeface's cells.
02:16:32Z  CLAIM   WI-3/C5 The whole drawing area is black wherever nothing is painted, including the two right-hand columns.
02:16:32Z  CLAIM   WI-3/C6 The window's title, as the toolkit reports it, is exactly `Terminal Game`.
02:16:32Z  CLAIM   WI-3/C7 Any character can be painted in any of the 1,200 cells in any of the six colour roles, and a screenshot of the real window shows each painted character inside its own cell in its role's colour.
02:16:32Z  CLAIM   WI-3/C8 Only characters are drawn: everything on the drawing surface is text or the black background, never an image or a shape standing in for a glyph.
02:16:32Z  CLAIM   WI-3/C9 Replacing one frame with another never shows a picture that is neither: over 5 seconds of repeated repaints, every screenshot matches, cell for cell, one of the frames that was asked for, and no text cursor or caret is visible in any of them.
02:16:32Z  CLAIM   WI-3/C10 Keys pressed in the window reach the program as named keys (the four arrows, `q`, `Q`, and any other key as itself), and nothing typed ever appears in the window.
02:16:32Z  CLAIM   WI-3/C11 A repeating tick is delivered between 6.5 and 7.5 times a second, measured over 5 seconds with no key pressed, and again over 5 seconds while keys are pressed as fast as a script can send them.
02:16:32Z  CLAIM   WI-3/C12 When the program ends the session, its window closes by itself and the process exits with status 0 within one second, leaving no window and no process behind.
02:16:32Z  CLAIM   WI-3/C13 Closing the window with its title-bar close button, or quitting from the application menu, ends the process in the same way, leaving no window, no process and no dialog.
02:16:32Z  CLAIM   WI-3/C14 If a key or tick handler raises an error, the window still closes and the process exits with a non-zero status and prints the error, instead of leaving a frozen window.
02:16:32Z  CLAIM   WI-3/C15 At the chosen type size, a person at a normal seat can read the characters comfortably and can tell the double-line, block and dot characters apart. — needs eyes
02:16:32Z  CLAIM   WI-3/C16 The window's title bar shows exactly "Terminal Game" and nothing else. — needs eyes
02:16:32Z  CLAIM   WI-3/C17 The default suite command opens no window, while the desktop command runs this item's window tests.
02:16:32Z  CLAIM   WI-4/C1 A wall square gets its character from which of its north, south, east and west neighbours are wall, for all 16 combinations: none `■`; east and/or west only `═`; north and/or south only `║`; south+east `╔`; south+west `╗`; north+east `╚`; north+west `╝`; north+south+east `╠`; north+south+west `╣`; east+west+south `╦`; east+west+north `╩`; all four `╬`.
02:16:32Z  CLAIM   WI-4/C2 The cell between two horizontally adjacent grid squares shows `═` when both squares are wall, and is blank otherwise.
02:16:32Z  CLAIM   WI-4/C3 A square beyond the edge of the grid counts as not wall, so the four corners of the outer wall come out `╔`, `╗`, `╚` and `╝`.
02:16:32Z  CLAIM   WI-4/C4 Applied to the maze in the specimen picture (`docs/FUNCTIONAL_REQUIREMENTS.md` §3), every wall square and every joining cell comes out exactly as the specimen shows it.
02:16:32Z  CLAIM   WI-5/C1 During play with a score of 0 the row reads exactly ` score 0    arrows, q quits`, followed by blanks to 40 cells.
02:16:32Z  CLAIM   WI-5/C2 On a loss with a score of 37 the row reads exactly ` CAUGHT  score 37   q quits`, and on a win with a score of 274 exactly ` CLEARED  score 274  q quits`, each followed by blanks to 40 cells.
02:16:32Z  CLAIM   WI-5/C3 For every score from 0 to 459 in each of the three states, the row is exactly 40 cells, shows the score in decimal, and the text after the score starts in the same cell as it does in the C1 and C2 examples for that state.
02:16:32Z  CLAIM   WI-5/C4 The row contains the state word (on an ending), the score and the key hints, and no other text.
02:16:32Z  CLAIM   WI-5/C5 Every cell of the row is in the status colour.
02:16:32Z  CLAIM   WI-6/C1 The up, down, left and right arrow keys translate to moves up, down, left and right respectively.
02:16:32Z  CLAIM   WI-6/C2 `q` and `Q` both translate to quit, including `Q` typed with Caps Lock on.
02:16:32Z  CLAIM   WI-6/C3 Every other key, including letters, digits, space, Return, Escape, Tab, Backspace, function keys and a modifier pressed alone, translates to nothing.
02:16:32Z  CLAIM   WI-7/C1 The player starts on the corridor square nearest the centre square (column 9, row 14, counting from 0), by straight-line distance in grid squares. When several are equally near, the same maze always gives the same one.
02:16:32Z  CLAIM   WI-7/C2 The ghost starts on the corridor square furthest from the player's start by straight-line distance in grid squares, not by distance along the corridors. This is shown on a hand-built maze where the two measures pick different squares.
02:16:32Z  CLAIM   WI-7/C3 When the centre square is itself corridor, the player starts on it.
02:16:32Z  CLAIM   WI-7/C4 Every corridor square holds one dot except the player's start square, which holds none, and no wall square holds a dot.
02:16:32Z  CLAIM   WI-7/C5 The ghost's start square holds a dot.
02:16:32Z  CLAIM   WI-7/C6 The score starts at zero and no outcome is decided.
02:16:32Z  CLAIM   WI-7/C7 Over 1,000 generated mazes, the player and the ghost never start on the same square, and neither starts on a wall.
02:16:32Z  CLAIM   WI-8/C1 While the square ahead in its current heading is corridor, the ghost's next square is that square, at junctions as well as along corridors.
02:16:32Z  CLAIM   WI-8/C2 When the square ahead is wall, the ghost moves to one of its other open neighbours, excluding the square it came from, chosen at random: over 10,000 trials at a square with two such exits, each is chosen at least 40% of the time.
02:16:32Z  CLAIM   WI-8/C3 The ghost turns back the way it came only when no other way is open, shown on a hand-built maze with a dead end.
02:16:32Z  CLAIM   WI-8/C4 The ghost's next square never depends on where the player is: for the same maze, ghost square, heading and random sequence, it is the same wherever the player stands.
02:16:32Z  CLAIM   WI-8/C5 The ghost only ever moves exactly one square north, south, east or west, and never onto a wall.
02:16:32Z  CLAIM   WI-8/C6 On its first move, having no heading yet, the ghost moves to one of its open neighbours.
02:16:32Z  CLAIM   WI-8/C7 A ghost move never changes the dots: every dot present before it is present after it, including the dot on the square the ghost moves onto.
02:16:32Z  CLAIM   WI-8/C8 Over 1,000 generated mazes and 1,000 moves in each, the ghost moves on every move and is never stuck.
02:16:32Z  CLAIM   WI-9/C1 The game window's top-left corner is placed a little below and to the right of the anchor's top-left corner: a fixed offset of between 20 and 60 points in each direction.
02:16:32Z  CLAIM   WI-9/C2 If that position would put any part of the game window off the visible screen, the window is moved just far enough to lie wholly on it.
02:16:32Z  CLAIM   WI-9/C3 If no anchor can be found (no window on screen, or the query fails), the window is placed wholly on the visible screen at a default position, and start-up carries on.
02:16:32Z  CLAIM   WI-9/C4 When the anchor is on a second display, the game window lands on that same display, wholly visible.
02:16:32Z  CLAIM   WI-9/C5 Finding the anchor finishes within 500 milliseconds, or gives up and falls back as in C3.
02:16:32Z  CLAIM   WI-9/C6 Run from a Terminal window on the real desktop, finding the anchor returns that Terminal window's position and size, matching what Terminal itself reports for its front window.
02:16:32Z  CLAIM   WI-10/C1 Given the specimen's maze, dots, player and ghost squares and a score of 0, the composed frame reproduces the specimen picture in `docs/FUNCTIONAL_REQUIREMENTS.md` §3 character for character, all 30 rows, ignoring the `← …` annotations.
02:16:32Z  CLAIM   WI-10/C2 The frame is 40 cells by 30 rows. Rows 0 to 28 hold the maze, and row 29 is exactly the status line WI-5 gives for the same score and outcome. Nothing from the maze is ever drawn on row 29.
02:16:32Z  CLAIM   WI-10/C3 Each grid square occupies two cells, its own and the joining cell to its east, so the 19 squares span cells 0 to 37 and cells 38 and 39 are blank on every maze row.
02:16:32Z  CLAIM   WI-10/C4 A corridor square holding a dot shows `▪` in the dot colour. A corridor square without one shows blank.
02:16:32Z  CLAIM   WI-10/C5 The player is drawn as `▐█▌` in the player colour and the ghost as `▗█▖` in the ghost colour, centred on their squares, so the two differ in colour and in outline.
02:16:32Z  CLAIM   WI-10/C6 When the player and the ghost stand on the same square, the ghost is drawn and the player cannot be seen.
02:16:32Z  CLAIM   WI-10/C7 While the ghost stands on a square with a dot, the dot is hidden. Once the ghost moves off, it is drawn again.
02:16:32Z  CLAIM   WI-10/C8 When the player and the ghost stand on horizontally adjacent squares, both centre blocks `█` are drawn, each in its own colour.
02:16:32Z  CLAIM   WI-10/C9 Every wall character is in the wall colour, every dot in the dot colour, the status row in the status colour, and every blank cell has the background colour.
02:16:32Z  CLAIM   WI-10/C10 Composing a frame changes nothing: composing twice from the same state gives identical frames, and the state is unchanged.
02:16:32Z  CLAIM   WI-11/C1 A move towards a corridor square moves the player exactly one square in that direction.
02:16:32Z  CLAIM   WI-11/C2 A move towards a wall changes nothing at all: the player's square, the dots, the score and the outcome are identical afterwards.
02:16:32Z  CLAIM   WI-11/C3 Moving onto a square that holds a dot removes that dot for the rest of the game and adds exactly one to the score.
02:16:32Z  CLAIM   WI-11/C4 Moving onto a square whose dot has already been eaten, including the start square, adds nothing to the score.
02:16:32Z  CLAIM   WI-11/C5 Over 1,000 games of random moves and ghost steps, the score never goes down.
02:16:32Z  CLAIM   WI-11/C6 The player walking onto the ghost's square loses the game.
02:16:32Z  CLAIM   WI-11/C7 The ghost stepping onto the player's square loses the game.
02:16:32Z  CLAIM   WI-11/C8 Eating the last dot wins the game.
02:16:32Z  CLAIM   WI-11/C9 Walking onto the ghost's square when it holds the last dot loses the game, not wins it. That dot is not eaten, and the score stays what it was before the move.
02:16:32Z  CLAIM   WI-11/C10 From adjacent squares, the player and the ghost can never pass through each other: a player move towards the ghost, or a ghost step towards the player, loses the game on that step.
02:16:32Z  CLAIM   WI-11/C11 Over 1,000 games of 1,000 random moves each, the player never stands on a wall and never leaves the maze.
02:16:32Z  CLAIM   WI-12/C1 A new session is already playing: the first tick moves the ghost, with no key pressed.
02:16:32Z  CLAIM   WI-12/C2 While playing, each tick moves the ghost exactly one square, and key presses between ticks neither add ghost moves nor remove them.
02:16:32Z  CLAIM   WI-12/C3 Each arrow key press moves the player at most one square, and with no key presses the player never moves, however many ticks pass.
02:16:32Z  CLAIM   WI-12/C4 Once the game is won or lost, ticks no longer move the ghost, arrow keys no longer move the player, and the state the shell would paint no longer changes.
02:16:32Z  CLAIM   WI-12/C5 `q` or `Q` ends the session at once, both while playing and after the game is decided.
02:16:32Z  CLAIM   WI-12/C6 After the game is decided, quit is the only input that has any effect.
02:16:32Z  CLAIM   WI-12/C7 An arrow key that arrives immediately after the tick in which the ghost catches the player does not move the player.
02:16:32Z  CLAIM   WI-12/C8 Nothing leads back from an ending: no sequence of inputs starts a new game, restores the player or resumes play.
02:16:32Z  CLAIM   WI-12/C9 Given the same maze, the same random source and the same sequence of ticks and keys, two sessions end in identical states.
02:16:32Z  CLAIM   WI-12/C10 A tick or a key that arrives after the session has ended is ignored without error.
02:16:32Z  CLAIM   WI-13/C1 The README's one command, run from a Terminal window, opens the game window showing a fresh maze, the player, the ghost and ` score 0    arrows, q quits`, and the ghost is moving within half a second with no key pressed.
02:16:32Z  CLAIM   WI-13/C2 Two launches in a row show different mazes.
02:16:32Z  CLAIM   WI-13/C3 In the real window, with no key pressed, the ghost moves between 32 and 38 squares in 5 seconds.
02:16:32Z  CLAIM   WI-13/C4 In the real window, one arrow key press moves the player one square onto a dot, the dot disappears, and the status line's score goes up by one, shown by screenshots before and after.
02:16:32Z  CLAIM   WI-13/C5 Played to a loss in the real window, the final picture shows the ghost over the player and ` CAUGHT  score N   q quits` with the right N, and it stays unchanged for at least 3 seconds while ticks pass and arrow keys are pressed.
02:16:32Z  CLAIM   WI-13/C6 Played to a win in the real window, the final picture shows ` CLEARED  score N  q quits` with N equal to the number of dots the maze started with, and it stays unchanged until `q`.
02:16:32Z  CLAIM   WI-13/C7 Pressing `q` or `Q`, during play and after an ending, closes the window and ends the process within one second, leaving no window, no process and no dialog.
02:16:32Z  CLAIM   WI-13/C8 The window opens a little below and to the right of the Terminal window it was started from, wholly on the visible screen, at the right place on a Retina display (not at half or double the intended position).
02:16:32Z  CLAIM   WI-13/C9 A screenshot of the real window shows walls in the wall colour, dots in the dot colour, the player in the player colour, the ghost in the ghost colour, the status line in the status colour and the background black, and the dots are dimmer than the player.
02:16:32Z  CLAIM   WI-13/C10 The default suite command opens no window, and the layer check (WI-1/C3, C4) passes on the finished tree with modules examined in every layer.
02:16:32Z  CLAIM   WI-13/C11 Seen in play, the walls join into corners, tees and crossings like the specimen picture, with no gaps or misaligned pieces between neighbouring characters, and a lone wall square shows as a single block. — needs eyes
02:16:32Z  CLAIM   WI-13/C12 Seen in play, the picture changes without flicker, the ghost moves at a steady pace, and no text cursor is visible. — needs eyes
02:16:32Z  CLAIM   WI-13/C13 Started from a Terminal window, the game window appears a little below and to the right of it, and no permission or consent dialog appears at any point. — needs eyes
02:16:32Z  TRACE   GAME-1 -> WI-7 (C4, C7), WI-13 (C1)
02:16:32Z  TRACE   GAME-2 -> WI-11 (C6–C9), WI-13 (C5, C6)
02:16:32Z  TRACE   GAME-3 -> WI-12 (C8)
02:16:32Z  TRACE   WIN-1 -> WI-3 (C1)
02:16:32Z  TRACE   WIN-2 -> WI-3 (C2–C5, C15)
02:16:32Z  TRACE   WIN-3 -> WI-3 (C6, C16)
02:16:32Z  TRACE   WIN-4 -> WI-9 (C1–C6), WI-13 (C8, C13)
02:16:32Z  TRACE   WIN-5 -> WI-3 (C12, C13), WI-13 (C7)
02:16:32Z  TRACE   SCRN-1 -> WI-10 (C2)
02:16:32Z  TRACE   SCRN-2 -> WI-3 (C8)
02:16:32Z  TRACE   SCRN-3 -> WI-4 (C1–C4), WI-13 (C11)
02:16:32Z  TRACE   SCRN-4 -> WI-10 (C4, C9), WI-13 (C9)
02:16:32Z  TRACE   SCRN-5 -> WI-10 (C5, C8), WI-13 (C9)
02:16:32Z  TRACE   SCRN-6 -> WI-5 (C5), WI-10 (C9)
02:16:32Z  TRACE   SCRN-7 -> WI-3 (C9), WI-13 (C12)
02:16:32Z  TRACE   MAZE-1 -> WI-2 (C1), WI-10 (C3)
02:16:32Z  TRACE   MAZE-2 -> WI-2 (C1, C5)
02:16:32Z  TRACE   MAZE-3 -> WI-2 (C2), WI-11 (C11)
02:16:32Z  TRACE   MAZE-4 -> WI-2 (C6), WI-13 (C2)
02:16:32Z  TRACE   MAZE-5 -> WI-2 (C3)
02:16:32Z  TRACE   MAZE-6 -> WI-2 (C4)
02:16:32Z  TRACE   START-1 -> WI-7 (C1, C3)
02:16:32Z  TRACE   START-2 -> WI-7 (C2)
02:16:32Z  TRACE   START-3 -> WI-7 (C4, C5)
02:16:32Z  TRACE   START-4 -> WI-7 (C6)
02:16:32Z  TRACE   START-5 -> WI-12 (C1), WI-13 (C1)
02:16:32Z  TRACE   CTRL-1 -> WI-6 (C1), WI-11 (C1), WI-13 (C4)
02:16:32Z  TRACE   CTRL-2 -> WI-11 (C1), WI-12 (C3)
02:16:32Z  TRACE   CTRL-3 -> WI-11 (C2)
02:16:32Z  TRACE   CTRL-4 -> WI-6 (C2), WI-12 (C5), WI-13 (C7)
02:16:32Z  TRACE   CTRL-5 -> WI-6 (C3), WI-3 (C10)
02:16:32Z  TRACE   GHOST-1 -> WI-3 (C11), WI-12 (C1, C2), WI-13 (C3)
02:16:32Z  TRACE   GHOST-2 -> WI-8 (C1)
02:16:32Z  TRACE   GHOST-3 -> WI-8 (C2, C3, C6)
02:16:32Z  TRACE   GHOST-4 -> WI-8 (C4)
02:16:32Z  TRACE   SCORE-1 -> WI-11 (C3), WI-13 (C4)
02:16:32Z  TRACE   SCORE-2 -> WI-11 (C3)
02:16:32Z  TRACE   SCORE-3 -> WI-11 (C4)
02:16:32Z  TRACE   SCORE-4 -> WI-7 (C5), WI-8 (C7), WI-10 (C7)
02:16:32Z  TRACE   SCORE-5 -> WI-11 (C5), WI-5 (C3)
02:16:32Z  TRACE   END-1 -> WI-11 (C6, C7, C10)
02:16:32Z  TRACE   END-2 -> WI-11 (C8), WI-13 (C6)
02:16:32Z  TRACE   END-3 -> WI-11 (C9)
02:16:32Z  TRACE   END-4 -> WI-10 (C6), WI-13 (C5)
02:16:32Z  TRACE   END-5 -> WI-12 (C4, C7), WI-13 (C5)
02:16:32Z  TRACE   END-6 -> WI-12 (C5, C6), WI-13 (C7)
02:16:32Z  TRACE   STAT-1 -> WI-5 (C4), WI-10 (C2)
02:16:32Z  TRACE   STAT-2 -> WI-5 (C1, C3)
02:16:32Z  TRACE   STAT-3 -> WI-5 (C2, C3)
02:16:32Z  ITERATION M1 walking skeleton: a window that paints, a maze that holds : WI-1, WI-2, WI-3, WI-4, WI-5, WI-6 (6.5 dev-days, ends day 2.5)
02:16:32Z  ITERATION M2 every piece of the game, tested pure : WI-7, WI-8, WI-9, WI-10, WI-11 (6.0 dev-days, ends day 4.5)
02:16:32Z  ITERATION M3 a game you can play to the finish : WI-12, WI-13 (3.0 dev-days, ends day 7.5)
02:16:32Z  ASSIGN  WI-1 -> developer A
02:16:32Z  ASSIGN  WI-2 -> developer B
02:16:32Z  ASSIGN  WI-3 -> developer C
02:16:32Z  ASSIGN  WI-4 -> developer A
02:16:32Z  ASSIGN  WI-5 -> developer A
02:16:32Z  ASSIGN  WI-6 -> developer A
02:16:32Z  ASSIGN  WI-7 -> developer B
02:16:32Z  ASSIGN  WI-8 -> developer A
02:16:32Z  ASSIGN  WI-9 -> developer C
02:16:32Z  ASSIGN  WI-10 -> developer A
02:16:32Z  ASSIGN  WI-11 -> developer B
02:16:32Z  ASSIGN  WI-12 -> developer B
02:16:32Z  ASSIGN  WI-13 -> developer C
02:16:32Z  RISK    WI-13 is HIGH and last: the run cannot finish before the user merges it; unavoidable, nothing else waits on a human
02:16:32Z  RISK    WI-2 (maze invariants, arch C4) is first on the 7.5-day critical path; a slip there moves the finish day for day
02:16:58Z  VERIFY  plan self-check (script): 107 claims, counts per item match the totals line; all 13 items appear as gantt bars; every claim id cited in text and in the traceability table exists
02:16:58Z  DONE    docs/IMPLEMENTATION_PLAN.md (landing as AMEND-0 on branch r8/plan)
02:26:18Z  NOTE    correction to 02:16:08Z VERIFY: the specimen's maze rows are 37 characters wide, so cells 37, 38 and 39 are all blank (the check tested only 38-39); WI-10/C3 reworded to say so, WI-10/C1 now says rows are padded to 40 (Copilot thread on PR #120)
02:26:18Z  NOTE    removed the title and blank line that preceded START, per progress-tracking.md (Copilot thread on PR #120)
02:26:30Z  CLAIM   WI-10/C1 (reworded) Given the specimen's maze, dots, player and ghost squares and a score of 0, the composed frame reproduces the specimen picture in `docs/FUNCTIONAL_REQUIREMENTS.md` §3 character for character, all 30 rows, each specimen row padded with blanks to 40 cells, ignoring the `← …` annotations.
02:26:30Z  CLAIM   WI-10/C3 (reworded) Grid square *n* (counting from 0) is drawn in cell 2*n*, with its joining cell to the east in cell 2*n*+1, so the maze's characters occupy cells 0 to 36. Cell 37, the joining cell after the last square, has no square east of it, and it and cells 38 and 39 are blank on every maze row, as in the specimen, whose maze rows are 37 characters wide.
