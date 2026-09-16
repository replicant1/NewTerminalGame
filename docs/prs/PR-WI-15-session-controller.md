# WI-15 — The session controller

**Lane:** DEV-A · **Branch:** `r6/wi-15-session-controller`, based on `main`
at `671f0e5` · **Mode:** non-local · **Not stacked** — WI-13 merged first.

**Announcing the seam, per section 2's rule 4 and amendment 3.** This is the
one-call seam **WI-12 implements** and **WI-19 consumes**:

```python
from terminal_game.application.session import Phase, Session, new_session

session = new_session(
    maze,
    compose=...,        # (GameState) -> frame        <- WI-12 implements this
    show=...,           # (frame) -> None             <- the grid surface
    random_source=...,  # handed straight to the ghost
    shut_down=...,      # () -> None                  <- WindowOwner.end_session
)
session.start()                    # START-5: the first picture, before the loop
session.tick()                     # GHOST-1
session.move(Direction.NORTH)      # CTRL-1
session.quit()                     # CTRL-4, END-6
session.phase                      # Phase.PLAYING | DECIDED | ENDED
session.failure                    # the exception that ended it, or None
```

**`compose` takes a game state and returns a frame. That is the whole seam.**
Everything about what is *in* that frame — the maze rows, the actors, the
draw order, row 29 — stays WI-12's and WI-13's, and nothing in this item's
tests asserts any of it.

---

## What this item is

Three states and no fourth: **Playing**, **Decided**, **Ended** (GAME-3).
`Phase` is *derived* from whether the session has been shut down and whether
the game's outcome is decided, so there is nowhere for a fourth state to
live and no restart edge to add one.

| File | What it is |
| --- | --- |
| `terminal_game/application/__init__.py` | a new subpackage for the Application layer |
| `terminal_game/application/session.py` | `Phase`, `Session`, `new_session` |
| `tests/test_session.py` | 44 tests |
| `docs/progress/r6-wi-15-session-controller.md` | the progress log |

Requirements: **GAME-3**, **START-5**, **CTRL-4**, **END-5**, **END-6**,
**WIN-5** under assumption A3, and **GHOST-1** in part (the cadence itself is
WI-3's; that a tick moves the ghost and nothing else does is here).

## Three decisions a reviewer should push back on if they disagree

**1. There is no clock object, and the session reads no clock.** The plan's
ownership table gives DEV-A "the clock seam", and I did not build one as an
object. The window owner already owns the timer and already starts it before
the event loop is entered; a session-owned clock would be a *second* one that
only tests ever use. Instead the session exposes `tick()` and something else
decides when to call it — the timer in the real game, the test in a test. A
whole game therefore runs headless as fast as it can be driven, which is what
WI-19 needs. **WI-19: drive `tick()`, `move()` and `quit()`; do not build a
clock.**

**2. A key reaches the session as `move(Direction)` or `quit()`, not as an
`Intent`.** The Application layer may not name Presentation, and WI-9's
`Intent` lives there. The Shell's `SessionCollaborator` adapter in WI-18 is
already unpacking a `KeyPress` and calling `translate`; dispatching the
intent it gets back is three lines in the same place, so it exists once:

```python
intent = translate(key.keysym, key.char)
if intent is None:
    return
if intent.kind is IntentKind.QUIT:
    session.quit()
else:
    session.move(intent.direction)
```

**3. A frame is composed and shown exactly when the state changes**, plus
once at `start()`. *The picture follows the state.* END-5's "composes nothing
new" in Decided then falls out of one rule rather than being a rule of its
own, and so does a press towards a wall composing nothing (CTRL-3).

## A failure is routed, not raised — and that is a measurement, not taste

*Amendment 1, from a Tk 8.5 behaviour measured during WI-3.* **Tk swallows an
exception raised inside an `after()` callback**: it reaches
`report_callback_exception`, a traceback is printed, and the main loop
carries on. A session that let an error out of a tick would not shut down —
it would sit there with a broken game on an unquittable screen.

So `tick()` and `move()` route a failure into **the same shutdown path `q`
uses**, deliberately, and do not re-raise. It is not absorbed: the exception
is kept on `session.failure` for the caller to report once the loop has
returned. **WI-18 should check `session.failure` after `WindowOwner.run()`
returns and exit non-zero if it is set.**

`start()` is deliberately different and is left to raise: it runs *before*
the event loop, where propagation works, and a game that cannot compose its
opening picture should fail loudly rather than open a window and shut itself
down again.

Note that `WindowOwner._guarded` already reaps the window if the collaborator
raises. That is the Shell's net and it stays; this item does not rely on it,
because inside an `after()` callback the re-raise that follows is swallowed.

## Where contradiction C-2 lands, and what a ruling costs

> WIN-5 says the window *"closes by itself as soon as the game ends"*; END-5
> says the last picture stays on screen; END-6 says `q` is the only way out
> of a finished game. All three cannot hold on WIN-5's literal reading.

**The user has not ruled.** We proceed on **assumption A3**: the outcome is
decided, the final picture stands, the player presses `q`, the process exits,
and the window closes without the player closing it.

**A3 is implemented in one place** — `Session._advance` enters `DECIDED`
rather than `ENDED` when the outcome is set. A ruling the other way is that
one line, plus the WIN-5, END-5 and END-6 rows of WI-20's sweep. There is a
test named for it, `test_deciding_does_not_shut_the_session_down`, so the
assumption is visible rather than implicit.

## What these tests own, and what they refuse to re-assert

Section 4's rule bites hardest here, because the session calls three things
that all have their own tests:

- **the turn resolver** — the join is asserted by computing the expected
  state with `resolve_move` / `resolve_tick` in the test and checking the
  session kept exactly that. What a turn *does* stays WI-11's 25 tests.
- **the frame composer** — the fake returns a `Picture`, which is
  deliberately **not** a `Frame`, so that nothing here can accidentally
  depend on what a frame contains.
- **the status line** — the session never chooses a line. It composes from a
  state whose outcome is set, and WI-13 selects by that outcome. The join
  asserted is that the outcome reaches the composer;
  `tests/test_status_line.py` owns what the line then reads.

**No mutation test was written and no working code was broken to watch a test
go red.** That is prohibited and none was invented.

## WI-12 landed while this branch was open, and the seam holds

`origin/main` moved to `a08b11b` (PR #45) part-way through; it was merged
onto this branch cleanly, with no conflicts.

**DEV-B's `compose_frame(state, status_row, walls=...)` takes two arguments
where this seam takes one. That is differently spelled, not wrong**, so
section 2's "conforming would change behaviour" case does not arise and
nothing needs settling between us. The plan requires WI-12 to take row 29
**as a value** and never compose its text, so binding WI-13's row in is the
*caller's* job — which is this item and, concretely, two lines in WI-18:

```python
def compose(state):
    return compose_frame(state, status_row(state.score.points, state.outcome))
```

**WI-19 should use exactly that** rather than a third arrangement.

**Verified end to end, outside the suite**, against the real composer, the
real wall glyphs, the real status line and a real generated maze:

```
new_session(generate_maze(Random(1)), compose=<the two lines above>, ...)
start() + 40 ticks -> 41 frames, each 30 x 40
row 29 -> 'score 0    arrows, q quits              '
quit()  -> Phase.ENDED, failure None
```

## Nothing here opens a window

Pure Application. Measured after this branch: `tkinter._default_root` is
`None` once every test module has been imported, and `grep` finds no mention
of `presentation`, `shell` or `tkinter` anywhere under
`terminal_game/application/`. WI-10's rules 4 and 5 are unaffected — a new
*sub*package leaves exactly one root package.

## The suite

Run from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 533 tests in 4.161s

OK
```

**533 passed, 0 failed, 0 skipped**, on this branch with `origin/main` at
`a08b11b` merged onto it. **44 are WI-15's** (446 before WI-8 and WI-12
landed, of which 402 were `main` at `671f0e5`).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
