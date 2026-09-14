# WI-8 — the player's move

Branch `wi-8-player-move`, **stacked on `wi-7-game-state` at af4c6d9**, not cut
from `main`: WI-8 depends on WI-7 and WI-7 cannot merge while nobody can reach
the primary tree. DEV-A, lane A, M1, local mode.

```
05:33:11Z START   WI-8 a move of one square in one of four directions.
05:33:11Z         CTRL-1, CTRL-2, CTRL-3, SCORE-1, SCORE-2, SCORE-3, SCORE-5.
05:33:11Z DECIDE  WI-8 goes in a new module, terminalgame/domain/player.py, and
05:33:11Z         changes no existing file. DEV-B is on WI-9 stacked on the same
05:33:11Z         branch; a new file of my own is the cheapest way to be sure we
05:33:11Z         cannot collide. game_state.with_changes already does everything
05:33:11Z         the move needs, so there is nothing to add to WI-7's module.
05:33:11Z DECIDE  WI-8 does NOT touch tests/test_layering.py. Adding player.py to
05:33:11Z         its "the domain is where it is said to be" list would be an
05:33:11Z         adjacent-line edit to the one file DEV-B is also likely to add
05:33:11Z         ghost.py to -- a predictable conflict for no gain, because
05:33:11Z         domain_files() already sweeps my module automatically. The same
05:33:11Z         guarantee goes in my own test file instead, reusing the
05:33:11Z         layering helpers rather than duplicating them.
05:33:11Z DECIDE  WI-8 a move into a wall returns the SAME state object, not an
05:33:11Z         equal one. CTRL-3 says "nothing at all", and identity is the
05:33:11Z         strongest form of that -- a test can assert `is`, which no
05:33:11Z         amount of rebuilt-but-equal state would satisfy.
05:33:11Z NOTE    WI-8 the trap the conductor named, taken seriously: "moving into
05:33:11Z         a wall leaves the player where they were" is green against a
05:33:11Z         move() that does nothing ever, and "re-entering an eaten square
05:33:11Z         scores nothing" is green against one that never scores. So every
05:33:11Z         such test here also exercises the case that MUST change, in the
05:33:11Z         same test, against the same state. A do-nothing implementation
05:33:11Z         has to fail them.
05:33:11Z PLAN    WI-8 move_player(state, direction) -> GameState, in
05:33:11Z         terminalgame/domain/player.py; tests in tests/test_player.py.
```
