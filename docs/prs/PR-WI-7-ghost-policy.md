# WI-7 — The ghost's movement policy

**Branch** `wi-7-ghost-policy` · **base** `main` (merged, WI-6 included) ·
**lands** GHOST-2, GHOST-3, GHOST-4, SCORE-4, END-1 (ghost walks into player),
END-5 (the ghost half).

**Suite:** `/usr/bin/python3 -m unittest discover -s tests` →
`Ran 567 tests in 11.478s` / `OK (skipped=2)`. That is `main`'s 515 plus this
item's 52. Zero failures, zero errors, the 2 skips are the pre-existing ones.

---

## What landed

### `termgame/rules.py` — two functions appended

`ghost_heading(maze, ghost, heading, rng) -> Direction` — the policy, three
clauses in the order they are tried:

1. **GHOST-2.** If the square straight ahead is open, carry on: same heading,
   one square on. Tried **first**, so a ghost running through a junction with
   side arms keeps going straight and never touches the random source.
2. **GHOST-3.** Otherwise draw uniformly from the open directions **other than
   the reverse** of the current heading.
3. **GHOST-3, last clause.** Only if that leaves nothing — a cul-de-sac — turn
   back the way it came.

`move_ghost(state, rng) -> GameState` — one tick. Guards on
`outcome != PLAYING` and returns the state **by identity** (END-5); moves the
ghost; carries `dots` and `score` across untouched (SCORE-4); sets `CAUGHT` if
the ghost's new square is the player's (END-1).

**GHOST-4 is enforced by absence.** `ghost_heading` is not handed the state at
all, so there is no player in its scope to notice. `move_ghost` reads
`state.player` exactly once, in the equality test that decides END-1, and by
then the move is already chosen.

### `tests/test_rules_ghost.py` — 52 tests

Every board hand-written and drawn in the docstring of the test that uses it:
`STRAIGHT` (a blind corridor), `CIRCUIT` (the GHOST-4 board), `CROSS` (a
lattice with a four-way junction), `TEE` (a T entered along its stem),
`CULDESAC` (a degree-one square). A last class checks each board is the shape
its picture claims, so a test cannot end up asserting something other than
what it says.

---

## The shared module — how the WI-6 collision went

**Three conflict hunks in `termgame/rules.py`, and all three were mechanical.**
Both items appended to the same two places:

| Hunk | WI-6 | WI-7 | Resolution |
|---|---|---|---|
| module docstring header | "starting a game, and what a move does" | "starting a game, and the ghost" | one opener naming all three |
| `__all__` | `move_player` | `ghost_heading`, `move_ghost` | both kept |
| end of file | `move_player` section | ghost section | `move_player` first, then the ghost pair — the order `ARCHITECTURE.md` §5.4 sets them out in |

**Nothing about the two transitions disagreed**, so there is no `ASK` here.
Worth recording that the mitigation the plan designed actually worked:
**neither item introduced a shared helper.** WI-6 needed `Maze.is_wall`, WI-7
needed `Maze.is_open` and `Maze.open_directions`, and WI-1 had already shipped
both on the maze value. The two halves of END-1 meet without touching —
`move_player` owns the player walking into the ghost, `move_ghost` owns the
ghost walking into the player, and each has its own test asserting its own
direction. Both return the **identical object** rather than an equal copy for
their respective no-op (CTRL-3 for the player, END-5 for the ghost); that was
arrived at separately in two worktrees and happens to agree.

The diff against `main` after the merge touches four files and is purely
additive to `rules.py`.

---

## The finding that changed the GHOST-4 test

Full write-up and numbers in **`docs/findings/WI-7-ghost-decision-points.md`**.
In short:

The ghost makes a **genuine** random choice only at a square of degree three
or more **entered along its one blocked direction**. A degree-four square is
never a decision point; a degree-three square is one from exactly one of its
three arms. On a regular lattice that almost never recurs.

**Measured:** from every corridor square and every heading on the `CROSS`
lattice, a 200-tick run makes **at most one** genuine choice and then settles
into a cycle that makes none — so the entire path is the same whatever seed it
is handed.

The first draft of the GHOST-4 test ran on `CROSS`, and it passed. **It would
also have passed against a ghost that hunted the player**, because the ghost
never reached a fork at which hunting could show. Green, and proving nothing.

Two changes fixed it, and both are in the branch:

1. GHOST-4 now runs on `CIRCUIT`, a board built so that every circuit passes
   through a decision (20 in 200 ticks, measured), **and** on a real generated
   maze (13–15 in 300, measured).
2. The vacuity guard does not re-implement the policy — that would be
   comparing the policy with itself. It changes the **seed** and requires the
   path to change. *A path that moves when the seed moves and stands still
   when the player moves is reading the seed and not the player.*

That fact is also asserted as a test in its own right
(`test_a_regular_lattice_gives_the_ghost_almost_nothing_to_decide`), so the
finding cannot go stale unnoticed.

---

## The named GHOST-4 test

Present and passing, in `TestGhost4TheGhostDoesNotHunt`:

- `test_three_player_positions_give_three_identical_ghost_paths` — the plan's
  test, on `CIRCUIT`, 200 ticks, player at (7, 1), (7, 4), (7, 7) on a strip
  walled off from the ghost's circuit so no END-1 catch can cut a run short
  and make two paths agree for the wrong reason.
- `test_that_comparison_is_not_vacuous` — the run is 200 ticks, wanders over
  more than eight squares and more than two headings, never ends, **and comes
  out different under three other seeds**.
- `test_the_player_may_even_be_moved_between_ticks` — stronger than three
  fixed positions: the player is teleported to a different square every single
  tick and the ghost's path is still identical to the run where it never moved.
- `test_three_player_positions_on_a_real_generated_maze` — the same again on a
  board the game would actually deal (seed 23, 300 ticks), with the three
  player squares chosen from cells the reference run never visits.

That the walled-off strip really is unreachable is itself flood-filled and
asserted, for both `CROSS` and `CIRCUIT` — the whole comparison rests on it.

---

## Deviations needing a ruling

**One, additive.** `ghost_heading` **raises `ValueError`** when the ghost's
square has no way on at all. `ARCHITECTURE.md` §5.4's pseudocode would return
`reverse(dir)` there, which walks the ghost into a wall.

- It is **unreachable in a real game**: MAZE-5 keeps every corridor square at
  degree two or more, so a generated maze cannot produce a walled-in square.
  Only a hand-written board can, and then it is a bug in the board.
- It follows the precedent already in this module: WI-5's `starting_heading`
  raises on exactly the same condition, with almost the same message.
- One test covers it
  (`test_a_walled_in_ghost_is_refused_rather_than_walked_into_a_wall`).

Say the word and it becomes a silent reverse instead; it is one `raise`.

**Nothing else.** No shared helper, no change to WI-5's or WI-6's functions, no
change to `model.py` or `maze.py`, no new module, no new dependency.

---

## Contradictions found in the plan or the architecture

**None.** One thing the plan says that turns out to be more load-bearing than
it reads, though, worth flagging rather than burying: the plan's instruction to
hand-build the cul-de-sac "because a generated maze never contains one" is
right, and the same reason has a second consequence it does not mention —
**MAZE-5 means the ghost never reverses on a generated maze at all**. Arriving
somewhere, the way back is open, and degree ≥ 2 guarantees at least one other
way on. That is asserted over 30 seeds × 120 ticks
(`test_the_ghost_never_reverses_on_a_generated_maze`), and it is the sharpest
single check that GHOST-3's ordering is right.

## Mutation checks

Not applicable — the user's explicit decision that this workflow does not run
them.

## What needs a human

Nothing in this item. It is pure: no terminal, no window, no clock. The AST
purity guard covers `rules.py` automatically and did not fire.

## A note on the repository

`orchestration/static/index.html` does **not** appear in this branch's diff.
The user's own unpushed work on `orchestration/` has not been touched. The
diff against `main` is four files: `termgame/rules.py`,
`tests/test_rules_ghost.py`, `docs/progress/wi-7-ghost-policy.md`,
`docs/prs/PR-WI-7-ghost-policy.md`, plus
`docs/findings/WI-7-ghost-decision-points.md`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
