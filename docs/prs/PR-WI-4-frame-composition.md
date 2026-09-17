# WI-4 — frame composition

**Branch:** `r7/wi-4-frame-composition`, cut from the tip of `main` at `ddc250e`.
**Base:** `main`. Not stacked on anything.

| File | What it is |
|---|---|
| `terminal_game/presentation/frame.py` | `compose_maze_rows` and `compose_frame`, the `Colour` vocabulary, the `Cell` type, and the actor and dot glyphs. |
| `tests/test_frame.py` | 18 tests. |
| `tests/conftest.py` | *(modified)* the specimen picture taken apart into a maze, a dot field and two actors. |
| `docs/progress/r7-wi-4-frame-composition.md` | The progress log, carrying WI-3's tail forward. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**192 passed, 0 failed, 0 skipped**, nothing deselected. 174 were already there; WI-4 adds
18.

---

## The test that matters

**The composer reproduces the specimen picture exactly.** The picture in
`docs/FUNCTIONAL_REQUIREMENTS.md` is taken apart into a maze (264 corridors, 287 walls),
262 dots, the player at `(10, 13)` and the ghost at `(1, 27)`; this module is asked to draw
them; and all **29 rows match character for character across the full 40 columns**.

That is the one test that can catch a frame composed *correctly but differently* from what
the specification shows — a column mapping one out, a missing connector, an actor two cells
wide instead of three, the ghost drawn before the player. Nothing else in the suite would.
Its docstring says so, so that nobody prunes it as "covered elsewhere".

It is guarded: a companion test asserts the parse really yielded 29 rows, 264 corridors,
287 walls, 262 dots and both actors, because a parse that quietly produced an empty maze
would make the reproduction pass by drawing nothing and comparing it with nothing.

## The three facts the plan handed me, re-measured rather than trusted

You told me to keep checking these rather than taking them, so I did.

1. **Ruling C-2, `2c` column mapping.** Confirmed: all 29 specimen maze rows are exactly 37
   columns, and a lone wall square marooned in a carved band lands at column `2x`.
2. **Three-cell actors.** Confirmed: player at 19/20/21, ghost at 1/2/3 in the picture.
3. **A connector flanking a corridor square is always blank, so a three-cell actor never
   overwrites a wall glyph.** Confirmed the hard way — by **standing the player on every
   one of the specimen's 264 corridor squares in turn** and requiring the set of
   wall-coloured cells to come out identical each time. This is the fact the whole
   three-cell design rests on, and it is now a property test rather than a sentence.

## SCRN-3's colour, by the ruling

The technical lead ruled `SCRN-3 | WI-3 (glyph) + WI-4 (colour)`, and its specific point —
**a lone block is the same blue as a line** — has its own test, because that is the easy
one to get wrong. Wall colour is also checked over the *whole* picture rather than one
square, since walls are drawn by two separate pieces of code (the squares, and the
connectors between them) and an uncoloured connector would pass a single-cell test.

## Design decisions (section 1.8 — reported, not asking for a ruling)

**Colour is a vocabulary of the specification's own words, not pixels.** `Colour.GOLD`, not
`#b8860b`. Presentation produces data; **WI-5 is the only part of the program that should
know what "gold" is in hexadecimal.** `Colour.CYAN` is in the enum although WI-4 never
emits it, because section 7 makes WI-4 the item that *defines* the seam WI-12 fills.

**`Maze.is_wall` raises off the grid** — deliberately, so an out-of-bounds bug cannot pass
for a dead end — so WI-4 supplies the outside-is-not-a-wall guard that WI-3 measured from
the border corners. It is one function with the evidence in its docstring.

**An actor's flanking cell outside the field is skipped, not wrapped.** MAZE-3's border
means an actor can never stand on column 0 or 18 so this cannot arise in a real game, but a
negative index in Python quietly addresses the far end of the row, and a silent wrap is a
worse bug than a missing half-block.

**`Direction` is not used.** Lane B reported the WI-3 seam as having nothing to negotiate
and that is right: WI-3 takes four bare booleans, and WI-4 reads neighbours as `(x±1, y±1)`
with its own bounds guard.

## Deviation needing a ruling (additive)

**`tests/conftest.py` gains the specimen parse** — `read_specimen()` and a `specimen`
fixture — which nothing asked me to put there. WI-4 needs the maze, the dot field and the
actors rather than just the rows, and WI-12 and WI-16 will want the status row, so it is
shared scaffolding rather than WI-4's. I kept lane B's stated preference for a conftest
fixture over an importable module. It is an append, so it should merge cleanly, and it is
mine to resolve if it does not.

## Known duplication, raised rather than silently resolved

`tests/test_wall_glyphs.py` (WI-3, mine) still has its own smaller specimen parser. **I did
not de-duplicate it.** Churning a landed green file mid-run to save twenty lines is not
worth the merge risk, and two parsers independently agreeing on the same picture is a weak
cross-check rather than a cost. Worth tidying when someone is next in that file; naming it
here so it reads as a decision and not an oversight.

## Notes for the items downstream

- **WI-5:** `Colour` is a six-member enum of names. The full glyph alphabet the surface must
  render is `wall_glyphs.ALL_WALL_GLYPHS` plus `DOT_GLYPH`, `CONNECTOR_GLYPH`,
  `PLAYER_GLYPHS`, `GHOST_GLYPHS` and the space — all of which S-1 measured at a uniform
  cell width in Menlo.
- **WI-12:** `compose_frame` wants exactly 40 `Cell`s for row 29 and refuses anything else.
  `Colour.CYAN` is waiting for you.
- **WI-7 (mine, next):** `compose_frame` is the whole picture; hand it to the surface
  unaltered.

## Window hygiene

WI-4 opens nothing, imports no toolkit and touches no desktop — it is pure data over a maze
and four integers. The `needs_window` exclusion is untouched. No `ctypes`, no Objective-C,
no `root.update()`; none of them comes near this item. No code was broken to watch a test
go red.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
