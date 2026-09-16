# WI-6 — Where the player and the ghost actually start

**Measured by:** DEV-A, WI-6, run 6
**Why it is here:** START-1 and START-2 each name *the* square, singular. On a
real 19 × 29 maze neither square is unique, and how the tie is broken decides
something a player can see. This records what the tie-break chosen actually
produces, so that whoever rules on it is ruling on a number rather than on a
guess.

---

## What was run

`/usr/bin/python3`, over the 200 seeded mazes the Domain sweep already uses.
For each: `opening_position(maze)`, then the player's square, the ghost's
square, the size of each tie, and the dot count. The measurement was taken
**twice** — once from a standalone script before `opening_position` was
written, and once from the finished function — and the two agree exactly.

## What came back

| Measured over 200 mazes | Result |
| --- | --- |
| Player start square | `(9, 14)` in **115** mazes, `(9, 13)` in **85** |
| Size of the player's tie | unique in 115, **two-way** in 85 |
| Ghost start square | `(1, 1)` in **115** mazes, `(1, 27)` in **85** |
| Size of the ghost's tie | **four-way** in 115, **two-way** in 85 |
| Dots at the start | **259 to 271**, mean **264.5** |
| Player and ghost ever on the same square | **never**, in any of the 200 |

## Why it comes out like that

**The middle of the grid is a connector, not a cell.** The centre of a
19 × 29 grid is the point (9, 14). Column 9 is odd, but **row 14 is even**,
so (9, 14) is one of the connector squares between the cell at row 13 and the
cell at row 15 — and it is corridor only when those two cells happen to be
joined. Measured: they are joined in 115 of 200 mazes.

- When (9, 14) is corridor, it is the unique nearest square and the player
  stands exactly in the middle.
- When it is wall, the two nearest corridor squares are (9, 13) and (9, 15),
  both exactly one square away, and the tie is broken in favour of (9, 13).

**The furthest square from the middle is always a corner**, and all four
corners of a 19 × 29 grid are cell squares, so all four are always corridor:

- from (9, 14), all four corners are at a squared distance of 8² + 13² = 233
  — a **four-way** tie, broken to (1, 1);
- from (9, 13), the two bottom corners are at 8² + 14² = 260 and the two top
  ones at 8² + 12² = 208 — a **two-way** tie, broken to (1, 27).

## The consequence, stated plainly

**The ghost always starts in the left-hand column of the maze**, at the top-
left or the bottom-left corner, and never on the right. The player always
starts within one square of the exact middle. Over 200 mazes there were only
**two distinct opening positions**, even though there were 200 distinct
mazes.

Nothing in the requirements is broken by this. START-2 asks only that the
ghost be the furthest corridor square from the player, and it always is;
*"so the two always start well apart"* holds in every case. But a player
would notice, over a few games, that the ghost is always on the left.

## The alternative, and why it was not taken

Breaking the tie with a draw from a random source would spread the ghost over
all four corners. It was not done because **WI-6's work-item description does
not hand this item a random source**, where WI-5's and WI-7's both say so
explicitly — and inventing one would be inventing a requirement.

If it is wanted, the change is confined to `ghost_start_square` in
`terminal_game/domain/opening_position.py`: one extra parameter and one
`random_source.choice(...)` over the tied squares. Its callers are
`opening_position` and, later, WI-18's entry point, both of which have a
random source in hand already. The tests that would change are the two
hand-built cases in `tests/test_opening_position.py`; the 200-seed
property tests assert *"no corridor square is further"* and would pass either
way, which is as it should be.

## One number the later items need

**A full game is worth 259 to 271 points, mean 264.5** — one per corridor
square, less the player's own. So:

- **WI-13** (status line): the winning score is a three-digit number in
  practice. STAT-3's `CLEARED  score 274  q quits` is illustrative, and the
  real number will be near it but not equal to it.
- **WI-19** (scripted game): a win path has to eat about 265 dots, so it
  should drive the state directly rather than walk a route by hand.
