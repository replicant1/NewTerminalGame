# M2 — DEV-B's lane, complete

**Developer:** DEV-B · **Iteration:** M2, *the rules and the picture* ·
**Mode:** non-local, real pull requests, merged by me

DEV-B's M2 lane is WI-12 alone (3 days). It is built, merged and green on
`main`. Nothing in this iteration opened a window.

---

## What landed

| Item | Branch | PR | State |
| --- | --- | --- | --- |
| **WI-12** — the frame composer | `r6/wi-12-frame-composer` | [#45](https://github.com/replicant1/NewTerminalGame/pull/45) | **merged** |

Opened `--base r6/wi-8-wall-glyphs` and **retargeted to `main`** once WI-8
merged a minute later.

| File | |
| --- | --- |
| `terminal_game/presentation/frame_composer.py` | `compose_frame`, `column_of_square`, `DOT_GLYPH`, `PLAYER_MOTIF`, `GHOST_MOTIF` |
| `tests/test_frame_composer.py` | 44 tests |

---

## Suite, as left

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 489 tests in 4.3s

OK
```

**489 passed, 0 failed, 0 skipped**, on `main` with WI-8, WI-12 and WI-13 all
landed.

---

## The announce rule paid for itself, visibly

Worth recording as evidence, because amendment 1 added the rule on
suspicion and this is the first time it has been tested.

WI-12 was briefed as depending on WI-8, and when I started **no `r6/wi-8-*`
branch existed on the remote**. I recorded `BLOCKED` and, rather than idle,
began building with the walls injected through a `WallGlyphs` protocol I had
invented — two methods, one for a wall cell and one for a connector.

DEV-C then pushed, and WI-8's own docstring said:

> **Announced for WI-12** (first-lander rule 4). The frame composer owns
> rows 0-28 and lays the dots and the actors over this; it does not need to
> know a single wall character to do so.

**I deleted my protocol and took theirs**, and theirs is better: the
composer never asks a per-square question at all. Without that sentence I
would have landed a second shape and one of us would have been conforming
afterwards. The rule cost DEV-C one sentence and saved a conforming branch.

**The conductor's own error is worth keeping with it**: I was told to stack
on a branch belonging to an agent spawned minutes earlier. A stacked branch
needs its parent *pushed*, not merely *assigned*. The conductor has logged
that as its own.

---

## Two things checked rather than argued about

**The plan's section-5 safety claim is now a test.** Section 5 says the
three-column actor motifs overwrite the connector on each side and that this
is safe, *because* a connector next to a corridor square is always blank —
the horizontal glyph appears only between two joined wall squares, and an
actor only ever stands on corridor. If that were ever wrong the picture
would silently lose a wall. It is now checked over **12 real generated
mazes**: no non-blank cell of WI-8's wall layer is ever covered by an actor.

**A dot count came out one short, and was right.** A test asserting every
dot in the field is drawn failed at 262 against 261. The missing one was
**the dot under the ghost** — SCORE-4 keeps it in the field, END-4 paints
the ghost over it. The test now states that rule rather than counting
blindly, and asserts the seed really does start the ghost on a dot so it
cannot pass for the wrong reason.

---

## How the tests are split, and why

**Every test but one class stands WI-8's walls in with a deliberately fake
vocabulary** — `W` for a wall square, `-` for a joining connector. Which
glyph a wall is drawn as belongs to WI-8's tests. WI-12's own tests own
*where* things go.

One class owns the seam to WI-8 and reads its expected picture *from*
`wall_layer` rather than retyping it. One test owns the seam to WI-13: that
whatever `status_row(score, outcome)` produces is what ends up on row 29,
unchanged, for all three endings — *what it says* stays WI-13's.

And two guards in the other direction: no wall glyph appears anywhere in the
composer's executable source, and no status-line literal appears anywhere in
the file at all.

---

## Seen, not only asserted

A real generated game (seed 4), composed and read. 30 rows, every one
exactly 40 characters, a 3-column margin on every maze row, the double lines
joining up, lone blocks where the generator left isolated walls:

```
 0|╔═══════╦═══════════════════════════╗   |
 1|║▗█▖▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║   |
14|║ ▪ ■ ▪ ╚═══════╣▐█▌║ ▪ ════════╣ ▪ ║   |
28|╚═══════════════════════════════════╝   |
```

It looks like the specimen. No window was involved: this is all value.

---

## Deviations needing a ruling

**A maze must *fit* the picture rather than be exactly 19 × 29.** The plan's
test list asks for "a small hand-built maze composes to a known picture",
which a strict size check would make impossible. `compose_frame` therefore
refuses a maze too wide or too deep and accepts anything smaller, composing
it into the top-left. The real game always hands over 19 × 29 and there is a
test that it fills the 37 columns and 29 rows exactly. A looser contract
than the plan's wording implies, so it is flagged.

---

## Still open, carried forward

- **The ownership-table contradiction from M1** — amendment 1's table gives
  directions to DEV-B, its own first-lander rule gives them to WI-5. The
  tree follows the rule; the table row is what is wrong.
- **`heading=None`** in WI-7's `next_step`, additive to the plan.
- **The modifier-state question on `KeyPress`** (WI-9), with DEV-C,
  unanswered. My recommendation was not to change it.
- **`tk_grid.create_surface` and `measure_metrics` have no automated test**
  (M0), because exercising them needs a live toolkit interpreter.
- **For a human:** is Menlo 16pt in a 400 × 570 window comfortable (**A4**);
  do the double-line glyphs join up cleanly at that size; does it flicker on
  a mapped window. All three are WI-16's, DEV-B's in M3.

---

## Next for DEV-B

M3: **WI-16, the look seen** — 2 days, depends on WI-2, WI-4 and WI-12, all
landed. It is the item that puts the real colours and the real glyphs in
front of a person, and it is where the three open human questions above get
answered.
