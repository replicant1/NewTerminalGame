# WI-12: Session control

Risk: MEDIUM
It is the plan's floor for WI-12, and I have not raised it. The code is pure application logic with no clock, no toolkit and no window. It stays MEDIUM because WI-13 drives the whole game through this interface.

**Branch:** `r8/wi-12-session-control`, cut from `main` at `ebffe07` (WI-10 included). **The base for controls is `ebffe07`.** **Lane B**, Dev B. **Realises:** START-5, GHOST-1 (one step per tick), CTRL-2, CTRL-4, END-5, END-6, GAME-3.

## What it is

`terminal_game/application/session.py` holds `Session`, the game's state machine. It has three phases:

- **`PLAYING`** holds from the moment the session is made. Each tick moves the ghost one square through WI-11's `step_ghost`. Each arrow intent tries one player move through WI-11's `move_player`.
- **`DECIDED`** holds once the game is won or lost. The final picture stays: ticks and arrows change nothing, and only quit has any effect. This is plan §1.8 Q2, reading A3.
- **`ENDED`** follows quit, given while playing or after the ending. The shell closes the window. Anything that arrives afterwards is ignored without error.

Nothing leads back from `DECIDED` or `ENDED`. There is no clock and no randomness of the session's own: ticks and intents arrive as calls, and the random source is handed in.

## The session's interface, for lane C (WI-13) (plan §5.2)

```python
from terminal_game.application.session import Session, PLAYING, DECIDED, ENDED
from terminal_game.presentation.frame_composer import compose        # WI-10
from terminal_game.presentation.input_translation import translate   # WI-6

session = Session.new(random.Random())   # lays out the maze with that source, sets up, keeps the source for the ghost

def after_event():
    if session.ended:
        window.close()
    else:
        window.paint(compose(session.state))

def on_key(name):                  # WI-3's key names
    session.handle(translate(name))    # a WI-6 intent: "up" "down" "left" "right" "quit", or None
    after_event()

def on_tick():                     # WI-3's 7 Hz tick
    session.tick()
    after_event()

window.paint(compose(session.state))   # the first picture, before run
sys.exit(window.run(on_key, on_tick))
```

- `Session(state, rng)` starts from any `GameState`. `Session.new(rng)` gives the same result as `Session(new_game(generate_maze(rng)), rng)`, so a test-only fixed seed for WI-13's scripted win and loss is just `Session.new(random.Random(seed))`.
- `session.state` is what to compose. `session.phase` is one of the three phases. `session.ended` is true once quit has been given.
- `handle` raises `ValueError` for an intent WI-6 could not have produced (A2). `None`, for any other key, is accepted and does nothing.
- Closing the window from its close button or the app menu is WI-3's concern (WI-3/C13): `run` returns and the session is simply dropped.

## Claims

Every command runs from the repository root, with `.venv/bin/python` built from `requirements.txt` as in plan §1.2. **H** is the harness `evidence/WI-12/session_transcript.py`. It drives sessions exactly as the interface above tells the shell to: key names go through WI-6's `translate`, and after each event it either records a close or composes a frame with WI-10's `compose`. It uses a stand-in window and never opens a real one. It prints each event with the phase, the squares and the status row that would be painted, then runs a C9 check over 1,000 seeds. It ends `ALL PASS` or `SOME FAIL` and exits 0 only on `ALL PASS`.

**Control for every claim: n/a.** The session is new code with no counterpart. At the base `ebffe07`, `terminal_game/application/` holds only `__init__.py` and `turn_resolution.py` (`git ls-tree --name-only ebffe07 terminal_game/application/`). Nothing on the base has phases, ticks or intents to run a claim against. The diff against the base is additions only.

| Claim | Word for word | Evidence | What the output shows |
|---|---|---|---|
| WI-12/C1 | A new session is already playing: the first tick moves the ghost, with no key pressed. | Executable: `.venv/bin/python -m pytest -v tests/test_session.py -k c1_`, and H | `PASSED`: over 200 seeds, `Session.new` is `PLAYING` and one tick moves the ghost. H: the first event, a `tick` with no key pressed, shows `phase playing … ghost (2, 1)`, where the ghost started at (1, 1). |
| WI-12/C2 | While playing, each tick moves the ghost exactly one square, and key presses between ticks neither add ghost moves nor remove them. | Executable: `-k c2_` | 2 `PASSED`. (a) Over 200 seeds, every tick while playing moves the ghost a Manhattan distance of exactly 1. (b) Over 200 seeds, a session with 0 to 3 random key presses between ticks gives exactly the ghost path of the same seed with no keys, one move per tick. The test fails if fewer than 10,000 ticks were compared. |
| WI-12/C3 | Each arrow key press moves the player at most one square, and with no key presses the player never moves, however many ticks pass. | Executable: `-k c3_` | 2 `PASSED`: 200 seeds × 300 random arrows, each moving at most one square; and 200 seeds × 500 ticks, with the player never leaving the start. |
| WI-12/C4 | Once the game is won or lost, ticks no longer move the ghost, arrow keys no longer move the player, and the state the shell would paint no longer changes. | Executable: `-k c4_`, and H | 2 `PASSED` (lost and won): after 50 rounds of a tick and four arrows, the state equals the decided state. H: after the catch, `Right`, `Left`, `tick` and `a` each print `player (4, 1) ghost (4, 1) status ' CAUGHT  score 0    q quits'`. After the win, a `tick` and `Left` each print `player (3, 1) ghost (7, 1) status ' CLEARED  score 6    q quits'`. |
| WI-12/C5 | `q` or `Q` ends the session at once, both while playing and after the game is decided. | Executable: `-k c5_`, and H | 6 `PASSED`: `q` and `Q`, each through WI-6's `translate`, while playing, after a loss and after a win. H shows `Q` after the catch, `q` after the win, and `q` while playing on a generated maze, each giving `-> window closed` on that event. |
| WI-12/C6 | After the game is decided, quit is the only input that has any effect. | Executable: `-k c6_` | 2 `PASSED` (lost and won). The key names Up, Down, Left, Right, a, space, Return, Escape, F1, Shift_L and 1, each through `translate` and each followed by a tick, leave phase and state identical. Then `q` ends the session. |
| WI-12/C7 | An arrow key that arrives immediately after the tick in which the ghost catches the player does not move the player. | Executable: `-k c7_`, and H | `PASSED`: after the third tick the outcome is `LOST` with both on (4, 1). Each of the four arrows then leaves the player on (4, 1). H prints the catching `tick`, then `Right` and `Left`, with the player still on (4, 1). |
| WI-12/C8 | Nothing leads back from an ending: no sequence of inputs starts a new game, restores the player or resumes play. | Executable: `-k c8_` | 2 `PASSED` (lost and won). Each runs 200 random sequences of 100 events (arrows, other keys, quit, ticks). After every event the phase is `DECIDED` or `ENDED`, never `PLAYING`, and the state, outcome included, equals the decided state. |
| WI-12/C9 | Given the same maze, the same random source and the same sequence of ticks and keys, two sessions end in identical states. | Executable: `-k c9_`, and H | `PASSED`: over 300 seeds, two runs of the same 600-event script end identical. The test fails unless more than 250 runs of a different script end differently, so it is not comparing things that could never differ. H: `identical end states for the same maze, source and inputs: 1000/1000; with a different input script, different end states: 999/1000  PASS`. H needs more than 800 of those to differ, the same kind of floor the test applies. |
| WI-12/C10 | A tick or a key that arrives after the session has ended is ignored without error. | Executable: `-k c10_`, and H | `PASSED`: after quit, given while playing, after a loss and after a win, 20 rounds of ticks and every intent (quit included) raise nothing and leave phase `ENDED` and the state unchanged. H shows `tick` and `Up` after close as `(after close: ignored)`. |
| WI-12/A1 | The session's intents are WI-6's own: every intent `translate` can produce is accepted by `handle` with the same meaning, so the shell can pass `translate(name)` straight in. | Executable: `-k a1_` | `PASSED`: the five constants equal WI-6's. `translate("Right")` and `translate("Left")` move the player east and back, and `translate("a")` does nothing. |
| WI-12/A2 | An intent WI-6 could not have produced is refused with `ValueError`: anything other than `None` or the five intents. | Executable: `-k a2_` | 8 `PASSED`: `"jump"`, `"Up"` (a key name, not an intent), `"q"`, `""`, `3`, the unhashable `[]` and `{}`, and `("up",)`. |
| WI-12/A3 | `Session.new(rng)` lays out the maze with the source it is handed and sets up the game: it equals `new_game(generate_maze(rng))` for the same seed. | Executable: `-k a3_` | `PASSED` for 50 seeds, and two seeds give different mazes. |

Also at this head: the suite `.venv/bin/python -m pytest -q` gives 494 passed, 0 failed, 1 skipped. `.venv/bin/python -m tools.layer_check` reports `application 3`, `PASS (0 violation(s), 0 problem(s))`.

## Diff map

```
terminal_game/application/session.py:1-36     -> docstring: phases and the shell's wiring (C1-C10, for WI-13)
terminal_game/application/session.py:38-46    -> mechanical (imports)
terminal_game/application/session.py:48-57    -> WI-12/A1 (intents equal WI-6's), A2 (the tuple of valid intents), C3 (one square per arrow)
terminal_game/application/session.py:59-62    -> WI-12/C1, C4, C5 (the three phases)
terminal_game/application/session.py:65-71    -> WI-12/C1 (playing from the start), C9 (state and source handed in)
terminal_game/application/session.py:73-76    -> WI-12/A3 (Session.new)
terminal_game/application/session.py:78-92    -> WI-12/C4 (state to paint), C1, C5, C8 (phase: nothing leads back)
terminal_game/application/session.py:94-97    -> WI-12/C1, C2 (one ghost step per tick while playing), C4 (none after)
terminal_game/application/session.py:99-103   -> WI-12/A2 (intent refused, unhashable ones included)
terminal_game/application/session.py:104-105  -> WI-12/C10 (ignored after the end)
terminal_game/application/session.py:106-107  -> WI-12/C5 (quit ends at once, in any phase)
terminal_game/application/session.py:108-109  -> WI-12/C3 (one move per arrow), C6, C7 (no move once decided)
tests/test_session.py (new)                   -> evidence for C1-C10, A1-A3
evidence/WI-12/session_transcript.py (new)    -> evidence (harness H) for C1, C4, C5, C7, C9, C10
docs/prs/PR-WI-12-session-control.md (new)    -> this brief
docs/progress/r8-wi-12-session-control.md (new) -> progress log
docs/completions/COMPLETION-M2-DEV-B.md:+12   -> WI-11 completion record (mechanical; conductor's ruling)
docs/progress/r8-wi-11-turn-resolution.md:+5  -> WI-11 completion record (mechanical; WI-11's final log lines)
```

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
