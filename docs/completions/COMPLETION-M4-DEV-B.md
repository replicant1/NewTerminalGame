# M4 — DEV-B's lane, complete

**Developer:** DEV-B · **Iteration:** M4, *the game itself* ·
**Mode:** non-local, real pull requests, merged by me

DEV-B's M4 lane is WI-19 alone. Built, merged and green.

---

## What landed

| Item | Branch | PR | State |
| --- | --- | --- | --- |
| **WI-19** — the scripted game | `r6/wi-19-scripted-game` | [#58](https://github.com/replicant1/NewTerminalGame/pull/58) | **merged** |

| File | |
| --- | --- |
| `tests/scripted.py` | The harness: `ScriptedGame`, `expected_picture`, `route_between`, `eat_everything` |
| `tests/test_scripted_game.py` | 32 tests — the whole-application test |

---

## Suite, as left

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 693 tests in 10.9s

OK
```

**693 passed, 0 failed, 0 skipped**, on `main` with WI-14 and WI-17 landed.

---

## Both of amendment 5's corrections honoured

**No clock was built and none consumed.** A game here is a loop over
`tick()`, `move()` and `quit()`.

**No status-line string is authored anywhere in the item.** Expected
pictures compose row 29 from WI-13's own `status_text` and join it onto the
maze rows a test types, so they follow WI-13 if the user ever rules on
contradiction C-3 or C-4 — which is the only property A7 ever had.

**274 is asserted nowhere**, and there is a test that the cleared score is
*not* 274 and does fall in the measured 259–271 band (A9, C-6).

---

## The three things the plan singled out

**The win path needs no lucky seed.** It runs on a ring of eight corridor
squares. Every square of a ring has exactly two corridor neighbours, so
every ghost choice is forced — straight on where it can, the single
non-reverse exit at each corner — and with the ghost's initial heading set
in the state the whole walk is deterministic. Both the opening and the final
pictures are asserted character for character.

**END-3 is proved in a whole game, not only in the resolver's unit test.**
Three corridor squares; the player eats the middle dot, so the only dot left
is under the ghost; the next move **empties the dot field and meets the
ghost on the same turn**, and the outcome is `CAUGHT`. A second test asserts
the field really did empty on that turn — without it the first could pass
for the wrong reason, a loss that happened before the win condition was ever
in play. A third asserts the dot was still taken and still scored (A8).

**The `PYTHONHASHSEED` property is pinned.** `PYTHONHASHSEED` is fixed at
interpreter start, so the test runs the same seeded game in **subprocesses
at two different hash seeds** and compares SHA-256 digests over every frame,
against the in-process digest.

### The real seeded game

| | |
| --- | --- |
| Maze | generated 19 × 29, seed 4 |
| Outcome | **CLEARED** |
| Dots at the start / final score | **262 / 262** |
| Moves | 360 |

---

## Two of my own fixtures were wrong, and the tests caught both

In both cases the fix was to the fixture or the harness, **not** the
assertion.

1. A *"the player walks into the ghost"* test came back **CLEARED**. On a
   three-square corridor, eating the middle dot is already eating the last
   dot, so the game was won before the player could reach the ghost. Moved
   to a five-square corridor and added an assertion that dots remain, so the
   test is about END-1 and not accidentally about END-2.
2. A frame-count assertion was off by one, because **my planner ticked once
   after the winning move**. The session ignores it, so nothing was wrong
   with the game — but it is a turn that shows no picture and a real loop
   would not make it. I fixed the planner, and the assertion now compares
   against turns counted by the harness rather than arithmetic modelled from
   the planner, so it cannot drift again.

---

## Suite cost, and what I did about it

WI-19 first took the suite from 4.8s to **13.1s**, and 5.1s of that was the
`PYTHONHASHSEED` subprocess replay. The digest is now over two seeded games
of twenty-five turns rather than three of forty, and the in-process replay
over sixty turns rather than a hundred and twenty. **The suite is 10.9s**,
of which 2.6s is the real 19 × 29 game being played to a win — which is the
point of the item and worth paying for.

---

## Deviations needing a ruling

**The hand-built games construct a `GameState` directly** rather than going
through `new_session(maze)`. The item asks for "a seeded maze" *and* for
"the frames asserted as text", and a seeded 19 × 29 maze cannot have its
picture read. So both are here: hand-built mazes small enough to assert
whole pictures, and a real seeded game for the score, the band and the
replay. Flagging the reading rather than assuming it.

---

## Still open, carried forward from earlier iterations

- **The ownership-table contradiction** (M1) — amendment 1's table gives
  directions to DEV-B, its own first-lander rule gives them to WI-5. The
  tree follows the rule; the table row is what is wrong.
- **`heading=None`** in WI-7's `next_step`, additive to the plan.
- **The modifier-state question on `KeyPress`** (WI-9), with DEV-C,
  unanswered. My recommendation was not to change it.
- **A maze must *fit* the picture** rather than be exactly 19 × 29 (WI-12).
- **`tk_grid.create_surface` and `measure_metrics` have no automated test**
  (M0) — exercised for real by `tools/the_look.py` and WI-4.

**For a human**, and this is the one that matters most: the three questions
in `docs/findings/WI-16-the-look.md` are all still unanswered, and they now
cost one command and about 25 seconds:

```
/usr/bin/python3 tools/the_look.py --seconds 8
```

**SCRN-3 — do the blue double lines actually join up?** — is the only
requirement on this run that no measurement can close.
