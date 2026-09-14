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
04:58:19Z  MERGE   wi-2-screen-port into main — 84 passed, 0 failed, 0 skipped (python3 -m unittest discover on main at 021db44)
04:58:27Z  VERIFY  WI-2 on main -> python3 -m unittest discover: Ran 84 tests, OK, 0 failed, 0 skipped. Matches DEV-B's reported count exactly.
04:58:27Z  DECIDE  WI-2 deviation 1, game_main holds the frame for --hold seconds -> ACCEPTED, because it exits by itself and honours q, so it neither blocks forever nor leaves WI-3 nothing to join to; it is M0 scaffolding only and WI-12's real game must exit on q and never on a timer.
04:58:27Z  DECIDE  WI-2 deviation 2, tests/test_layering.py -> ACCEPTED and adopted as a standing obligation: every later item that adds a layer extends it, and WI-4/WI-7 add the domain-purity cases.
04:58:27Z  DECIDE  WI-2 deviation 3, Frame.put raises out of range rather than clipping -> KEEP RAISING; no put_clipped. Measured: MAZE-3's border ring means an actor can only stand on squares 1..17, so its three-column glyph spans columns 1..35 of 0..36 and can never run off the edge. WI-5b must not add clipping; if it finds a real case, it comes back to me.
04:58:27Z  DECIDE  WI-2 deviation 4, dim yellow for gold and bold magenta for pink -> ACCEPTED, because an eight-colour terminal has neither; it stays one dict so it is one edit, and whether it reads right to a person stays a human check in WI-14b.
04:58:27Z  NOTE    DEV-B's finding on termios PENDIN (0x20000000 set after a clean curses session, every other bit identical on all four exit paths) is the kind of measurement a later restore test would otherwise fail on. WI-12 must mask that bit, not weaken the assertion.
04:58:27Z  NOTE    The launcher importing nothing from the game package is already this plan's section 3 rule, not a new ruling; DEV-A's launcher takes its own name and imports nothing from terminalgame.
04:58:27Z  DECIDE  COMPLETION-M0-DEV-B.md -> write it now covering M0 as it will actually stand, because the run is paused and WI-4 will not be dispatched.

## Note on the four lines that follow

05:01:47Z  NOTE    The next four lines were written at 05:01:47Z but record things I observed earlier, while I was isolated in DEV-B's worktree and could neither reach main nor commit here. I parked them in the scratchpad at the time rather than backfill invented timestamps, so they carry one honest stamp — the moment they reached this file — and each says plainly what it observed. The chronology of this log is intact everywhere else; this paragraph is the seam.

05:01:57Z  BLOCKED [observed earlier] I could not merge: the harness isolated me into the worktree agent-ab294a285809afe2d, which had DEV-B's branch wi-2-screen-port checked out, and refused any git command redirected at the primary checkout. main was checked out in the primary tree, so I could not merge into it from there and could not commit my own log without writing onto DEV-B's branch. Raised with the conductor, who took it to the user rather than merging in my place.
05:01:57Z  VERIFY  [observed earlier] wi-2-screen-port at ff2a680 -> main (eeccce3) is an ancestor, so a pure fast-forward with no merge commit; the commit adds docs/completions/COMPLETION-M0-DEV-B.md (174 lines) and 5 lines to docs/progress/wi-2-screen-port.md, and nothing executable.
05:01:57Z  VERIFY  [observed earlier] suite at ff2a680 inside DEV-B's worktree -> Ran 84 tests, OK, 0 failed, 0 skipped. Run with python3 -B so no bytecode was written into their tree; git status --short --untracked-files=all there returned nothing, before and after.
05:01:57Z  RISK    [observed earlier] two agents in one worktree: I was inside DEV-B's worktree with their branch checked out, which is the collision developer.md exists to prevent. No live collision occurred - DEV-B had finished and reported - and I wrote nothing. The risk was that I could have.
05:01:57Z  VERIFY  working tree restored -> pwd, git rev-parse --show-toplevel and git worktree list all confirm the primary tree with main checked out. Checked myself before acting rather than taking the restoration on report.
05:01:57Z  MERGE   wi-2-screen-port into main - 84 passed, 0 failed, 0 skipped (git merge --ff-only to ff2a680, then python3 -m unittest discover on main)
05:01:57Z  NOTE    DEV-A's WIN-3 finding, carried forward to the WI-1 merge: the window title bar reads "rodneybailey - Terminal Game - <running command>" because two title components are absent from the scripting dictionary and are governed by the player's saved Terminal profile. The standing assumption A3 / question Q3 says the terminal is driven per window with saved preferences left untouched, so the custom title is set, the profile-governed components are not cleared, and WIN-3 is NOT recorded as verified. It affects the WIN-3 coverage row and stays an assumption the user has not answered; flipping it is a change in the launcher and nowhere else.
05:03:09Z  VERIFY  working tree -> primary tree, main checked out, a01c88b. Checked before acting, as I said I would. The harness has been moving agents; I do not take restoration on report.
05:03:09Z  VERIFY  wi-1-window-launcher at e573172 -> merge-base d4c1a7f, so not a fast-forward. 19 files, +2634 lines, all additions. launcher/ is a new package disjoint from terminalgame/.
05:03:09Z  VERIFY  the predicted conflict on tests/__init__.py -> the two sides were NOT identical: main's (DEV-B's) is 81 bytes with a docstring, DEV-A's is 0 bytes. It merged cleanly anyway because an empty side has nothing to disagree with, so the docstring survived. The developers' agreement ("empty and identical on both sides") was not actually met; it was benign this time by luck, not by the agreement holding.
05:03:09Z  MERGE   wi-1-window-launcher into main - 191 passed, 0 failed, 0 skipped (merge commit feb7f7e, python3 -m unittest discover on main)
05:03:09Z  VERIFY  191 = 84 + 107 exactly, the first time both lanes' code has been in one tree. Nothing was lost and neither lane's tests interfered with the other's.
05:03:09Z  VERIFY  the section 3 layer rule across both lanes -> launcher/ imports nothing from terminalgame/; terminalgame/ names the launcher only in comments and imports neither it nor subprocess; subprocess appears only in launcher/. tests/test_layering.py passes with a launcher present for the first time, which is the first run in which it could have been wrong.
05:03:09Z  DECIDE  WI-1 deviation 1, the A2 fallbacks built now rather than in WI-13 -> ACCEPTED, because the clamp cannot function without a screen rectangle, so the fallback was not separable from WI-1's own outcome. Consequence for the plan: WI-13 becomes hardening and verification rather than first implementation. Recorded as a plan amendment.
05:03:09Z  DECIDE  WI-1 deviation 2, A4 pinned at 32 points down and 32 right -> ACCEPTED; A4 says in terms that the offset is a small fixed one chosen by the implementer, so it was theirs to pin. Now pinned and stated.
05:03:09Z  DECIDE  WI-1 deviation 3, GameWindow.asked_for alongside GameWindow.position -> ACCEPTED, because their own measurement proves the distinction is real: set position is a request, not an instruction. Recording what was asked for beside what was granted makes a silent override visible instead of discarding it.
05:03:09Z  DECIDE  C2 against C3 when setup fails while the game is still running -> C2 WINS, confirming DEV-A's choice. Closing a busy window raises a modal sheet that blocks every later osascript call INCLUDING the cleanup itself, so "reap anyway" does not even achieve reaping - it destroys the ability to reap. An orphan window is a nuisance a human can close in one gesture; a modal sheet stops the whole team and needs the user. Naming the window id in the failure is the right mitigation.
05:03:09Z  CONTRADICT My own plan section 4.1 says "Reap your windows on the failure path too" without saying what reaping means when the process will not die -> DEV-A's measurement exposed the gap. Amended: reaping never means closing a busy window.
05:03:09Z  CONTRADICT ARCHITECTURE.md A4 and the WIN-4 coverage row say the position is "clamped to the visible screen so the window always lands somewhere visible" -> measured: the desktop reports the union of all displays, -3509,-1440,1611,982, much of which is over no display at all, so clamping to it does not deliver visibility. The real guarantee is keeping the new window's corner inside the reference window's own frame, which is by construction on a display the player is looking at.
05:03:09Z  CONTRADICT ARCHITECTURE.md treats "move it to x+offset, y+offset" as an instruction -> measured: asked for Point(-876,-1353), landed at Point(-876,30), because macOS constrains a window to the screen it is on. WIN-4 must be confirmed by reading the position back, never assumed from the request succeeding.
05:03:09Z  NOTE    DEV-A's argument about where the test seam belongs is worth preserving: the seam is at the subprocess runner, not the adapter, so tests assert on the AppleScript text. C1 is a claim about the words in a script - act on a captured id, never on "the front window" - and a test that watched Python method calls would watch a well-behaved adapter emit "close front window" and notice nothing. That is the plan's own rule about asserting the consequence rather than the shape, applied somewhere I had not thought to apply it.
05:03:09Z  NOTE    Window hygiene on WI-1 held and was checked rather than assumed: five windows opened across the item, all five closed by the identity that created them, a final read-only census showing only the user's own pre-existing window id 7104, no modal sheet raised, no osascript call timed out.
05:03:31Z  DRAFT   docs/IMPLEMENTATION_PLAN.md section 11, Amendments after M0 -> what M0 actually delivered, WI-13's change of character, C2 beating C3 with the section 4.1 ground rule corrected in place, WIN-4's mechanism, WIN-3 not verifiable by automation, and where a test seam belongs when the requirement is about a script.
05:03:31Z  DONE    M0 closed at two of four items. main at feb7f7e plus this commit, 191 passed, 0 failed, 0 skipped. WI-1 and WI-2 delivered; WI-3 and WI-4 never dispatched because the run was paused. Whoever resumes starts at WI-4, the head of the critical path. Every merge this run was mine and each is recorded above with its count.

05:15:00Z  VERIFY  working tree -> primary tree, main checked out at 2229124. Checked before acting; the harness has isolated me before and a restoration is not something I take on report.
05:15:00Z  VERIFY  wi-4-maze-generator at ad81ae4 -> merge-base 5269b67, not a fast-forward. 9 files, +1666, all additions. Main's only change since the base is docs/progress/conductor.md, so no overlap at all with the branch.
05:15:00Z  MERGE   wi-4-maze-generator into main - 256 passed, 0 failed, 0 skipped (merge commit, python3 -m unittest discover on main)
05:15:00Z  VERIFY  256 reconciles exactly as DEV-B said: 191 on main + 29 + 30 + 6 = 256, so nothing existing changed count.
05:15:00Z  VERIFY  DEV-B's C8 proof, checked myself rather than taken on report. The premise is about the code, so I ran the real generator over 720 mazes at nine sizes: open squares with BOTH coordinates even = 0. The conclusion then follows by counting, and I checked that too: an opened square is either a cell (odd,odd) or the wall between two cells (exactly one even coordinate), so a both-even square is never opened; and every 2 x 2 block of squares contains exactly one both-even square, because exactly one of y,y+1 and one of x,x+1 is even. Therefore no 2 x 2 block can be fully open. The argument is sound.
05:15:00Z  DECIDE  C8 -> UPGRADED from a measurement to a proof in the plan. The architect's 300-maze sweep was evidence for something that holds by construction at any size under any random source. This matters because the sweep invites "could we relax the restriction if the numbers stay good?", and the answer is no, not "probably not".
05:15:00Z  DECIDE  WI-4 deviation 1, generate_maze taking width and height defaulting to 19 x 29 -> ACCEPTED and I want it kept. It is what lets the invariants be demonstrated at nine sizes, which is what turns C8 from a claim about 19 x 29 into a claim about the algorithm. MAZE-1 is preserved by the default.
05:15:00Z  DECIDE  WI-4 deviation 2, MazeTooSmall on an even dimension or a lattice under 2 x 2 cells -> ACCEPTED. Both cases make a requirement unsatisfiable, and refusing beats returning a quietly broken grid. It is the same principle as the WI-2 ruling that Frame.put raises rather than clips, so the two lanes are now consistent about refusing rather than silently degrading. I hit the 3 x 3 case by accident while checking the proof and the message named the reason, which is the behaviour working.
05:15:00Z  DECIDE  test_the_domain_carries_no_screen_geometry, flagged by DEV-B as a text scan that cannot catch a bare 40 -> KEEP AS IS, do not extend the word list, and do not invent work. The doubt is recorded, which is what I asked for. Guarding C5 harder needs a different mechanism, and DEV-B has already built the better one without naming it: the generator is exercised at nine sizes, so a screen dimension hard-coded in the domain would fail those tests outright. That is a stronger guard than any word list.
05:15:00Z  DECIDE  docs/completions/COMPLETION-M0-DEV-B.md -> REVISE it to cover WI-2 and WI-4 both. The document is one per lane per iteration and lane B's M0 is now actually complete, so the existing one is out of date rather than in need of a companion. No fifth document shape; the four in section 4.3 stand.
05:15:00Z  NOTE    DEV-B kept its own sweep honest in a way worth recording: a grid of solid wall satisfies MAZE-2, 3, 5 and 6 vacuously, so the sweep asserts corridor count too, and it runs the carve alone to show it leaves 8-22 dead ends every time. That is what makes "zero dead ends after the braid" mean anything rather than being true of an empty claim.
05:15:00Z  NOTE    tests/test_layering.py extended with DomainPurityTest, 6 tests, under the standing obligation I promoted after WI-2. The launcher half stays unguarded and WI-12 owns it; DEV-B recorded that in the file's docstring rather than closing it quietly.
05:15:12Z  DRAFT   docs/IMPLEMENTATION_PLAN.md sections 11.7-11.9 -> C8 upgraded from measurement to proof with the argument written out, refusing-beats-degrading made policy across both lanes, and the C5 guard that already exists in the nine-size tests.

05:52:50Z  VERIFY  working tree restored -> primary tree, main checked out at 08d9f7e, clean. Checked myself before acting; the harness had isolated me across five worktrees since the last merge I performed.
05:52:50Z  VERIFY  main at 08d9f7e before my merge -> python3 -m unittest discover: Ran 575 tests, OK. Confirms the user's queue integration landed green.
05:52:50Z  MERGE   wi-11-game-loop into main - 620 passed, 0 failed, 0 skipped (merge commit 1f4e229)
05:52:50Z  NOTE    WI-11 also changed terminalgame/domain/rules.py: advance_ghost now returns the state it was given when the ghost stays put, so "nothing happened" is signalled uniformly across the Domain. DEV-A's own file from its own item, documented in place. Accepted.
05:52:50Z  CORRECT I said last turn that nine merges landed "with no suite run between them". That was an inference from git's default commit messages, not an observation, and it was wrong: the user integrated the queue one branch at a time, in plan order, with the whole suite after each and a hard stop at the first red. The record is docs/findings/integration-queue-lockout.md. Absent metadata is not evidence of an absent method, and I should have written only what I measured, which was the endpoint.
05:52:50Z  DRAFT   docs/IMPLEMENTATION_PLAN.md -> applied the twelve edits owed while I was locked out: EDIT 3 (section 11.1 rewritten), 5 (11.3 replaced), 6 (11.12), 7 (11.10's fifth condition), 9 (section 3's Presentation bullet), 10 and 15 (section 4.4), 11 (section 4.2), 12 (11.8), 13 and 16 (11.11), 14 (11.13), plus 11.14 carrying the STAT-1 obligation into WI-12.
05:52:50Z  VERIFY  suite after the plan edits -> 620 passed, 0 failed, 0 skipped. Documents only; no code touched.

06:17:27Z  VERIFY  new merge procedure -> main is checked out in no tree; primary tree detached; the two routes in .claude/agents/technical-lead.md work from anywhere. Read the updated section before merging rather than acting on the summary I was sent.
06:17:27Z  MERGE   wi-12-wire-the-game into main - 648 passed, 0 failed, 0 skipped (integration tree, removed and verified gone)
06:17:27Z  MERGE   wi-13-launcher-robustness into main - 686 passed, 0 failed, 0 skipped (integration tree, removed and verified gone)
06:17:27Z  MERGE   wi-14a-acceptance-pack into main - 732 passed, 0 failed, 0 skipped (integration tree, removed and verified gone)
06:17:27Z  NOTE    The predicted --hold/--seed collision did not materialise: WI-13 merged green at 686 after WI-12 removed --hold. DEV-B's warning that its timing probe wants re-running still stands; that is a measurement, not a test failure.
06:17:27Z  DECIDE  WI-13 deleting Desktop.is_busy and script.window_is_busy outright -> ACCEPTED, and promoted to section 4.4. "A warning is not a guard" is the sharpest line of the run: the correct answer had been documented for a whole work item and the wrong one was still the default, so the defect survived on the path the docstring told people not to use.
06:17:27Z  DECIDE  WI-3's finding is superseded in its cause -> pointer added by me at the top of the finding, not by editing DEV-A's measurement. It takes BOTH the grid and a real curses program; nothing built on it changes, but a cause stated wrongly is how somebody later concludes it does not apply to them. Recorded as section 11.18.
06:17:27Z  DECIDE  the acceptance pack's boundary -> may import launcher, must import nothing from the game, guarded in test_layering. A check that reaches inside can pass while the thing the player runs is broken. Where the pack lives and what it is called are NOT mine - section 3 says so, and this is the one case where I was asked directly.
06:17:27Z  NOTE    WI-14a's brief asked for "maze properties over many seeds"; that is discharged by WI-4's 20,000-seed sweep in the unit suite, where it belongs. The pack correctly does not reach into the domain to repeat it.
06:17:27Z  DRAFT   docs/IMPLEMENTATION_PLAN.md -> EDIT 17 and the is_busy ruling into section 4.4; new sections 11.15 (--seed/--hold and WI-14b's obligation), 11.16 (what the specification does not say), 11.17 (the acceptance pack's boundary), 11.18 (WI-3 superseded).
