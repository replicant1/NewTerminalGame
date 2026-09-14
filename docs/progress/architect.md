04:10:23Z  START   architect, fresh run: deriving the architecture from docs/FUNCTIONAL_REQUIREMENTS.md alone; previous run's documents deliberately not consulted
04:10:23Z  READ    docs/FUNCTIONAL_REQUIREMENTS.md in full - 58 codes across GAME/WIN/SCRN/MAZE/START/CTRL/GHOST/SCORE/END/STAT
04:10:23Z  READ    .claude/agents/architect.md, .claude/shared/progress-tracking.md, .claude/shared/ask-a-human.md
04:11:25Z  VERIFY  counted requirement codes in the spec -> 49 unique (GAME 3, WIN 5, SCRN 7, MAZE 6, START 5, CTRL 5, GHOST 4, SCORE 5, END 6, STAT 3), not the 58 I was briefed with; coverage table will have 49 rows
04:11:25Z  VERIFY  measured the sample picture -> 29 maze rows of 37 columns; each maze square is 2 screen columns (19x2=38, last join column blank), so MAZE-1 fits 40 cols with a 3-column right margin
04:11:25Z  VERIFY  located actor glyphs in the sample -> ghost at col 1 for cell 1, player at col 19 for cell 10: actors draw 3 columns wide at 2c-1..2c+1, bleeding one column into the neighbour
04:11:25Z  VERIFY  prototyped DFS perfect maze + braiding on a 19x29 grid over 300 seeds -> 0 dead ends, fully connected, solid border, no 2x2 open block, 269 corridor squares (268 dots) every time; MAZE-2..6 need no special architecture, only a domain-layer generator
04:11:25Z  WEIGH   how the app gets its own macOS window : (a) automate a terminal emulator from a launcher process (b) open a native GUI window and paint a character grid (c) leave it to the user to size a terminal
04:11:25Z  DECIDE  window ownership -> two candidates, (a) favoured and (b) as the alternative; (c) rejected because WIN-1..WIN-5 make window lifecycle the app's job, not the player's
04:11:25Z  WEIGH   input vs the 7Hz ghost clock : (a) single-threaded loop with a timed key read (b) timer thread + input thread + shared state under a lock
04:11:25Z  DECIDE  concurrency -> single-threaded loop with a timeout on the key read, because GHOST-1 needs two event sources, not two threads, and threads would buy nothing at this scale
04:11:31Z  ASK     WIN-5 says the window closes as soon as the game ends, but END-5/END-6 say the final picture stays and q is the only way out - which wins at the moment of a win or loss?
04:11:31Z  ASSUME  the final picture stays and the window closes when the session exits (on q, or on quit after an ending). Affects the WIN-5 and END-5/END-6 coverage rows and the second sequence diagram; cheap to flip - it moves one signal earlier in the same component
04:11:31Z  ASK     may the game rely on the one-off macOS Automation/Accessibility permission needed to read the frontmost window's position (WIN-4) and to drive the terminal (WIN-1..3, WIN-5)?
04:11:31Z  ASSUME  yes, with a documented fallback to a fixed default position if the query is refused. Affects WIN-4 coverage and the launcher component only
04:11:31Z  ASK     which terminal application may be automated, and may its settings be changed - or must the game leave the user's terminal preferences untouched?
04:11:31Z  ASSUME  the system-supplied terminal, driven per-window only, with no change to the user's saved preferences. Affects WIN-2 coverage and the launcher's window-setup step
04:11:31Z  RISK    desktop automation is permission-gated and version-sensitive; a failed window query or a refused automation event must degrade to a usable default rather than abort the game
04:11:31Z  RISK    closing a terminal window while its process is still running raises a modal sheet only a human can dismiss; the launcher must confirm the window is idle before closing it
04:11:31Z  DRAFT   beginning docs/ARCHITECTURE.md
04:12:49Z  DRAFT   docs/ARCHITECTURE.md written: drivers, two candidates with block and sequence diagrams, rejected alternatives, recommendation, two 49-row coverage tables, assumptions, cautions, open questions
04:13:29Z  VERIFY  coverage tables checked by script -> 49 rows each, no missing, no extra, no duplicate codes, matching the 49 codes in the spec
04:13:29Z  VERIFY  all 5 mermaid diagrams rendered with mmdc -> 5/5 OK after removing a <br/> and a semicolon from a sequence Note (both are mermaid syntax, not text)
04:13:29Z  DECIDE  recommendation -> Candidate 1 (Launched Terminal Session with a Layered Game Core), because both candidates still need the same automation permission for WIN-4, so Candidate 2 buys a GUI toolkit and a hand-built text grid for an advantage it only partly delivers
04:13:29Z  RISK    WIN-5 and END-5 cannot both hold at the instant of an ending; recorded as assumption A1 and open question Q1 with the two affected coverage rows named
