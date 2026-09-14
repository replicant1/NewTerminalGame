# WI-6 — the status line

Branch `wi-6-status-line`, cut from `wi-10-rules-outcome` at 1d37240. Four deep:
`wi-7-game-state` → `wi-8-player-move` → `wi-10-rules-outcome` → this.
DEV-A, lane A, M2, local mode.

```
05:41:19Z START   WI-6 the bottom row and nothing else, in cyan. STAT-1, STAT-2,
05:41:19Z         STAT-3, SCRN-6.
05:41:19Z NOTE    WI-6 checked DEV-B's branches before creating anything, rather
05:41:19Z         than assuming. They are live on wi-5b-frame-composition (worktree
05:41:19Z         agent-a8ddd11bcf04cac47, head bc21558), and BOTH their branches
05:41:19Z         already carry terminalgame/presentation/__init__.py. WI-5b is the
05:41:19Z         frame composer, so it is the thing that will PLACE my status row.
05:41:19Z DECIDE  WI-6 took their presentation/__init__.py verbatim rather than
05:41:19Z         writing my own: git cat-file blob 6b5672e... into place, and
05:41:19Z         verified my file hashes to the same 6b5672e2. An add/add of two
05:41:19Z         identical blobs merges clean; two different ones conflict. This
05:41:19Z         is the "one of you writes it, the other reads that exact blob"
05:41:19Z         rule, and it is why I read rather than agreed.
05:41:19Z NOTE    WI-6 following their convention from wall_glyphs.py: Presentation
05:41:19Z         imports Colour from terminalgame.screen.port and names a module
05:41:19Z         colour constant. Colour.STATUS maps to COLOR_CYAN in the adapter,
05:41:19Z         which is SCRN-6 -- checked rather than assumed.
05:41:19Z MEASURE WI-6 the leading-space question, from the source rather than from
05:41:19Z         the summary of it. The picture's status row is at line 71 of
05:41:19Z         FUNCTIONAL_REQUIREMENTS.md and is 27 characters: a leading space
05:41:19Z         then "score 0    arrows, q quits". STAT-2's inline quote is the
05:41:19Z         same 26 characters WITHOUT the space.
05:41:19Z DECIDE  WI-6 keep the leading space. Three reasons: the picture is a
05:41:19Z         verbatim code block that preserves whitespace exactly, where an
05:41:19Z         inline backtick quote is prose in which a leading space is
05:41:19Z         invisible and trivially lost in transcription; the maze's left
05:41:19Z         wall sits at column 0, so one space lifts the line off it; and
05:41:19Z         WI-2's skeleton already on main uses " score 0    arrows, q
05:41:19Z         quits" with the space, so this agrees with the tree instead of
05:41:19Z         contradicting it. ASSUMPTION, not a ruling -- the user has not
05:41:19Z         been asked.
05:41:19Z MEASURE WI-6 STAT-3's alignment, checked rather than assumed. "q quits"
05:41:19Z         starts at index 19 in the CAUGHT line and 20 in the CLEARED one.
05:41:19Z         But ONE rule reproduces all three quoted lines exactly: the score
05:41:19Z         field is "score <n>" left-justified in 9 columns, with two spaces
05:41:19Z         either side of it. The one-column difference falls out entirely
05:41:19Z         from CAUGHT being six letters and CLEARED seven.
05:41:19Z DECIDE  WI-6 the misalignment is INCIDENTAL, and the decisive reason is
05:41:19Z         not the arithmetic: a game ends one way, so a player never sees
05:41:19Z         both lines. Alignment between them is unobservable. Reproducing
05:41:19Z         the two quoted lines exactly matters; aligning them with each
05:41:19Z         other would mean departing from a quote to fix something nobody
05:41:19Z         can see.
05:41:19Z PLAN    WI-6 terminalgame/presentation/status_line.py: status_text,
05:41:19Z         status_row, STATUS_COLOUR. Tests in tests/test_status_line.py --
05:41:19Z         DEV-B's is test_wall_glyphs.py, so no collision.
05:43:31Z MEASURE WI-6 ran DEV-B's own tests/test_layering.py from
05:43:31Z         wi-5b-frame-composition against this tree, rather than assuming
05:43:31Z         my module would satisfy the PresentationLayerTest their WI-5a
05:43:31Z         added. All four Presentation guards pass on status_line.py:
05:43:31Z         imports only the Domain and the screen port; never reaches for
05:43:31Z         the terminal adapter; reads no key, writes no terminal, never
05:43:31Z         sleeps; and the Domain does not import Presentation. The single
05:43:31Z         failure is their test asserting wall_glyphs.py exists, which is
05:43:31Z         on their branch and not mine -- an artefact of running their
05:43:31Z         file against my tree alone, not a defect in either.
05:43:31Z NOTE    WI-6 their test_layering.py is a STRICT SUPERSET of mine: it
05:43:31Z         already carries my WI-7 uses_global_random work and my
05:43:31Z         game_state.py line, because they merged wi-7-game-state. I have
05:43:31Z         not touched that file in WI-6, so no conflict is expected.
05:43:31Z NOTE    WI-6 their guard permits terminalgame.screen.port but their own
05:43:31Z         comment records that as needing a ruling -- plan §3 says
05:43:31Z         Presentation depends on the Domain "and on nothing else" while
05:43:31Z         asking it to produce colours it cannot name without the port.
05:43:31Z         status_line.py imports Colour and REQUIRED_WIDTH from there, so
05:43:31Z         if that ruling goes the other way this module changes alongside
05:43:31Z         wall_glyphs.py. Followed the convention already in the tree
05:43:31Z         rather than opening a second front.
05:43:31Z NOTE    WI-6 status_line.py deliberately NOT added to their
05:43:31Z         PresentationLayerTest named-module list: files_under sweeps it
05:43:31Z         automatically, naming one module already serves that list's
05:43:31Z         purpose, and a second name is an adjacent-line edit to the one
05:43:31Z         file the other lane is editing. Recorded in the commit message
05:43:31Z         and the PR summary per EDIT 11.
05:43:31Z TEST    400 passed, 0 failed, 0 skipped  (python3 -m unittest discover)
05:43:31Z COMMIT  26232d6 WI-6: the status line
05:43:31Z NOTE    WI-6 merged main on the rhythm: still c4171fb, up to date.
05:43:31Z NOTE    WI-6 windows opened: 0. Pure presentation.
05:43:31Z DONE    WI-6 wi-6-status-line (docs commit follows 26232d6)
```
