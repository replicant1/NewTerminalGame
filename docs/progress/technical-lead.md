# Technical Lead — progress log

04:24:32Z  START   Technical lead begins. Local mode, 2 developers, Candidate 1 ruled by the user. Overwriting the previous run's log.
04:24:32Z  READ    docs/ARCHITECTURE.md — both candidates, sections 8 (A1-A10), 9 (C1-C14), 10 (Q1-Q3).
04:24:40Z  READ    docs/FUNCTIONAL_REQUIREMENTS.md — extracted 49 unique codes; per-section counts match caution C12 exactly.
04:24:40Z  VERIFY  requirement-code extraction -> 49 unique codes: GAME 3, WIN 5, SCRN 7, MAZE 6, START 5, CTRL 5, GHOST 4, SCORE 5, END 6, STAT 3. C12 confirmed.
04:24:40Z  READ    .claude/agents/developer.md — four document paths, worktree/branching rules, window-safety rules.
04:26:17Z  DECIDE  architecture -> Candidate 1 "Launched Terminal Session with a Layered Game Core", because the user ruled it; Candidate 2 stays a documented fallback only.
04:26:17Z  DECIDE  mode -> local mode, told by the conductor; I merge every work item, developers never touch main.
04:26:17Z  DECIDE  team size -> 2 developers, told by the conductor; two lanes, DEV-A and DEV-B.
04:26:17Z  VERIFY  python3 on this machine -> 3.9.6, curses imports, unittest present, pytest ABSENT.
04:26:17Z  DECIDE  runtime -> Python 3.9.6, standard library only, unittest as the test framework, because pytest is not installed and there is no virtualenv or packaging in this tree.
04:26:17Z  VERIFY  specification picture geometry -> 30 rows: 29 maze rows of exactly 37 columns, then the status line. Square glyphs sit on even columns 0..36 (19 squares); odd columns are joiner/filler only.
04:26:17Z  CONTRADICT ARCHITECTURE.md S6 MAZE-1 says "19 x 2 = 38 of 40 columns; the remainder is the blank right margin" -> measured: the picture is 37 columns wide, so the right margin is 3 columns, not 2. Assumption A5 in the same document says 37. The S6 note is the wrong one.
04:26:17Z  CONTRADICT ARCHITECTURE.md A5 says the 3-column actor glyph "bleeds one column into the square to the west" -> measured: actor glyphs sit at odd columns 2k-1 and 2k+1, which are joiner columns, never another square. An actor overwrites the joiner either side, which can erase a horizontal wall join; it never overwrites a neighbouring square.
04:26:17Z  CONTRADICT FUNCTIONAL_REQUIREMENTS.md WIN-5 ("closes by itself as soon as the game ends") against END-5/END-6 ("the last picture stays on screen", "q is the only way to leave a finished game") -> both cannot hold at the instant of a win or loss. Carried as assumption, not ruling.
04:26:17Z  CONTRADICT .claude/agents/developer.md requires report section 5 "Mutation checks - the failure messages verbatim" -> the same file, and this plan, prohibit proving a test can fail. Developers are told to write "not applicable" there.
04:26:25Z  WEIGH   iteration shape : 3 large iterations vs 4 smaller ones over 2 lanes
04:26:25Z  DECIDE  iteration shape -> 4 iterations, M0..M3, because M0 must prove the window and the screen end to end before any game logic is worth writing.
04:26:25Z  ITEM    WI-1 Desktop automation adapter and window launcher: query geometry, create a window, capture its id, size/title/colour it, move it, close it safely (2 d, depends on nothing)
04:26:25Z  ITEM    WI-2 Screen port and terminal adapter over curses, plus a trivial game process that draws one frame and quits on q (2 d, depends on nothing)
04:26:25Z  ITEM    WI-3 End-to-end join: the launcher opens the window, the game runs in it, the window closes by itself after the game exits (1 d, depends on WI-1, WI-2)
04:26:25Z  ITEM    WI-4 Maze model and generator: 19x29, border ring, odd-lattice carve, braid out every dead end (2 d, depends on nothing)
04:26:25Z  ITEM    WI-5a Wall-glyph selection: a pure mapping from a square's four wall neighbours to a blue double-line glyph, lone block included (1 d, depends on WI-4)
04:26:25Z  ITEM    WI-5b Frame composition: 37 of 40 columns, 29 maze rows, dots, player, ghost, draw order (2 d, depends on WI-5a, WI-7)
04:26:25Z  ITEM    WI-6 Status line: the bottom row, cyan, in play and at both endings (1 d, depends on WI-7)
04:26:25Z  ITEM    WI-7 Game state and the opening position: the state vocabulary, player at the centre, ghost furthest away, a dot on every other corridor square, score zero (1 d, depends on WI-4)
04:26:25Z  ITEM    WI-8 The player's move: walls block, dots are eaten, the score rises (1 d, depends on WI-7)
04:26:25Z  ITEM    WI-9 Ghost policy: straight on while it can, otherwise a random other way, reversing only as a last resort, blind to the player (1 d, depends on WI-4, WI-7)
04:26:25Z  ITEM    WI-10 Rules and outcome: one ordered function, collision decided before the last dot (1 d, depends on WI-7, WI-8)
04:26:25Z  ITEM    WI-11 The game loop: the clock, key-or-tick by timeout arithmetic, quit, and the frozen ending (2 d, depends on WI-2, WI-8, WI-9, WI-10)
04:26:25Z  ITEM    WI-12 Wire the whole game into the launched window and play it (2 d, depends on WI-3, WI-5b, WI-6, WI-11, WI-13)
04:26:25Z  ITEM    WI-13 Launcher robustness: permission refused, bounded waits, orphan reaping on the failure path (1 d, depends on WI-3)
04:26:25Z  ITEM    WI-14a Acceptance pack: automated checks over the landed pieces, and the written human-check list (1 d, depends on WI-5b, WI-6, WI-11)
04:26:25Z  ITEM    WI-14b Run the acceptance pack against the wired game and report (1 d, depends on WI-12, WI-14a)
04:26:25Z  ITERATION M0 "Walking skeleton: a window, a screen, and a pure maze" : WI-1, WI-2, WI-3, WI-4
04:26:25Z  ITERATION M1 "A model that can be played headlessly" : WI-7, WI-8, WI-10, WI-5a, WI-9
04:26:25Z  ITERATION M2 "The picture, the loop, and a launcher that fails safely" : WI-6, WI-11, WI-5b, WI-13
04:26:25Z  ITERATION M3 "The whole game in its own window" : WI-12, WI-14a, WI-14b
04:26:25Z  ASSIGN  WI-1, WI-3, WI-7, WI-8, WI-10, WI-6, WI-11, WI-12 -> DEV-A (11 developer-days)
04:26:25Z  ASSIGN  WI-2, WI-4, WI-5a, WI-9, WI-5b, WI-13, WI-14a, WI-14b -> DEV-B (11 developer-days)
04:26:34Z  TRACE   GAME-1 -> WI-4 + WI-7 (one pure state holding maze, player, ghost, dots)
04:26:34Z  TRACE   GAME-2 -> WI-10 (outcome CLEARED / CAUGHT)
04:26:34Z  TRACE   GAME-3 -> WI-7 (session scope) + WI-11 (no pause, no restart path exists)
04:26:34Z  TRACE   WIN-1 -> WI-1 (the launcher creates the window; the game process never does)
04:26:34Z  TRACE   WIN-2 -> WI-1 (40x30, fixed-width font, black ground on the captured id) + WI-14b human check
04:26:34Z  TRACE   WIN-3 -> WI-1 (title set on the captured id only)
04:26:34Z  TRACE   WIN-4 -> WI-1 (frontmost geometry queried BEFORE creation, then offset and clamped) + WI-13 (fallback when refused)
04:26:34Z  TRACE   WIN-5 -> WI-3 (close the captured id once the game process has exited and the window is idle) under assumption A1
04:26:34Z  TRACE   SCRN-1 -> WI-5b (rows 0-28) + WI-6 (row 29)
04:26:34Z  TRACE   SCRN-2 -> WI-2 (a character-cell port; no image path exists anywhere)
04:26:34Z  TRACE   SCRN-3 -> WI-5a (neighbour-sensitive blue double-line glyphs, lone block included)
04:26:34Z  TRACE   SCRN-4 -> WI-5b (dim gold dot, one per corridor square)
04:26:34Z  TRACE   SCRN-5 -> WI-5b (bright yellow player, pink ghost, different outlines)
04:26:34Z  TRACE   SCRN-6 -> WI-6 (cyan status line)
04:26:34Z  TRACE   SCRN-7 -> WI-2 (whole-frame buffered present, cursor hidden) + WI-12 (no flicker in the real window)
04:26:34Z  TRACE   MAZE-1 -> WI-4 (19 x 29 grid) + WI-5b (37 columns used, 3 columns of right margin)
04:26:34Z  TRACE   MAZE-2 -> WI-4 (odd-lattice carve; no 2x2 open block)
04:26:34Z  TRACE   MAZE-3 -> WI-4 (border ring never carved)
04:26:34Z  TRACE   MAZE-4 -> WI-4 (seeded generator) + WI-7 (a fresh seed per session)
04:26:34Z  TRACE   MAZE-5 -> WI-4 (braiding pass, restricted to the same odd lattice)
04:26:34Z  TRACE   MAZE-6 -> WI-4 (spanning-tree carve, preserved by braiding)
04:26:34Z  TRACE   START-1 -> WI-7 (corridor square nearest the centre)
04:26:34Z  TRACE   START-2 -> WI-7 (corridor square at greatest straight-line grid distance, metric stated)
04:26:34Z  TRACE   START-3 -> WI-7 (a dot on every corridor square but the player's)
04:26:34Z  TRACE   START-4 -> WI-7 (score zero)
04:26:34Z  TRACE   START-5 -> WI-11 (the clock runs from the first pass; nothing is awaited)
04:26:34Z  TRACE   CTRL-1 -> WI-11 (arrow keys mapped to a move) + WI-8 (the move itself)
04:26:34Z  TRACE   CTRL-2 -> WI-8 + WI-11 (one key, one square; no held-direction state exists)
04:26:34Z  TRACE   CTRL-3 -> WI-8 (a move into a wall changes nothing at all)
04:26:34Z  TRACE   CTRL-4 -> WI-11 (q or Q quits on every pass, in play and after an ending)
04:26:34Z  TRACE   CTRL-5 -> WI-11 (unmapped keys discarded) + WI-2 (raw, non-echoing mode)
04:26:34Z  TRACE   GHOST-1 -> WI-11 (timeout recomputed each pass as the time to the next tick) + WI-9 (one square per tick)
04:26:34Z  TRACE   GHOST-2 -> WI-9 (straight on while the corridor allows)
04:26:34Z  TRACE   GHOST-3 -> WI-9 (random among the other open ways; reversal only as a last resort)
04:26:34Z  TRACE   GHOST-4 -> WI-9 (the player's position is not a parameter of the policy)
04:26:34Z  TRACE   SCORE-1 -> WI-8 (the dot is gone for the rest of the game)
04:26:34Z  TRACE   SCORE-2 -> WI-8 (one dot, one point)
04:26:34Z  TRACE   SCORE-3 -> WI-8 (an empty square scores nothing)
04:26:34Z  TRACE   SCORE-4 -> WI-9 (the ghost's move touches neither dots nor score) + WI-5b (the ghost is drawn over an intact dot)
04:26:34Z  TRACE   SCORE-5 -> WI-6 (shown in the status line) + WI-8 (only ever rises)
04:26:34Z  TRACE   END-1 -> WI-10 (co-location tested after every move, either way round)
04:26:34Z  TRACE   END-2 -> WI-10 (no dots remaining)
04:26:34Z  TRACE   END-3 -> WI-10 (collision evaluated before the cleared test, inside one ordered function)
04:26:34Z  TRACE   END-4 -> WI-5b (fixed draw order: the ghost after the player)
04:26:34Z  TRACE   END-5 -> WI-11 (after an ending, no ticks and no moves; the frame stands)
04:26:34Z  TRACE   END-6 -> WI-11 (q remains the only key acted on)
04:26:34Z  TRACE   STAT-1 -> WI-6 (nothing else writes the bottom row)
04:26:34Z  TRACE   STAT-2 -> WI-6 (in-play text with the live score)
04:26:34Z  TRACE   STAT-3 -> WI-6 (CAUGHT / CLEARED text selected by outcome)
04:26:34Z  VERIFY  traceability -> all 49 requirement codes placed on a work item; none unplaced.
04:26:41Z  ASK     Q1 At the moment of a win or a loss, does the window close (WIN-5) or does the final picture stay until q (END-5, END-6)?
04:26:41Z  ASSUME  A1: the picture freezes at the ending and the window closes by itself when the player quits. WIN-5, END-5, END-6, WI-3 and WI-11 depend on it; flipping it moves one signal earlier inside the loop.
04:26:41Z  ASK     Q2 May the game rely on the one-off macOS Automation / Accessibility permission needed for WIN-4 and for driving the window? No agent can grant or verify it; it is a dialog in front of a human.
04:26:41Z  ASSUME  A2: yes, with a documented fallback position if it is refused. WIN-2, WIN-3, WIN-4, WIN-5, WI-1 and WI-13 depend on it.
04:26:41Z  ASK     Q3 Which terminal application may be automated, and may anything about it be changed?
04:26:41Z  ASSUME  A3: the system-supplied terminal, driven per window, with the player's saved preferences left untouched. WIN-2 and WI-1 depend on it.
04:26:41Z  ASK     Should the stale repo-root executables (verify, launch-smoke, check-window-placement, play, "Terminal Game") be deleted? They reference a package that no longer exists.
04:26:41Z  ASSUME  they stay on disk and the plan declares them non-authoritative and off limits; no work item reads them. Nothing depends on the answer beyond tidiness.
04:26:41Z  RISK    WI-1 desktop automation overruns or is blocked by the permission dialog -> M0 slips and every later iteration slips with it; lane A carries one day of float in M0 for exactly this, and WI-13's fallback keeps a refusal from being fatal.
04:26:41Z  RISK    the terminal application's saved preferences override the per-window font, size or colours -> WIN-2 fails in a way only a human at the screen can see; collected as a human check in WI-14b rather than guessed at.
04:26:41Z  RISK    a window closed while its process is still alive raises a modal sheet that blocks every later osascript call -> the whole run appears to hang on a mysterious timeout; C2 is restated as a ground rule and WI-13 owns the idle confirmation.
04:26:41Z  RISK    WI-5b and WI-6 both write into the same 40x30 frame -> a merge conflict; they are sequenced on different lanes with WI-6 landing first, and the two developers own disjoint rows (0-28 against 29).
04:26:41Z  RISK    curses on an 80x24 default window before WI-1's resize lands -> the game cannot address 40x30; WI-2 must fail loudly rather than draw a truncated frame.
04:28:02Z  DRAFT   docs/IMPLEMENTATION_PLAN.md — all sections: mode, runtime, layer rule, ground rules, assumptions, contradictions, 4 iterations, schedule, gantt, dependency graph, 49-row traceability, risks.
04:28:20Z  VERIFY  plan self-consistency -> 49 traceability rows (all codes, none extra); 16 work items, 16 gantt bars, every item has a bar; bar days per iteration 7/5/6/4 = 22, matching the iteration table; milestones M0..M3 at 19/22/25/28 Sep, matching the quoted boundaries.
04:28:20Z  DONE    docs/IMPLEMENTATION_PLAN.md
04:57:52Z  NOTE    DEV-B reports WI-2 ready on branch wi-2-screen-port head ebbd510, base d4c1a7f, 84 passed. Beginning merge checks.
