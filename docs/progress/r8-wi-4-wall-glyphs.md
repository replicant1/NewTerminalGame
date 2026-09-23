03:18:05Z  WI-4 START   WI-4 wall glyphs (LOW), Dev A, branch r8/wi-4-wall-glyphs from origin/main 75723e7, carrying r8/wi-1-completion per the conductor's ruling
03:20:24Z  WI-4 DECIDE  interface -> wall_glyph(n,s,e,w), joining_glyph(w,e), and square_glyph/joining_cell over an is_wall(col,row) predicate with explicit width/height, because C3 must hold whatever the maze value says off-grid and WI-10 can pass maze.is_wall
03:20:24Z  WI-4 VERIFY  specimen redraw -> 287 wall squares, 518 joining cells, 0 mismatches, 4 sprite-covered joining cells blank; lone blocks at grid (6,18) and (6,22) (my first expectation said col 5, a miscount of cell 12)
03:20:24Z  WI-4 RISK    WI-4 LOW, because it is the plan floor: an isolated pure leaf
03:20:24Z  WI-4 CLAIM   C1-C3 executable -- pytest -v tests/test_wall_glyphs.py -k c1/c2/c3; C4 executable -- evidence/WI-4/specimen_glyphs.py
03:20:24Z  WI-4 TEST    157 passed, 0 failed, 1 skipped
