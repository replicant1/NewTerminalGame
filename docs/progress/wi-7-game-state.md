# WI-7 — the game state and the opening position

Branch `wi-7-game-state`, cut from `main` at c4171fb. DEV-A, lane A, M1, local mode.

```
05:27:28Z START   WI-7 the state vocabulary the rest of the game speaks, and the
05:27:28Z         opening position. START-1 to START-5 and GAME-3. Depends on WI-4,
05:27:28Z         which is merged.
05:27:28Z NOTE    WI-7 read PR-WI-4-maze-generator.md before writing anything, as
05:27:28Z         instructed, rather than inferring the maze API. Taken from it:
05:27:28Z         coordinates are (x, y), y counts down from the top, so north is
05:27:28Z         y - 1; Maze is immutable and hashable; corridor_squares() is in
05:27:28Z         reading order; anything off the grid reads as WALL; generate_maze
05:27:28Z         carries no state between calls.
05:27:28Z DECIDE  WI-7 the state is immutable, like Maze. WI-8's "a move into a
05:27:28Z         wall changes nothing at all" is then testable as equality against
05:27:28Z         the state before, rather than as an absence of mutation, and
05:27:28Z         WI-9 and WI-10 cannot alias a state they were handed.
05:27:28Z DECIDE  WI-7 Q3/START-2 metric: straight-line (Euclidean) distance across
05:27:28Z         the grid, compared as squared distance so the arithmetic stays
05:27:28Z         exact integers. "Straight-line" is what A6 says and Euclidean is
05:27:28Z         what straight-line means; Manhattan and Chebyshev also satisfy
05:27:28Z         the words, so this is an ASSUMPTION and recorded as one, never a
05:27:28Z         ruling. The same metric serves START-1's "nearest the middle", so
05:27:28Z         there is one metric in the item rather than two.
05:27:28Z DECIDE  WI-7 ties break in reading order (smallest y, then smallest x),
05:27:28Z         stated in the sort key rather than left to rely on the order
05:27:28Z         corridor_squares() happens to return.
05:27:28Z DECIDE  WI-7 the centre is compared in doubled coordinates -- dx =
05:27:28Z         2x-(width-1) -- so an even-sided grid has an exact centre instead
05:27:28Z         of a half-square rounding decision. 19x29 is odd both ways so it
05:27:28Z         changes nothing there, but §11.9 says to keep testing at other
05:27:28Z         sizes and this is what makes those sizes exact.
05:27:28Z DECIDE  WI-7 START-5 "the ghost is already moving" means the ghost needs a
05:27:28Z         heading from the outset. It is drawn from the random source among
05:27:28Z         the ghost's open neighbours, so it is always a way the ghost can
05:27:28Z         actually go and it is reproducible from the seed. A fixed initial
05:27:28Z         heading would sometimes point into a wall.
05:27:28Z NOTE    WI-7 START-3 excepts only the player's square, so the ghost's
05:27:28Z         starting square DOES hold a dot. That is what makes END-3
05:27:28Z         reachable -- the last dot can sit under the ghost -- and WI-10
05:27:28Z         depends on it, so it is pinned with its own test here.
05:27:28Z PLAN    WI-7 terminalgame/domain/game_state.py: Outcome, GameState,
05:27:28Z         new_game/new_game_with, and the metric. Tests in
05:27:28Z         tests/test_game_state.py -- a name under neither DEV-B's prefix
05:27:28Z         nor my launcher one. Extend tests/test_layering.py per the
05:27:28Z         standing obligation.
```
