04:32:05Z  START   WI-1 the picture as a value (DEV-B, run 6) on branch r6/wi-1-picture-value, based on main 1f6ea32
04:32:05Z  READ    docs/IMPLEMENTATION_PLAN.md, docs/ARCHITECTURE.md (candidate 2 adopted), docs/FUNCTIONAL_REQUIREMENTS.md, .claude/shared/*.md
04:32:05Z  VERIFY  /usr/bin/python3 -> 3.9.6, Tk 8.5; ls-remote on origin for r6/ heads -> empty, no collision with run-5 branches
04:33:54Z  VERIFY  measured the specimen picture in FUNCTIONAL_REQUIREMENTS.md myself -> 30 rows; 29 maze rows of exactly 37 chars; status row 27 chars with a leading space. Confirms plan section 5 and contradiction C-1 (architecture prose says 38/2, its own V8 and this say 37/3)
04:33:54Z  PLAN    WI-1: terminal_game/presentation/frame.py holding Colour (closed 6-member enum), Cell (glyph+colour NamedTuple), immutable Frame, mutable FrameBuilder; tests/specimen.py carrying the specimen picture as shared test data
04:33:54Z  DECIDE  frame value shape -> immutable Frame plus a separate FrameBuilder, because the whole test strategy calls the frame a value and a stored "last picture" (END-5) must not be mutable by whoever composed it
04:33:54Z  DECIDE  out-of-range positions -> IndexError including negatives, because Python negative indexing would otherwise wrap and draw silently in the wrong place
04:33:54Z  DECIDE  package layout -> terminal_game/{domain,application,presentation,shell}/ with tests/ flat at the root, because it makes WI-10 layer guard trivial and keeps the pinned discover command finding everything
04:33:54Z  TEST    45 passed, 0 failed, 0 skipped  [/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"]
