# WI-1 — the maze as data

**Branch:** `r7/wi-1-maze-grid`, cut from `main` at `c76bc37`
**Lane:** B · **Iteration:** M0 · **Depends on:** WI-0
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**149 passed, 0 failed, 0 skipped** (56 inherited from `main`, 93 new)

A 19 × 29 grid in which each square is wall or corridor and nothing else, with
neighbour queries, plus the structural checker that answers three questions
about any grid. **The checker is WI-2's oracle**, so the half of this that
matters most is that its three answers are genuinely independent.

---

## `terminal_game/domain/maze.py`

### MAZE-1 is a property of the type, not of a call site

The plan asks that the grid be 19 × 29 and that **no other shape be
representable**. `WIDTH` and `HEIGHT` are module constants; there is no size
argument anywhere; and every route in either produces that shape or refuses:
`from_rows` rejects the wrong depth, the wrong width and a ragged row, naming
the row, and the constructor rejects any position outside the grid.

A size parameter with a 19 × 29 default would have made MAZE-1 a property of
every call site instead — true wherever somebody remembered, and false the
first time somebody did not.

### MAZE-2 is structural rather than remembered

`Square` has exactly two members. A maze is stored as **the frozenset of its
corridor squares**, so every square not in that set is wall; there is no
third state to represent and no place to put one. `from_rows` rejects an
unrecognised character, naming the row and column.

That representation also makes carving a cheap set union, equality and hashing
free, and `Maze` **immutable** — which is what lets WI-2 hold on to a maze it
has already checked while it tries a repair on a copy.

### Coordinates, fixed once

`x` runs 0–18 left to right, `y` runs 0–28 top to bottom, `Position(0, 0)` is
top-left, and **north is `y - 1`**. `y` increasing downwards matches the order
the rows are drawn in and the order the specimen picture reads in, which is
worth more than matching school graph paper. `corridors()`, `positions()`,
`walls()` and `border()` all come back in reading order, so anything built on
top — the dot field, START-2's furthest-square search, a failure message —
reads the same way twice.

### Neighbour queries

`neighbours` (the orthogonally adjacent squares that are on the grid),
`corridor_neighbours` (those you could step onto), and `ways_on_from`, which
returns a `Direction -> Position` mapping — the same information with the
direction kept, which is what a ghost needs in order to know which way it
came. A test pins that the two cannot disagree.

**Asking what is outside the grid raises rather than answering `WALL`.** A
silent `WALL` would make an out-of-bounds bug look like an ordinary dead end,
which is the hardest kind of maze bug to find.

---

## `terminal_game/domain/structure.py` — WI-2's oracle

Three questions, from three requirements:

| Function | Requirement | Returns |
|---|---|---|
| `border_breaches` | MAZE-3 | the border squares that are not wall |
| `dead_ends` | MAZE-5 | the corridor squares with fewer than two ways on |
| `unreachable_corridors` | MAZE-6 | the corridor squares cut off from the rest |

`check(maze)` answers all three at once as a `StructureReport`, whose
`is_sound` is the one-call form a generator uses to know it has finished.

### Two decisions that are really about WI-2

**Each question returns *which squares* fail it, not whether any do.** A
carve-then-repair loop opens a wall to remove a dead end and thereby changes
connectivity. A generator told only "not sound" has no way to tell whether its
last repair helped; a generator told *which* squares can fix exactly those.

**The three are computed independently, with no question borrowing another's
answer.** A maze with no corridors at all is *fully connected* — vacuously,
but truthfully — and whether it is a good maze is MAZE-5's business, not
MAZE-6's. Bundling them would have made the oracle useless for the loop it
exists to serve.

`describe()` renders a failing report as a sentence per failing requirement,
naming the codes and the squares and truncating a long list. Somebody reads
that string when a generator gives up after too many attempts.

---

## The tests, and how they are written

**93 new: 57 in `tests/test_maze.py`, 36 in `tests/test_structure.py`.**

Every structural property here is a property of a *shape*, so a test about one
is only as good as a reader's ability to see the shape it is talking about.
`tests/conftest.py` adds a `draw` fixture that places a picture inside the
19 × 29 frame:

```python
maze = draw("""
    .....
    .###.
    .....
""", at=(4, 4))
```

`.` carves, `#` leaves wall, a space leaves the square alone — which is what
lets a picture be a shape rather than a rectangle. Because the frame is
all-wall, a test gets a legal MAZE-3 border for free and breaches it only when
that is the point.

It is a fixture in `conftest.py` rather than a module the tests import, so
that nothing is added to `sys.path`, `tests/` stays a plain directory of test
files, and **nothing about WI-0's arrangement changes under the two developers
currently writing tests against it.**

**Each of the checker's three questions is exercised three ways:** it accepts
what it should, it rejects what it should and names the squares, and — the
part the plan is really asking for — **a maze that fails one question passes
the other two.** Three fixtures carry that: a ring drawn over the corner
(breaches the border, no dead ends, connected), a ring with one square hanging
off the middle of an edge (a dead end, border intact, connected), and two
rings that never meet (disconnected, border intact, no dead ends).

### One thing worth recording

My first "ring with a stub" picture hung the stub off a *corner*, where it
touched the ring at two points and therefore had two ways on — no dead end at
all. Four tests failed on it. **The picture was wrong, not the checker**, and
the fix was to the fixture. I kept the mistaken shape as a test of its own
(`test_a_square_touching_a_ring_at_two_points_is_not_a_dead_end`) so that
nobody later "fixes" the checker towards it: MAZE-5 counts ways on and does
not ask where they go.

---

## What WI-2 gets from this

* `Maze.all_walls()` to start from, and `with_corridors_at` / `with_walls_at`
  to carve and to fill back in; both return a new maze.
* `check(maze).is_sound` for "am I finished", and `border_breaches`,
  `dead_ends`, `unreachable_corridors` for "what do I fix".
* `ways_on_from` for anything that needs the direction as well as the square.
* Reading-order determinism everywhere, so a seeded generator is reproducible.

WI-2 is also mine, so if any of that turns out to be the wrong shape I will
say so in WI-2's summary rather than quietly changing it here.

---

## Deviations needing a ruling

1. **`Direction`, and `Direction.opposite()`, are in this work item.** The
   plan gives WI-1 "neighbour queries" and does not mention a direction
   vocabulary; `opposite()` in particular is there for GHOST-3, which is
   WI-9's. I added it because `ways_on_from` needs directions to be nameable
   and a second developer inventing a parallel `Direction` in the ghost policy
   would be worse. **Additive, and it lands in WI-9's ground**, so it wants a
   ruling.
2. **`tests/conftest.py` is new.** It is test scaffolding shared by both new
   test files and it will be shared by WI-2's. Nothing existing changes.
3. **`ways_on_from` beyond "neighbour queries".** `corridor_neighbours` alone
   would satisfy the letter of the brief; the direction-keeping form is what
   WI-9 will actually want.

## Contradictions found

**None in the plan or the architecture on this item.** MAZE-1 through MAZE-6
are consistent with each other and with the plan's section 5, and C-3 (the
observation that GHOST-3's reverse clause is unreachable in a generated maze)
is already recorded and is WI-9's to handle — nothing here contradicts it.

One thing that is *not* a contradiction but is worth stating: my brief named
`c3c6c55` as `main`, and `main` had already moved to `c76bc37` when I fetched,
because S-1's PR #75 landed in between. I branched from the tip, which is what
"from `main`" means.

## What needs a human

Nothing. The three deviations above want a ruling from the technical lead, not
from the user.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
