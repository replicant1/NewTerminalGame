# WI-10 — the rules and the outcome, as one ordered function

Branch `wi-10-rules-outcome`, cut from `wi-8-player-move` at 62d2bb5. A
three-deep stack: `wi-7-game-state` → `wi-8-player-move` → this, because WI-10
depends on WI-7 and WI-8 and neither can merge while the tree is locked.
DEV-A, lane A, M1, local mode.

```
05:36:19Z START   WI-10 the rules and the outcome. END-1, END-2, END-3, GAME-2,
05:36:19Z         and END-5's "everything stops". END-4's draw order is WI-5b's.
05:36:19Z NOTE    WI-10 told rather than left to rediscover: END-3's headline
05:36:19Z         case is reachable only because START-3 excepts the player's
05:36:19Z         square alone, so the ghost starts on a dotted square. My own
05:36:19Z         WI-7 test pins it. Without that decision "eat the last dot on
05:36:19Z         the ghost's square" could not arise.
05:36:19Z DECIDE  WI-10 the outcome gap I flagged in WI-8 is the DOMAIN's, and
05:36:19Z         the requirement decides it rather than taste. END-5 reads "Once
05:36:19Z         a game has ended everything stops: the ghost stands still, the
05:36:19Z         arrow keys do nothing, and the last picture stays on screen."
05:36:19Z         "Everything stops" is a statement about the game, not about key
05:36:19Z         handling -- a domain that still moves a finished player can
05:36:19Z         represent a state the requirements forbid. END-6's "q still
05:36:19Z         quits, and is the only way to leave" IS key handling and stays
05:36:19Z         with WI-11 and CTRL-4/CTRL-5.
05:36:19Z DECIDE  WI-10 the guard goes on move_player itself, not only on the
05:36:19Z         composed step, because a guard that can be bypassed by calling
05:36:19Z         the primitive is not a guard. It returns the same state object,
05:36:19Z         matching the convention WI-8 set for CTRL-3. WI-8's three
05:36:19Z         pinning tests get rewritten, as their own docstrings asked.
05:36:19Z NOTE    WI-10 a trap found while designing settle(): outcome_of is a
05:36:19Z         pure function of positions and dots, so re-running it on a
05:36:19Z         FINISHED state could change the answer -- a CLEARED game whose
05:36:19Z         ghost later stood on the player would read as CAUGHT, turning a
05:36:19Z         win into a loss. END-5 forbids it. settle() therefore leaves a
05:36:19Z         finished outcome alone rather than recomputing it, and there is
05:36:19Z         a test for exactly that.
05:36:19Z PLAN    WI-10 terminalgame/domain/rules.py: outcome_of (the ordered
05:36:19Z         function), settle, advance_player, advance_ghost. Tests in
05:36:19Z         tests/test_rules.py.
```
