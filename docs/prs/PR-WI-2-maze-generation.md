# WI-2 — maze generation

**Branch:** `r7/wi-2-maze-generation`, cut from `main` at `ddc250e`
**Lane:** B · **Iteration:** M1 · **Depends on:** WI-1
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**217 passed, 0 failed, 0 skipped** (174 inherited, 43 new)

The plan calls this the biggest algorithmic risk in the project, on the
architect's caution C4: MAZE-4, MAZE-5 and MAZE-6 are three constraints
fighting over one grid, and the obvious generators produce dead ends in
quantity.

**It converged in a single pass with no retry loop.** The rest of this says
why, because the reason is more useful than the result.

---

## Two of the four requirements are made impossible, not repaired

Carving happens on a lattice of **cells at odd coordinates**: cell `(i, j)` is
the grid square `(2i + 1, 2j + 1)`, and two adjacent cells are joined by
opening the single square between them. That gives **9 cells across and 14
deep**, and MAZE-1's grid is exactly the size such a lattice needs:

    19 = 2 × 9 + 1        29 = 2 × 14 + 1

From that one choice:

**MAZE-2 — corridors one square wide.** Every 2 × 2 block of grid squares
contains one whose column *and* row are both even. Cells are odd-odd;
connectors have exactly one even coordinate; so a both-even square is never
carved. A corridor two squares wide is not unlikely — it is unrepresentable.

**MAZE-3 — the border ring is solid.** Cells occupy columns 1–17 and rows
1–27. A connector lies strictly between two cells, so columns 2–16 and rows
2–26. Nothing carveable reaches column 0 or 18, or row 0 or 28.

**Both are asserted exhaustively over the whole lattice, not sampled over
generated mazes**, so they hold for every maze the generator could ever
produce rather than for the two hundred it produced here.

### This is measured, not guessed

Decoding all 29 rows of the specimen picture in the requirements, on ruling
C-2's mapping of maze column `c` to screen column `2c`, gives **zero corridor
squares with both coordinates even** — across all 551 squares. The original
maze was built this way. `docs/findings/WI-2-odd-cell-lattice.md` records the
measurement with a snippet that reproduces it, and I ran that snippet as
written to check it does.

---

## The other two requirements, in sequence

**MAZE-6** comes from a randomised depth-first carve, which spans every cell
by construction, so connectivity holds of the result and of anything made from
it by adding more edges.

**MAZE-5** comes from a repair pass. A spanning tree is nothing *but* dead
ends; the repair gives every cell a second way on by opening one more wall.

**Why it converges in one pass, and cannot thrash:**

* Adding an edge only ever *raises* two degrees, so the repair **never creates
  the fault it is removing**.
* Adding an edge never disconnects anything, so it **cannot undo MAZE-6** to
  satisfy MAZE-5.
* Every cell has at least two lattice neighbours — two at the corners, four
  inside — so a cell short of ways on **always has a spare one to use**.

That is the part of caution C4 that turned out not to bite. The three
constraints do not fight on this lattice, so there is nothing for a retry loop
to settle.

**Measured over 500 seeds: 0 unsound, 0 with a 2 × 2 corridor block, 500
distinct mazes, 3.16 ms each** including the full structural check.

---

## MAZE-4, and how randomness arrives

`RandomSource` is a `Protocol` with **one method, `randrange`**. The domain
may not name a module-level random source, so nothing here imports `random`;
`random.Random` satisfies the protocol and so does a test double.

Shuffling is done from `randrange` by Fisher-Yates rather than taken from the
source, so a maze depends only on the sequence of integers it was given and
not on the shuffling algorithm of whatever supplied them.

The test double `Numbers` has `randrange` and **nothing else** — no `shuffle`,
no `choice`, no `seed`. A generator that reached for any of those would fail
with an `AttributeError`, which is how "one method is the whole surface" gets
tested rather than merely claimed in a docstring.

---

## The gate before a maze is handed out

The plan asks for connectivity to be verified before a maze is handed out.
`verified()` asks **WI-1's checker** — the same oracle the tests use, so the
generator cannot be sound by its own definition and broken by everyone
else's — and raises `GenerationFailed` naming the requirement if it is not.

Both branches are genuinely exercised: a sound maze passes through, and a
hand-built unsound one raises with `MAZE-3` or `MAZE-5` in the message. The
unsound mazes are fixtures drawn for the purpose; **no working code was
altered to make anything fail.**

---

## The tests — 43 new

**The sweep** builds 200 mazes once in a module-scoped fixture and then asks
one question per test, so a failure names the requirement it broke rather than
a compound verdict: MAZE-3 via `border_breaches`, MAZE-5 via `dead_ends`,
MAZE-6 via `unreachable_corridors`, MAZE-2 via a 2 × 2 scan, plus the oracle's
own `is_sound` and MAZE-4's all-distinct.

**The parity proofs** are exhaustive rather than sampled, as above.

**The parts** are tested separately: the lattice geometry, that being a
neighbour is mutual, that the carve reaches every cell and produces a tree of
exactly 125 edges, that the carve *is* all dead ends before the repair (so the
repair is visibly doing something), that the repair only ever adds edges, and
that running the repair twice changes nothing the second time.

One test asks the repair a question the generator never asks it — a cell with
**no** edges at all, needing a shortfall of two rather than one. The carve
cannot produce that, but a repair that assumed every cell already had one way
on would quietly leave it a dead end.

### Suite time

The suite goes from **0.13 s to 1.91 s**, and 1.8 s of that is the 200-seed
sweep. I judged that worth paying for the project's stated biggest risk, and
`SEEDS` is a named constant at the top of the file if anyone disagrees.

---

## An error I caught in my own finding, worth passing to WI-8

I first wrote that the grid's exact centre `(9, 14)` has both coordinates odd
and is therefore always corridor. **Row 14 is even.** `(9, 14)` is a
*connector*, and is carved only when that particular wall is opened — measured
over 200 seeds, it is corridor in **109** of them.

That matters to **START-1**, "the player begins on the corridor square nearest
the middle". A search that assumed the centre was walkable would pass its own
test on roughly every other seed. The nearest always-corridor squares are the
cells above and below it, `(9, 13)` and `(9, 15)`, both corridor in 200 of
200. **START-1 must search rather than compute, and its test must run over
many seeds.** It is in the finding under "what later items should take from
it".

---

## Deviations needing a ruling

1. **No retry loop**, where the plan said "expect carve-then-repair: generate,
   eliminate each dead end, verify connectivity". I do all three steps, but
   the verify never fails and there is nothing to retry. The plan described a
   shape it expected rather than mandating one, so this may need no ruling —
   but it is a visible departure from the words and I would rather name it.
2. **The 2 × 2 single-width check lives in the test file, not in WI-1's
   checker.** WI-1's checker has exactly three questions by design and adding
   a fourth would change a merged contract. Only WI-2's tests need it today.
   If WI-18's audit wants it later, it should move rather than be duplicated.
3. **`GenerationFailed` is a new exception type in the domain.** Small, but it
   is vocabulary other layers may end up catching.

## Contradictions found

**None.** MAZE-2 through MAZE-6 are mutually satisfiable and the specimen
picture agrees with all of them. Caution C4 overestimated the difficulty, but
an overestimated risk that was called out early and turned out cheap is the
system working, not a contradiction — and it was right to flag it, because the
naive generator it warned about really would have failed.

## What needs a human

Nothing from this item. The three deviations want the technical lead.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
