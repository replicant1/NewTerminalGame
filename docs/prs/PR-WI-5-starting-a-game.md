# WI-5 — Starting a game

**Branch** `wi-5-starting-a-game` · **base** `main` · **Dev A, round 3** ·
lands **START-1, START-2, START-3, START-4** and the state half of **START-5**.

A pure function from a seeded random source to a fresh game state. One new
module, one new test file, nothing else touched.

---

## What is in it

### `termgame/rules.py` — new

The rules module the architecture's §5.3 names. This work item lands only its
*starting* half; WI-6 and WI-7 add the two transitions to the same module, and
WI-1 has already shipped the corridor / open-neighbour query they will share,
so neither of them needs to introduce a helper here.

| Function | What it decides |
|---|---|
| `centre_of(maze)` | the middle square of the grid — exactly `(14, 9)` on the real 29 × 19 board |
| `squared_distance(a, b)` | squared Euclidean across the grid, exact integer arithmetic |
| `starting_player(maze)` | **START-1** — the corridor square nearest the middle, ties by lowest `(row, col)` |
| `starting_ghost(maze, player)` | **START-2** — the corridor square furthest from the player *across the grid*, ties the same way |
| `starting_dots(maze, player)` | **START-3** — every corridor square but the player's |
| `starting_heading(maze, ghost, rng)` | a direction open from where the ghost stands, drawn from the same `rng` |
| `starting_state(maze, rng)` | a fresh game on a maze it is handed — the seam a hand-written board plugs into |
| `new_game(rng)` | **START-1..5** — generate a maze from `rng`, then start on it |

`starting_state` is split out from `new_game` on purpose: it is what lets a
test hand in a seven-row board that a reader can check by eye, without the
test having to fabricate a 29 × 19 grid or the module having to read a file.

The tie-break is one expression, `min(candidates, key=lambda p: (score(p),
p.row, p.col))`. Because no two squares share a `(row, col)`, it never draws;
"furthest" is expressed as nearest to the negated distance, which keeps both
placement rules in one comparator rather than a `min` and a mirrored `max`.

**START-5, the state half.** `new_game` takes a random source and nothing
else. There is no title screen, no "press any key", and no parameter by which
one could be introduced — a test pins the signature so that a later item
cannot quietly add one.

### `tests/test_rules_start.py` — new

36 tests. What matters about them is stated in the section below.

---

## How the placement tests are written, and why

The plan is explicit that these assertions must be **an exhaustive recount over
the board, not a recomputation with the same expression the code uses** — a
test that re-derives the implementation's own formula proves only that the
formula equals itself.

So every placement test in this file:

- **walks the whole 29 × 19 grid by index**, asking `maze.is_corridor((r, c))`
  cell by cell. It never iterates `maze.corridors()`, never calls
  `rules.starting_player`, `rules.starting_ghost`, `rules.centre_of` or
  `rules.squared_distance`, and never imports them for comparison;
- **writes the distance out longhand with literal numbers** —
  `(r - 14) ** 2 + (c - 9) ** 2` for the centre, `(r - pr) ** 2 + (c - pc) ** 2`
  for the player — so the centre `(14, 9)` is pinned by the test rather than
  borrowed from the module;
- asserts a **property over every cell**, not an equality against a
  recomputation: *no corridor square is strictly nearer the centre than the
  player's, and any square that ties is at a higher `(row, col)`.* The ghost's
  test is the same sentence with "further from the player" in it.

A `_Recount` helper does the walk once per state and hands back plain counts and
plain sets, so each test asserts against a number it can name.

The tie-breaks are not left to chance. Two hand-written boards force them:

- a board whose exact middle `(3, 4)` is a **wall**, so four corridor squares
  tie at distance 1 and the player must take `(2, 4)` — the lowest of them;
- a board whose middle is corridor, so the player is at distance 0 and **four
  corner squares tie** for furthest, and the ghost must take `(1, 1)`.

Both are checked by hand in the test's own docstring, and separately re-checked
by the exhaustive recount.

The seeded sweep exercises both tie-breaks too, and two tests assert that it
does rather than leaving it to luck. **Measured over 200 seeds: a tie for
nearest the middle on 88 of them, and a tie for furthest from the player on all
200.** The first is because the exact centre `(14, 9)` is a *link* cell of the
lattice, so on many seeds it is a wall and the two node squares above and below
it both sit at distance 1 — which is exactly why START-1 says "nearest the
middle" and not "the middle", and why the search has to be over corridor squares
rather than a lookup. The second is because squared Euclidean distance collides
freely: `(a, b)` and `(b, a)` offsets from the player are the same distance.

## What else the tests establish

- Over 200 seeds: the player is corridor; the ghost is corridor; the ghost is
  not the player; the score is `0`; the outcome is `PLAYING`; the ghost's
  heading is one of the four directions **and is open from its own square**
  (recounted from the grid, not from `open_directions`).
- **Dots by exhaustive recount**: a cell carries a dot **if and only if** it is
  corridor and is not the player's, and `len(dots) == corridors − 1` where the
  corridor count comes from the walk. Nothing off-grid, nothing on a wall.
- The same seed gives an **identical** starting state twice — maze, player,
  ghost, heading, dots, score and outcome — and two different seeds give
  different ones.
- The heading really is drawn from the `rng`: across seeds more than one
  distinct heading is observed, so the test cannot be satisfied by always
  returning the first open direction.
- `GameState` still carries exactly the seven fields WI-1 declared — GAME-3
  holds through this item by a state built here having no eighth field.
- START-2's "rather than along the corridors" has teeth: a breadth-first search
  written out in the test finds seeds where the square furthest *along the
  corridors* is not the one the code chose, so swapping the metric for a flood
  fill would be caught.
- Degenerate boards fail loudly rather than silently: a maze with no corridor,
  and a ghost square with no way on, each raise `ValueError`.

Purity is covered without a new test: WI-1's guard discovers core modules by
listing `termgame/`, so `rules.py` came under both the static and the dynamic
check the moment it landed. It imports `random` **as a type only** — every
function that needs randomness takes a `random.Random` parameter — and makes no
module-level `random` call.

---

## Assumption A2 — recorded, not ruled

**§9's A2 is with the user and unanswered.** START-2 says the ghost starts
furthest from the player "measured across the grid rather than along the
corridors", which rules out path distance but does not say which straight-line
metric. This item proceeds on the plan's recorded assumption — **squared
Euclidean on `(row, col)`** — and that is an assumption, not a decision.

The **tie-break** is not part of A2 and is not an assumption: the plan's §5 WI-5
settles it in writing for both placements — *"ties broken by lowest row then
lowest column"*, and *"ties broken the same way"* for the ghost — and its "Tests
must establish" list repeats it. That is a decision, taken before this item
started, and it is what the code and the tests implement. Only the metric is
open.

**Blast radius, should the answer differ:** one expression and one test class.
`rules.squared_distance`, where `starting_ghost` calls it, is the expression.
`GhostPlacementTests` is the test — specifically
`test_no_corridor_square_is_further_from_the_player_than_the_ghosts`, whose
longhand `(r - pr) ** 2 + (c - pc) ** 2` would become the matching Manhattan or
Chebyshev arithmetic, and the two hand-written-board expectations
`test_hand_written_board_ghost_takes_the_lowest_of_four_tied_corners` and
`test_hand_written_board_the_four_way_tie_for_the_ghost_is_real`. Nothing else
in the module or the suite depends on the metric. This is WI-11's to apply.

What is **not** open, and is asserted independently of the metric:
`test_the_ghost_is_measured_across_the_grid_and_not_along_the_corridors`. It
runs its own breadth-first search from the player and finds seeds where the
square furthest *along the corridors* is not the square the code chose. That is
the half of START-2 the specification does settle — "rather than along the
corridors" — and it holds whichever straight-line metric the user picks.

Squared rather than rooted Euclidean is not part of the open question: the two
order the candidates identically, and the squared form is exact integers, so a
tie is a tie and never a floating-point near-miss.

---

## Relationship to `termgame/standins.py`

WI-4 shipped `standins.new_game` as a temporary starting state and **WI-9
deletes the file**. This item does not touch it, delete it, or rewire
`loop.py` to prefer `rules.new_game` — that is WI-9's job, and deleting it now
would break WI-4's tests.

**The two do not disagree about anything.** The stand-in reaches the same player
and the same ghost as `rules.new_game` for a given maze: it uses the same centre
`(14, 9)`, the same squared-Euclidean metric, and the same lowest-`(row, col)`
tie-break — spelled `max(..., key=(dist, (-row, -col)))` where this module
spells it `min(..., key=(-dist, row, col))`, which is the same order. Where they
part company is only the heading: the stand-in draws it with
`rng.randrange(len(headings))` and this module with `rng.choice(headings)`, so
the two consume the random source differently and a given seed will generally
give the two functions different headings. That is expected, affects nothing
while both exist, and disappears when WI-9 removes the stand-in.

---

## Suite

Run from the root of the worktree, the pinned command:

```
/usr/bin/python3 -m unittest discover -s tests
```

```
Ran 409 tests in 11.413s

OK (skipped=2)
```

`main` was at 373 tests, 2 skipped. 373 + 36 = 409, and the two skips are the
same two.

---

## Deviations and open points

- **No deviation from the plan's §5 WI-5 list.** Every bullet it names is
  covered.
- **Additive, and needing a ruling if you disagree:** the module is named
  `termgame/rules.py` after the architecture's §5.3, and it exports the four
  placement decisions as separate public functions rather than burying them in
  `new_game`. That is what lets the hand-written-board tests name the rule they
  are checking, and it is where WI-6 and WI-7 will add their transitions. §1 of
  the plan says names are the developer's, so I have not treated this as a
  deviation; say the word if you want it elsewhere.
- **Additive:** `starting_state(maze, rng)` alongside `new_game(rng)`. The plan
  asks only for `new_game`; the seam exists so a test can use a board a reader
  can check by hand, which the plan does ask for.

---

## Contradictions found

**None, and one thing specifically checked and cleared.** The obvious candidate
was `standins.new_game` disagreeing with `rules.new_game` about where things
start, since WI-9 will swap one for the other. Measured across 200 seeds: for
the same maze the two agree on the player's square and on the ghost's square
every time. They differ only in how the ghost's heading is drawn —
`rng.randrange(len(headings))` against `rng.choice(headings)` — which consumes
the random source differently, so the same seed gives the two functions
different headings on **99 of those 200 seeds**. That is a difference, not a
disagreement, and it disappears when WI-9 deletes the stand-in.

The plan's §5 WI-5 and the architecture's §5.3 agree with each other on every
point of this item: the centre `(14, 9)`, squared Euclidean for the ghost, the
lowest-`(row, col)` tie-break, dots as corridors minus the player, score zero,
and a random open initial heading.

---

## Mutation checks

not applicable — not part of this workflow

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
