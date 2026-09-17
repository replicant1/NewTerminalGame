# WI-14 — the live game

**Branch:** `r7/wi-14-live-assembly`, cut from the tip of `main` at `7aebddc`.
**WI-16 is stacked on this branch** — lane C branched from `46f9682`, the surface commit.

| File | |
|---|---|
| `terminal_game/shell/game.py` | `build_game`, `Game`, `CADENCE_MS`, `run_game`, `main`. |
| `tests/test_game.py` | 16 headless tests and 1 marked `needs_window`. |
| `terminal_game/application/session.py` | *(fixed)* `__repr__` read the stale stamped field. |
| `tests/test_session.py` | *(+2)* the `repr` fix and its control. |
| `docs/progress/r7-wi-14-live-assembly.md` | |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**886 passed, 0 failed, 0 skipped, 5 deselected**. 799 before.

**Real window:** `-m needs_window tests/test_game.py` under a 90-second deadline in a
parent process — **1 passed in 1.15s**, elapsed 1.26s, no timeout.
**Crash reports 14 before, 14 after. Zero new. Nothing left on the desktop.**

---

## The surface went first, on purpose

`46f9682` is the first commit on this branch and contains nothing but the public surface,
pushed before any test was written, with the conductor told the moment it was up. Lane C
branched WI-16 from it. **The run's last planned conflict risk cost nothing** — the same
shape as the seam that cost us WI-4b, handled by committing the seam before working inward.

Nothing in the surface moved afterwards.

## Two defects of the same kind, and the second was mine

Both are about reading `GameState.outcome` — **the field the resolver stamps** — where
WI-11 established the derived function is the one source of truth.

**`Session.__repr__`**, found by lane C reading ahead. It printed
`Session(decided, undecided, ...)` for a hand-built board: phase right, outcome wrong.
**`repr` is what pytest prints on failure**, so WI-16's tracebacks would have sent whoever
debugged them after the wrong thing. Fixed, with a test on the awkward board *and* a
control proving `repr` can still say `undecided`.

**The status row, which was mine and new.** Finding the first one made me look for others,
and row 29 was being composed from `state.outcome` — so a hand-built board would have shown
a **stale outcome on the screen**, in the one place a player would read it. Exactly the
boards WI-16 hands in. Now taken from the session.

Worth naming as a pattern: the rule "ask the function, never the field" has now been broken
in two places that did not look like places where anyone asks whether the game is over — a
`repr` and a status line. Both were found by someone going looking rather than by a test
failing.

## GHOST-1 now has a test that names it

Lane B's audit found GHOST-1 was the one requirement code **no test mentioned anywhere**,
and that `143` appeared only in prose. Its point is right: a cadence inlined into an
`after()` call is a requirement nobody can audit, and WI-18 would have found a code nobody
claimed.

Two tests now carry GHOST-1 in their names and docstrings:

- the ghost moves on the timer **with no key sent in the test at all**;
- the interval asked for is `CADENCE_MS`, **on every beat and not just the first**, because
  a reschedule using a different interval would drift only after the first tick.

They assert against `CADENCE_MS`, not a literal, with one separate line pinning the
constant's value — so WI-19 changing it changes what the test *means* rather than breaking
it.

## The seams, one test each — and nothing either side of them

That a maze is sound is WI-2's; a move legal, WI-10's; Decided ignoring a tick, WI-11's;
`q` meaning quit, WI-13's; the picture right, WI-4b's; the canvas showing what it was given,
WI-5's. **None of it is re-proved here.**

| Seam | Asserted by its consequence |
|---|---|
| WI-13 → WI-11 → WI-10 | one key in, the player has moved one square and scored the dot |
| WI-4b → WI-5 | after a move *and* a tick, all 30 rows on the glass equal the composed field — and the picture is shown to have changed, so a game that painted once and never repainted would fail |
| WI-12 → WI-4b | row 29 is exactly `status_for(state)`; nothing here knows the literal |
| scheduler → session | the ghost moves with no key, at `CADENCE_MS`, repeatedly |
| random source → generator **and** ghost | same seed gives the same maze **and** the same 30-step walk; a different seed gives neither |
| WI-11 → WI-6, both ways | quitting closes the window, **and closing the window quits the session** |

That last one only exists here. A player who clicks the close button has left the game, and
if that did not reach the session the session would still be nominally playing with the
window gone.

**The controls that make the rest mean something:** a key that means nothing changes
nothing (or "Right moved the player" would say nothing about translation being wired in);
the fixture board is asserted to put the player where every move test assumes; and
`start()` twice is asserted not to run two timers, which would double the ghost's speed in
a way nothing else would catch.

## A test double that lied, caught and fixed

`RecordingScheduler.fire` left its entry pending after firing, but **Tk's `after` is
one-shot**. So it reported a timer as still scheduled after the game had deliberately
stopped rescheduling — a false pass on the very test that checks the timer stops once the
game is decided. The double now clears before invoking. The game was correct throughout; no
production code was changed to make a test pass.

## Decisions taken (section 1.8 — reported, not asking)

**`tick()` is public and the scheduler is injectable**, so a whole game runs with no real
time passing. `maze=` plays a board handed in, which is how WI-16's END-3 board gets in, and
`seed=` makes a journey reproduce. **Nothing is shown and no timer runs until `start()`.**

**The timer stops when the session stops accepting play.** WI-11 would ignore the beats, but
a timer firing forever into a decided game is a tick that moves nothing, forever.

## Window hygiene

Never a second `tkinter.Tk()` — everything goes through `GameWindow`. No competing
`destroy`, no `update()`, no `ctypes`. The watchdog in `run_game` is **not set in
production**: a game that closed itself on a timer would be a time limit, and GAME-3
forbids one. Crash reports counted before and after.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
