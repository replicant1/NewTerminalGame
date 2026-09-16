# WI-19 — The scripted game

**Developer:** DEV-B · **Branch:** `r6/wi-19-scripted-game` · **Base:** `main`
**Iteration:** M4 · **Depends on:** WI-15 (landed)

A whole game played headless, in the suite, as a sequence of asserted
pictures. **It never opens a window, it builds no clock, and it does not
assemble the shell.**

## Both of amendment 5's corrections are honoured

**There is no clock and none was built.** A game here is a loop over three
calls — `tick()` for the ghost's turn, `move()` for a key, `quit()` to end
it. Nothing in this branch constructs a clock or consumes one.

**No status-line string is authored anywhere in it.** A7 forbids writing one
outside WI-13. Expected pictures are built by
`expected_picture(maze_rows, score, outcome)`, which composes row 29 from
**WI-13's own `status_text`** and joins it onto the maze rows a test types.
If the user ever rules on contradiction C-3 or C-4, these tests follow WI-13
instead of needing to be retyped — which is the only property A7 ever had.

**274 is asserted nowhere.** There is a test that the cleared score is *not*
274 and that it falls in the measured 259–271 band (A9, contradiction C-6).

## The win path needs no lucky seed

The win path runs on a **ring** of eight corridor squares. Every square of a
ring has exactly two corridor neighbours, so every ghost choice is forced —
straight on where it can, and the single non-reverse exit at each corner —
and setting the ghost's initial heading in the state makes the whole walk
deterministic. Tick, then move, seven times round: the ghost stays one
square ahead and the player eats up behind it.

The opening picture, asserted character for character:

```
╔═══════╗
║▐█▗█▖▪ ║
║ ▪ ■ ▪ ║
║ ▪ ▪ ▪ ║
╚═══════╝
```

and the final one, after seven moves:

```
╔═══════╗
║▗█▖    ║
║▐█▌■   ║
║       ║
╚═══════╝
```

`▐█▗█▖` in the first is not a typo and there is a test naming it: two
squares two columns apart give two three-column motifs that **share a
column**, and END-4's draw order decides which is seen.

## END-3, end to end in a whole game

The plan singles this out, because END-3 lives in the order of two
statements and an ordinary test of the two endings separately would still
pass if they were swapped. Three corridor squares, the player at one end and
the ghost at the other:

- the player eats the middle dot — now **the only dot left is under the
  ghost**;
- the player moves onto it, which **empties the dot field and meets the
  ghost on the same turn**;
- the outcome is `CAUGHT`, not `CLEARED`.

There is a separate test that the dot field really did empty on that turn,
because without it the first could pass for the wrong reason — a loss that
happened before the win condition was ever in play. And a third that the dot
**was still taken and still scored** (A8).

## The real seeded game

A generated 19 × 29 maze, seed 4, played to a win by a deliberately simple
planner: head for the nearest remaining dot by the shortest route that does
not walk through the ghost, and tick after every move.

| | |
| --- | --- |
| Outcome | **CLEARED** |
| Dots at the start / score | **262 / 262** |
| Moves | 360 |
| Score in the measured band | 259 ≤ 262 ≤ 271 ✓ |
| Score is 274 | **no** |

The planner is not clever and does not need to be — the ghost does not hunt
(GHOST-4), so a player that keeps off the one square it occupies clears the
maze.

## The property this item rests on, pinned

Amendment 1 asks WI-19 to pin that seeded generation is independent of
`PYTHONHASHSEED`, because it is the kind of invariant a later change undoes
by iterating a set and the failure would look random rather than causal.
`PYTHONHASHSEED` is fixed when the interpreter starts, so the test **runs
the same seeded game in subprocesses at two different hash seeds** and
compares SHA-256 digests over every frame, against the in-process digest.
Plus the ordinary in-process checks: the same seed plays the same game
twice, two different seeds play different games.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 637 tests — 637 passed, 0 failed, 0 skipped
```

32 are new here. None opens a window; all six of WI-10's guard rules stay
clean.

## Two of my own fixtures were wrong, and the tests caught both

Worth recording, because in both cases the fix was to the fixture or the
harness and **not** to the assertion.

1. A *"the player walks into the ghost"* test came back **CLEARED**. On the
   three-square corridor, eating the middle dot is already eating the last
   dot, so the game was won before the player could reach the ghost. Moved
   to a five-square corridor, where dots remain after the collision, and
   added an assertion that they do — so the test is about END-1 and not
   accidentally about END-2.
2. A frame-count assertion was off by one. My planner **ticked once after
   the winning move**. The session ignores it, so nothing was wrong with the
   game — but it is a turn that shows no picture, and a real loop would not
   make it. **I fixed the planner.** The assertion now compares against
   turns counted by the harness rather than arithmetic modelled from the
   planner, so it cannot drift again.

## Suite cost, and what I did about it

WI-19 first took the suite from 4.8s to **13.1s**, and 5.1s of that was the
`PYTHONHASHSEED` subprocess replay. The digest is now over two seeded games
of twenty-five turns rather than three of forty, and the in-process replay
over sixty turns rather than a hundred and twenty. **The suite is 10.6s.**
A short game pins reproducibility no worse than a long one and costs every
developer the difference on every run.

The remaining 2.6s is the real 19 × 29 game being played to a win, which is
the point of the item.

## Deviations needing a ruling

**The hand-built games construct a `GameState` directly** rather than going
through `new_session(maze)`. The plan says "a seeded maze"; a seeded 19 × 29
maze cannot have its picture read as text, and the item also says "the
frames asserted as text". So both are here: hand-built mazes small enough to
assert whole pictures, **and** a real seeded game for the score, the band
and the replay. Flagging the reading rather than assuming it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
