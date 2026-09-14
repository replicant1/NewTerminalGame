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
```
