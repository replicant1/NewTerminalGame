# WI-11 — the game loop

**Branch** `wi-11-game-loop`. **Lane** A (DEV-A), M2. **Local mode.**
**Suite** `python3 -m unittest discover` — **570 passed, 0 failed, 0 skipped**.
**Windows opened: none.** The loop was measured against a real clock with a stub
screen; no terminal and no window were needed.

Requirements: **GHOST-1, CTRL-1, CTRL-2, CTRL-4, CTRL-5, START-5, END-5, END-6,
SCRN-7**.

## Exactly what was integrated, and in what order

Recorded so the technical lead can check the tree it produces on `main` is the
one these 570 tests ran against.

| Step | What | Result |
| --- | --- | --- |
| 1 | Cut `wi-11-game-loop` from **`wi-6-status-line` at `a88d511`** | — |
| 2 | Merged **`wi-9-ghost-policy` at `dee3312`** | clean, no conflicts; 5 files added; suite **435** |
| 3 | Merged **`main` at `ee0b954`** | clean, no conflicts; 23 files; suite **525** |
| 4 | WI-11's own work | suite **570** |

**`main` was not where I was told it was, and this is worth flagging.** I was
given `c4171fb`, then corrected to `8c4e2ce` with "no queued branch has landed;
the lockout is unchanged". `main` is in fact at **`ee0b954`** and **five
branches have landed**: `679a629` wi-3-end-to-end-join, `c708a39`
wi-7-game-state, `89e5d0a` wi-5a-wall-glyphs, `6694d56` wi-8-player-move,
`ee0b954` wi-9-ghost-policy. `8c4e2ce` is real but six commits back.

So `wi-3-end-to-end-join`, `wi-7-game-state` and `wi-8-player-move` **no longer
need merging — they are on `main`.** What remains of my chain is
`wi-10-rules-outcome`, `wi-6-status-line` and this. I verified with `git log`
rather than accepting either sha, which is the remedy DEV-B named when it caught
the same class of error.

## What is new

| File | What it is |
| --- | --- |
| `terminalgame/application/__init__.py` | The Application layer — new package. |
| `terminalgame/application/loop.py` | `play`, `quits`, `direction_of`, `next_deadline`, `TICK_SECONDS`. |
| `tests/loop_fakes.py` | `FakeClock`, `ScriptedScreen`, `CountingGhost`, `StillGhost`. |
| `tests/test_game_loop.py` | 45 tests. |
| `terminalgame/domain/rules.py` | **Changed** — one fix, found by this item. |
| `docs/findings/WI-11-the-tick-against-a-real-clock.md` | The real-clock measurement. |

```python
from terminalgame.application.loop import play

final_state = play(screen, state, random_source, compose)
```

## Caution C7 is the whole of the risk

A single thread can only wait in one place, so **the key read's timeout *is* the
ghost's schedule**. It is recomputed every pass from the clock as the time
remaining to the next tick.

Two things that would look right and be wrong:

- **A fixed timeout** restarts the wait on every key, so a player holding an
  arrow postpones the ghost indefinitely — GHOST-1 broken silently.
- **A sleep** would not hand over a key that arrived early until the sleep ended.

The deadline advances by **whole ticks from the schedule**
(`next_tick += TICK_SECONDS`), never `now + tick`, so the loop's own work is not
added to every interval. After a stall it catches up **without firing the ticks
it missed** — a burst of ghost moves to "catch up" would teleport it across the
maze, which is worse than having missed them.

### The test that a fixed timeout would fail

Two runs, five seconds of clock each. One with nothing pressed; one with fifty
keys at irregular moments. **The tick counts must be equal.** A fixed-timeout
loop ticks fewer times in the run with keys.

The keys are deliberately *not* arrows, so the state cannot change and the only
difference between the runs is how often `read_key` returns early — the property
under test, isolated. And the test asserts the noisy run really did read far
more keys, so it cannot pass by the keys being dropped. A second version repeats
the comparison **with** arrow keys, on a state where the game cannot end, so the
claim holds where the state really is changing.

### Measured against a real clock, too

An injected clock proves the arithmetic and nothing about the machine.

| asked for | elapsed | ticks | ticks/second |
| --- | --- | --- | --- |
| 2.0 s | 2.007 s | 14 | 6.975 |
| 4.0 s | 4.011 s | 28 | 6.981 |

Target 7.000; error under 0.4 %. **The anti-drift property is in the counts, not
the rate**: 14 ticks in two seconds and 28 in four — exactly double for exactly
double the time. A loop rebasing its deadline on the present would show fewer
than twice. Full detail in `docs/findings/WI-11-the-tick-against-a-real-clock.md`.

## No second enforcement of END-5

As ruled. **There is no `if the game is over` around the player's move.** The
loop calls `advance_player` and the Domain refuses; one enforcement, with the
Domain's whole suite behind it.

**The redraw needs no check either, and this is the part I would most want
read.** The loop redraws when the state has *changed*, detected by **identity** —
the Domain returns the same object when nothing happened, the convention WI-8 set
for CTRL-3 and WI-10 kept. Once the game is over nothing changes, so nothing is
redrawn. END-5's "the picture stands" is not asserted in the loop at all; it
falls out of the Domain's guarantee. That is the property the lead described:
the loop-side behaviour is an *optimisation*, and forgetting it could not have
broken anything.

**One `is_over` check does exist**, and it earns its place honestly: it stops the
ghost's policy being consulted for a move that would be thrown away, which would
also draw on the random source. **Delete it and the loop is still correct** —
that is the test of whether something is an optimisation or a rule, and it is
said in the module docstring so nobody later mistakes it for a guard.

The tick routes through `ghost_policy.ghost_move` (the pure policy, not handed
the player — GHOST-4) and then WI-10's `advance_ghost`. **Not
`ghost_policy.move_ghost`**, which does not guard on outcome and would take the
ghost half of END-5 back out of the Domain.

## A fix in WI-10 that this item found

`advance_ghost` now returns the state it was given when the ghost was told to
**stay where it is**. `GameState.with_changes` builds a new object whatever it is
handed, so a ghost with nowhere to go (WI-9's `NOWHERE_TO_GO_MEANS_STAY_PUT`)
looked like a change, and the loop redrew a picture identical to the one already
on screen.

Every other step in the Domain already returned the same state when nothing
happened. This makes the convention hold **without exception**, which matters
more now than it did, because the loop's redraw rule depends on it.

Found by a loop test failing, not by inspection — `test_nothing_is_redrawn_while
_nothing_moves` went red with 8 frames instead of 1.

## CTRL-2 and STAT-2, placed here deliberately

- **CTRL-2's behavioural half** — a tick moves the ghost and **not** the player.
  Tested by running with nothing pressed and asserting the ghost moved several
  times while the player and the score did not change. (The structural half was
  discharged in WI-8: `GameState` has nowhere for drift to live.)
- **STAT-2's "kept up to date"** — the status module cannot fail at it, so it
  becomes the loop redrawing when the score moves. Tested by asserting the
  sequence of scores actually drawn is `[0, 1]` across the move that eats a dot.

## What the frame builder is, and is not

**Injected, not imported.** WI-5b is not in this tree — WI-12 is the wiring item
and depends on it — and the loop has no business knowing how a state becomes a
picture. I read DEV-B's `compose(state, status_line=None)` signature off
`wi-5b-frame-composition` so the injection point matches what WI-12 will pass;
the wiring will be `compose(state, status_line=status_row(state))`.

## Deviations, for a ruling

1. **`terminalgame/application/` is a new package.** Plan §3 names the layer;
   nothing had created it. DEV-B has no application module on either branch, so
   no collision — but it is a new shared path and worth knowing about.
2. **`play` takes `ghost_move` as a parameter**, defaulting to the real policy.
   The plan asks for an injected clock and key source; this is the same idea
   applied once more, and it is what lets a test *count ticks* exactly rather
   than infer them from the ghost's position.
3. **`next_deadline` is public.** It is the anti-drift arithmetic and it is
   worth testing on its own, including the stall case, which is hard to provoke
   through the loop.

## A deliberate omission, recorded so nobody "fixes" it

**`tests/test_layering.py` is untouched.** The Application layer has no
purity class in it, and I did not add one: WI-12 is the wiring item and is the
natural place to decide what Application may import, and DEV-B is actively
editing that file for WI-5b. Adding a class there now would be an edit to the
one shared file in the middle of the other lane's item, to state a rule whose
shape is not yet settled. **This absence is a decision, not an oversight.**

Note that `LayerRuleTest` already sweeps every file under `terminalgame/`, so
`loop.py` is covered for `curses` and `subprocess` today.

## Assumptions

**Q1 is load-bearing here and remains an assumption.** A1 — the picture freezes
at the ending and the window closes when the player quits — is what makes END-5
and END-6 mean "stop moving, keep drawing nothing, wait for `q`". The loop
implements exactly that. **Not recorded as a ruling.** Flipping A1 would change
where the loop returns, not how it keeps time.

## Contradictions found

**None.** The nine requirements are consistent with each other and with the
Domain beneath them.

One observation: **GHOST-1's "about seven times a second" is the only timing
number in the specification, and "about" is doing real work.** The measured
6.98 is within 0.4 % of 7.0, and the error is the loop's own overhead. Nothing
in the specification says what tolerance is intended; I have treated it as
comfortably met rather than asking, because the alternative reading — that 6.98
fails — would make the requirement unsatisfiable on any real machine.

## What needs a human

1. **Whether the game *feels* right at seven ticks a second** — whether the
   ghost is too fast to escape or too slow to fear. That is a judgement about
   play, not a measurement, and `TICKS_PER_SECOND` is the one constant.
2. **Nothing else.** No window was opened; the picture itself belongs to WI-12
   and WI-14b.

## Commits

| | |
| --- | --- |
| `b90d6ea` | WI-11: the game loop |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
