# WI-16 — the end-to-end behaviour suite

The assembled game driven through the journeys no unit test covers. Plan section 5,
iteration M3, lane C.

## Stacked, deliberately

**This branch is cut from `r7/wi-14-live-assembly` at `46f9682`, not from `main`, and this
PR targets that branch.** Plan section 7 makes WI-16 the one stacked item in the project:
it branches while WI-14 is still in flight because lane C would otherwise wait three days
for lane A. Based on `main` the diff would show WI-14's commits as WI-16's own and be
unreadable.

**Retarget with `gh pr edit <n> --base main` once WI-14 merges.**

`46f9682` is deliberately the first commit on that branch — the public surface, committed
before lane A wrote any tests, exactly as section 7 asks. Nothing here touches lane A's
code.

## What is here

`tests/test_end_to_end.py` — **33 tests**, no production code.

Every one plays a **whole game**: real maze, real resolver, real ghost policy, real
composer, real surface, joined as `build_game` joins them. What is asserted is what a
player would see at the end.

## The journeys

| | |
|---|---|
| **A win** | A corridor ring. The player follows the corridor westward — the way the ghost circulates — and clears all 19 dots in 19 turns without being caught. **The ghost is moving throughout**, and a test asserts that, so the win is not a walk round an empty board |
| **A loss** | The same ring, same driver, the player setting off *eastward* instead — straight into the ghost. Caught in 7 turns with dots still on the board |
| **The END-3 board** | Two corridor squares. `new_game` puts the player on one and the ghost on the other, with the game's only dot on the **ghost's** square — so one move eats the last dot *and* walks into the ghost |
| **`q` from Playing and from Decided** | Both cases, both `q` and `Q`, and the window closes with the session |

**The win and the loss differ only in which way the player sets off**, and a test asserts
they really do end differently — if they ever agreed, one of them would be proving nothing.

## The END-3 board is as small as it can be, and that is the point

Two squares. The two step orderings — *eat then test the win* versus *test the collision
first* — give **different answers on this board and the same answer on every other**. A
test first establishes that the board really is the discriminating one (one dot, and it is
on the ghost's square) so the assertion below it cannot pass vacuously.

Played: **`CAUGHT`, score 1, zero dots left.** Both halves happened — the board is cleared
of dots *and* lost. And the status line says `CAUGHT`, which is where a player would
actually notice END-3 being broken.

This also confirms the lead's ruling from END-3's own wording: **eating the last dot on the
ghost's square does score it.**

## The positions are built; the verdicts are not

No test here stamps an outcome and expects it believed. `GameState.outcome` is a cache the
resolver writes and `turn.outcome_of` is the derived truth; on a hand-built board they can
disagree. Every board is set up and then *played*, and the outcome is whatever the rules
produce.

## Guards, so the journeys cannot pass for the wrong reason

- **The seed does not matter here, and the suite says so rather than assuming it.** A ring
  has no junctions, so the ghost never consults the random source. I measured that during
  planning — seeds 7 and 8 walked identically on a two-loop fixture — and the test records
  it, with a warning that **any test wanting different seeds to differ needs a maze with
  junctions.**
- **A journey reaches a decision rather than running out.** The driver has a turn limit as
  well as a decision condition; a journey that hit the limit would silently report whatever
  it had.
- **The END-3 board is checked to be discriminating** before it is used as one.

## Deliberately not re-asserted

The resolver's step order (`test_turn.py`), the session's three states
(`test_session.py`), the status strings (`test_status.py`), the composer's mapping
(`test_frame.py`), the painter (`test_surface.py`). **These are journeys, not a second
opinion.** END-3 in particular is now structural in the resolver, so what this establishes
is that the *assembled game* behaves that way end to end.

## Headless, and a correction to how I have been evidencing that

`build_game(master=tk_root)` builds the window withdrawn and **`start()` is never called**,
so no timer runs and nothing reaches the screen. `Game.tick()` is public and is what drives
time. One Tk interpreter in the whole suite, because a second `tkinter.Tk()` can crash this
build.

**The correction, which applies to every report I have filed this run.** I have been
quoting `lsappinfo visibleApplicationCount` as evidence that no window reached the screen.
**It is not that.** Measured just now: baseline 8, **9 while a withdrawn Tk root that never
maps anything is alive**, 8 again when it exits. It counts *registered applications* — S-1's
Dock tile — not windows. The baseline also drifts with what the user is doing; it was 7
earlier this run and is 8 now, so only the delta means anything.

So: that metric shows **no stray application was left registered**, which is real and worth
keeping. What shows no window is the Tk-level assertion — `state() == "withdrawn"`,
`winfo_ismapped()` false, `winfo_viewable()` false — and those are what this suite asserts,
including after a whole game has been played.

## Suite state

```
.venv/bin/python -m pytest -q          →  890 passed, 0 failed, 0 skipped, 4 deselected
```

Repository root, `.venv` from `/usr/bin/python3` 3.9.6, pytest 8.4.2, on this branch —
which is WI-14's surface commit plus this file. **WI-16 adds 33.** Crash reports **14, none
new**; the last was at 02:00:51Z.

## What needs a human

Nothing new. **One thing WI-16 must not be read as ticking:** lane B has reported that
**WIN-4 is not met** — the shipped anchor reader follows nothing and the route is still an
open question with the user. No journey here touches placement, and none should be taken to
imply otherwise.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
