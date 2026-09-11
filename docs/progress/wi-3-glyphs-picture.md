01:13:49Z  START   WI-3 glyph and colour tables, and the whole picture
01:14:02Z  READ    docs/FUNCTIONAL_REQUIREMENTS.md — SCRN-1..7, STAT-1..3, END-4, MAZE-1, and the mock-up
01:14:13Z  READ    docs/IMPLEMENTATION_PLAN.md — §2 ground rules, §5 WI-3 brief, §6 pairing, §9 A3, §10
01:14:17Z  READ    termgame/model.py — Position/Direction/Outcome/Maze/GameState/Frame/FrameBuilder all present
01:14:26Z  READ    termgame/maze.py — lattice, from_text loader, invariant checks
01:14:26Z  READ    tests/test_purity.py — AST + poison guards; my module must import nothing impure
01:15:39Z  NOTE    WI-3 decoded the mock-up: all 15 non-empty wall masks are unambiguous (one glyph each); mask 15 (NSEW) absent, inferred as the crossing
01:15:39Z  NOTE    WI-3 joiner rule confirmed against the mock-up: the only odd-column non-blanks are the player/ghost spill at (13,19/21) and (27,1/3)
01:16:28Z  READ    docs/ARCHITECTURE.md §5.5, §7, §8, §12 — the 16-entry table there agrees with my decode on all 15 observed cases
01:16:28Z  PLAN    WI-3 two pure modules: termgame/theme.py (glyphs, 16-entry wall-mask table, style identifiers, the three status strings) and termgame/view.py (render(state) -> Frame), plus a 30x40 golden picture fixture
01:20:07Z  TEST    test_theme.py alone: 30 passed, 0 failed, 0 skipped
01:20:07Z  COMMIT  f6042f3 WI-3: glyph and colour tables — all 16 wall masks and the five style identifiers
01:20:07Z  NOTE    WI-3 theme.py committed early so Dev B can read the style identifiers: wall, dot, player, ghost, status (plus WI-1 default); attributes are the plain names bold and dim
01:24:35Z  TEST    whole suite: Ran 258 tests ... OK (skipped=2) — 258 passed, 0 failed, 2 skipped (main was 186+2; WI-3 adds 72)
01:24:35Z  NOTE    WI-3 golden fixture tests/fixtures/spec_picture.txt passes: the spec picture renders back as exactly those 30 rows of 40 columns
01:24:35Z  ASK     SCRN-5 gives each entity three characters on a two-column pitch, so two entities on horizontally adjacent corridor cells must share one picture column; the spec never draws that case and does not say what should happen
01:24:41Z  ASSUME  proceeding with the draw order the plan specifies — the ghost is last, so the ghost keeps the shared column and the player loses its right-hand edge for that one frame. Affects only view.draw_entity and TestTwoEntitiesSideBySide in tests/test_view.py; a ruling either way is a few lines
01:25:57Z  NOTE    WI-3 PR summary written to docs/prs/PR-WI-3-glyphs-picture.md
01:26:27Z  NOTE    WI-3 draft PR #6 opened against main
01:27:08Z  TEST    cross-check on /opt/homebrew/bin/python3 (3.14.7): Ran 258 tests ... OK (skipped=2) — 258 passed, 0 failed, 2 skipped
01:27:14Z  DONE    WI-3 wi-3-glyphs-picture (head after this commit); draft PR #6 to be marked ready, suite 258 passed 0 failed 2 skipped on both interpreters
