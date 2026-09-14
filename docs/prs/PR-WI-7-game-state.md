# WI-7 — the game state and the opening position

**Branch** `wi-7-game-state`, cut from `main` at `c4171fb`.
**Lane** A (DEV-A), iteration M1. **Local mode** — this file stands in for the
pull request; nothing pushed, no `gh` used, not merged.
**Depends on** WI-4, which is merged.
**Suite** `python3 -m unittest discover` — **309 passed, 0 failed, 0 skipped**.
**Windows opened: none.** Pure domain; nothing touched the desktop.

Requirements: **START-1 to START-5**, and **GAME-3**.

## What this is

The state vocabulary the rest of the game speaks — the maze, the player's
square, the ghost's square and heading, which squares still hold a dot, the
score, and a three-case outcome — plus the rules that open a game on it.

| File | What it is |
| --- | --- |
| `terminalgame/domain/game_state.py` | `Outcome`, `GameState`, `new_game` / `new_game_with` / `open_game_on`, `nearest_to_centre`, `furthest_from`, `opening_heading`, `squared_distance`, `DISTANCE_METRIC`, `NoCorridorToStartOn`. |
| `tests/test_game_state.py` | 51 tests. |
| `tests/test_layering.py` | **Extended**, not created — two tests and one helper. |

Names collide with nothing: the existing test files are `test_maze.py`,
`test_maze_generator.py`, `test_layering.py`, `test_screen_port.py`,
`test_curses_adapter.py`, `test_game_main.py`, `test_real_terminal.py`,
`fake_terminal.py`, and my own `test_launcher_*.py` / `launcher_fakes.py`.
`test_game_state.py` is under none of those prefixes. The only shared file is
`tests/test_layering.py`, already on `main` — an edit to a merged file, not a
race to create a new one.

## The surface WI-8, WI-9, WI-10, WI-6, WI-5b and WI-11 will speak

```python
from terminalgame.domain.game_state import GameState, Outcome, new_game

state = new_game(seed)          # a whole game: maze, both actors, every dot
state.maze                      # the Maze from WI-4
state.player                    # (x, y)
state.ghost                     # (x, y)
state.ghost_heading             # a Direction, from the first instant
state.dots                      # frozenset of (x, y)
state.score                     # int
state.outcome                   # Outcome.PLAYING / CAUGHT / CLEARED

state.dot_at(square)            # is there still a dot there
state.dots_remaining            # how many are left  — WI-10 wins on nil
state.is_over                   # outcome is not PLAYING
state.with_changes(score=1)     # a NEW state; this one is untouched
```

`GameState.FIELDS` is the field list, and there is a test pinning it exactly,
because six later items depend on this vocabulary and a field appearing or
vanishing quietly would reach all six.

**The state is immutable.** Assigning to a field raises; `dots` is a
`frozenset`; `with_changes` is the only way anything moves, and it refuses a
field that does not exist. Two reasons, both practical rather than stylistic:

- WI-8's requirement is that a move into a wall changes **nothing at all,
  including the score**. Against an immutable state that is one assertion —
  `moved == before` — rather than a hunt for a mutation that may not have a
  visible symptom.
- WI-9's ghost policy is handed a state to read. It cannot alter one by
  accident, and `GameState` is hashable, so a test can put states in a set.

It follows `Maze`, which WI-4 made immutable and hashable for the same reasons;
the domain is consistent about this rather than half and half.

## START-2's metric — an assumption, stated, and pinned

**Straight-line (Euclidean) distance across the grid**, compared **squared**.

The user has not answered Q3. A6 says "straight-line grid distance", and
straight-line is what Euclidean means — but **Manhattan and Chebyshev satisfy
START-2's words just as well**, and all three keep the actors well apart. So
this is recorded as an assumption and it is cheap to flip:
`squared_distance` is the only place it is decided, and `DISTANCE_METRIC` is
the only sentence that changes.

It is not a distinction without a difference, and the tests say so rather than
asserting it. From the origin, **(0, 5) is further than (3, 3) under
straight-line distance — 25 against 18 — and nearer under Manhattan — 5 against
6.** START-2 puts the ghost on the *furthest* square, so the two metrics start
it in different places on the same maze. `test_it_is_not_manhattan` and
`test_it_is_not_chebyshev` would fail if the metric were swapped, which is the
point of having them.

Squared, never square-rooted: ordering by `d²` is the same as ordering by `d`
for non-negative distances, and it keeps the arithmetic in exact integers, so
squares that are genuinely equidistant tie **exactly** rather than tying or not
according to floating-point error.

**The same metric serves START-1's "nearest the middle"**, so there is one
metric in the item rather than two to keep consistent.

## Two decisions the requirements leave open

**Ties break in reading order** — smallest `y`, then smallest `x`. Stated in the
sort key rather than left to rely on the order `corridor_squares()` happens to
return, so it stays true if that order ever changes. There is a test on a
hand-built maze that *first checks a tie actually exists* — four squares equally
near the centre, two equally far from the player — and then checks which one is
chosen. A tie-break test on a maze with no tie proves nothing.

**The centre is compared in doubled coordinates.** The centre of a grid `width`
across sits at `(width - 1) / 2`, a half-square when the width is even. Rather
than round it and have to justify rounding one way, both the centre and each
square are doubled, so `dx = 2x - (width - 1)` is an exact integer on every
grid. 19 x 29 is odd both ways so it changes nothing there — it is what makes
the other grid sizes in §11.9 exact rather than approximately right.

## START-5, and a consequence of START-3 that WI-10 depends on

**"The ghost is already moving"** means the ghost has a heading before anything
is pressed. It is drawn from the random source among the ghost's **open
neighbours**, so it is always a way the ghost can actually travel and always
reproducible from the seed. A fixed initial heading would point into a wall on
most mazes, and the ghost's first move would be a turn rather than a move.
MAZE-5 guarantees at least two ways on, so the choice is never empty on a
generated maze; a hand-built square with none falls back to a fixed direction
rather than failing, because a ghost with nowhere to go is a maze problem and
not a reason for opening a game to fail.

**START-3 excepts the player's square and no other, so the ghost starts on a
square that does hold a dot.** That is what makes END-3 reachable at all — the
last dot of a game can be the one underneath the ghost — and **WI-10 depends on
it**, so it is pinned with its own test here rather than left as a consequence
nobody wrote down.

## How the placement rules are tested

**By searching the maze, not by recomputing the formula.** For every seed:
no corridor square is nearer the centre than the player's, and none is further
from the player than the ghost's. A test that reapplied `min` with the same key
would agree with the code however wrong they both were.

Also checked: the player is always on corridor; the ghost is always on corridor
and never on the player; the dots are exactly the corridor squares less the
player's; the count is the corridor count less one; no dot is ever on a wall;
score zero; outcome playing; the heading is always into corridor.

Three further groups:

- **Reproducibility.** One seed names one opening position, field by field and
  not merely the maze; making other games in between does not shift it;
  different seeds give different mazes.
- **Refusal, not degradation (§11.8).** A maze with no corridor refuses and
  names **START-1**; one with a single corridor square refuses and names
  **START-2**. The single-square case still opens for the player alone, so the
  two thresholds are distinguished rather than lumped.
- **Other grid sizes (§11.9).** Five sizes other than 19 x 29, all rules still
  holding, with the extremal checks repeated. A screen dimension hard-coded
  anywhere in this module fails these outright.

## `tests/test_layering.py` — what the extension contains

Stating what it now contains rather than that it was agreed:

- `LayerRuleTest` and `DomainPurityTest`'s existing six tests are **unchanged**.
- `PACKAGE_ROOT`, `THE_ADAPTER`, `THE_DOMAIN`, `FORBIDDEN_IN_DOMAIN`,
  `python_files`, `domain_files`, `source_of`, `imports` and
  `imported_game_modules` are **unchanged**.
- `import re` added.
- One helper added, `uses_global_random(source)`.
- `test_the_domain_is_where_it_is_said_to_be` gained one line asserting
  `domain/game_state.py` is among the files scanned — the same guard WI-4 put on
  `maze.py` and `maze_generator.py`, so that moving the module cannot leave the
  scans silently checking less than they claim.
- Two tests added:
  `test_randomness_enters_the_domain_only_where_it_can_be_seeded` and
  `test_the_random_scan_can_tell_a_shared_generator_from_an_owned_one`.

**Why that rule and not another.** It is the clause of plan §3 the other purity
tests do not reach: *"randomness enters it only through a seed or a random
source passed in, so any maze or ghost behaviour can be reproduced in a test"*.
A module calling `random.choice(...)` imports nothing forbidden and depends on
nothing above it — it passes every other test in the class — while using the
interpreter's shared generator, which no test can seed, so what it produces
cannot be reproduced. WI-7 places both actors from a random source and **WI-9's
ghost policy will do the same**, which is why it is worth guarding now.

`random.Random(...)` is an owned generator and is not flagged; neither is
`random_source.choice(...)`, because the name before the dot must be exactly
`random`. The scan is checked against literal source strings in both
directions, so a clean result means it looked rather than that it was blind.

## Deviations, for a ruling

Three, all additive, none of them changing anything on `main`.

1. **`open_game_on(maze, random_source)` is public**, alongside
   `new_game` / `new_game_with`. The plan asks only for a new game. It exists so
   a test — and WI-10, which needs constructed states — can open a game on a
   maze written out by hand without going through the generator. Nothing
   downstream is obliged to use it.
2. **`new_game` takes `width` and `height`**, defaulting to the specification's
   19 x 29. Same shape as WI-4's deviation 1 and for the same reason: §11.9 says
   to keep testing at other sizes, and that needs a way to ask for one. If the
   technical lead drops WI-4's parameters, drop these with them — nothing
   downstream needs them.
3. **`NoCorridorToStartOn`** is raised for a maze with too few corridor squares.
   The plan does not mention error behaviour. §11.8 says refuse and name the
   requirement where an argument makes one unsatisfiable, which is what this
   does.

## Assumptions carried, not settled

- **Q3 / START-2's metric** — straight-line (Euclidean), as above. **An
  assumption, not a ruling.** The user has not answered.
- **A6** — "measured across the grid" read as straight-line distance between
  squares, not corridor distance. The ghost can therefore be near the player
  *along the corridors* while far across the grid; START-2 asks for the latter
  and says so explicitly.
- **Tie-breaking in reading order** is mine; nothing in the requirements
  specifies it. It needs to be *something* deterministic, and reading order is
  the order the maze already hands squares out in.

## Contradictions found

**None** in the plan or the requirements as they bear on WI-7. START-1 to
START-5 are consistent with each other and with GAME-3, and all five are met.

One observation, not a contradiction: **START-2's purpose clause — "so the two
always start well apart" — is a weaker claim than its mechanism.** Maximising
across the grid does keep them apart in the plain sense, but it says nothing
about corridor distance, and on a maze whose corridors wind, a ghost that is far
across the grid can be a short walk away. Nothing in the requirements asks
otherwise and I have not treated it as a defect; it is worth knowing before
anyone reads START-2 as a fairness guarantee. Measured over 30 seeds, the
straight-line separation is comfortably more than half the furthest the grid
could place the ghost from that player, which is what the "well apart" test
checks.

## What needs a human

1. **Is the opening position any good to play?** The requirements are a floor:
   nearest the middle, furthest away, every dot laid. Nothing in START-1 to
   START-5 asks whether the game *opens* well — whether the ghost is far enough
   to feel safe, or so far it is irrelevant for the first minute. To look:

   ```
   cd <repo root>
   python3 -c "
   from terminalgame.domain.game_state import new_game
   s = new_game()
   rows = [list(line) for line in s.maze.as_text().splitlines()]
   rows[s.player[1]][s.player[0]] = 'P'; rows[s.ghost[1]][s.ghost[0]] = 'G'
   print('\n'.join(''.join(r) for r in rows))
   print(s.player, s.ghost, s.ghost_heading.name, s.dots_remaining)"
   ```

   `#` is wall, a space is corridor, `P` and `G` are the two actors. Run it a
   few times. **If the metric wants changing, that is the Q3 decision above**,
   and `squared_distance` is the one function to change.
2. **Q3 itself** — whether straight-line is the metric the user meant. Still
   open, still an assumption.

**No window was opened and nothing touched the desktop**, so there is no
window-related human check and nothing was left on anyone's screen.

## Commits

| | |
| --- | --- |
| `c6d03a6` | WI-7: the game state and the opening position |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
