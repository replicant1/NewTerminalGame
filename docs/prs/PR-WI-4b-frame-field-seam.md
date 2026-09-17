# WI-4b — the composer produces the surface's field

**Branch:** `r7/wi-4b-frame-field-seam`, cut from the tip of `main` at `b3437ca`. Not
stacked.

| File | |
|---|---|
| `terminal_game/presentation/frame.py` | *(rewritten)* builds a `field.Field`; `frame.Cell` and `frame.Colour` are gone. |
| `tests/test_frame.py` | *(migrated)* 21 tests, up from 18. |
| `docs/progress/r7-wi-4b-frame-field-seam.md` | |
| `docs/progress/r7-wi-9-ghost-policy.md` | *(modified)* WI-9's log tail, carried forward. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**439 passed, 0 failed, 0 skipped**, nothing deselected. 436 before.

---

## Why this item exists

WI-4 and WI-5 landed within minutes of each other and **each invented the Presentation
seam, differently.** Both were on `main`, both green, and nothing joined them:

| | WI-5 (lane C) | WI-4 (mine, before this) |
|---|---|---|
| cell | `field.Cell(glyph, colour, background)`, `#rrggbb` | `frame.Cell(glyph, colour)`, a `Colour` enum |
| field | `field.Field` — mutable, 40 × 30 baked in | `Tuple[Tuple[Cell, ...], ...]` |
| colours | `palette`, six hex constants | `frame.Colour`, six enum members |

`surface.present` takes a `Field`. `compose_frame` returned neither.

## Why WI-4 is the half that moved

Three reasons, **all from lane C's code rather than from anyone's preference**:

1. `field.py`'s own docstring already declared the contract — *"WI-4 composes rows 0-28 and
   WI-12 supplies row 29; both produce one of these"* — and `Field.write`'s says it is
   *"the convenience WI-12 wants for the status line and WI-4 wants for a run of wall
   glyphs"*. **Lane C wrote the seam I should have been producing.** I did not see it
   because WI-5 had not landed when I wrote WI-4.
2. **`Field` enforces SCRN-2 in the data.** One character and two colours, with no other
   shape a cell can take. A tuple of tuples cannot do that, and ground rule 1.4 is why it
   matters.
3. `surface.present` already consumes it. The tuple had **no consumer at all.**

Settled with lane C directly on [PR #83](https://github.com/replicant1/NewTerminalGame/pull/83#issuecomment-5707265768),
not through a lead — including telling them **not** to adapt `Field` to me, so we would not
both fix it. No objection had arrived when I started; I said I would read silence as *carry
on*, and did. If they disagree it is one module and reversible.

## What survived, which is the point of a type migration

**Both of WI-4's measured tests are unchanged in intent:**

- the **specimen reproduction** — all 29 rows, character for character, against the
  normative picture;
- the **264-square actor check** — the player stood on every corridor square of the
  specimen, requiring the set of wall-coloured cells to come out identical each time.

They are what prove the composer still draws the right picture after its data type changed,
and a type migration is exactly what quietly breaks them. Verified by hand as well as by
the suite: the composed specimen row 13 reads

```
║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪▐█▌▪ ▪ ▪ ▪ ▪ ║ ▪ ║
```

with row 29 carrying the supplied status cells.

## One guard that is new

**The composer's output is asserted to be an instance of the `Field` class the *surface
itself* imported**, not the one the test imported, and `surface.Field is Field`. If either
module is ever pointed at a different `Field`, the two halves of Presentation drift apart
silently again and every other test here still passes — which is precisely how WI-4 and
WI-5 came to have two of everything. It builds no surface and opens no window; the join
proper is WI-7's to assert.

## Decisions taken (section 1.8 — reported, not asking)

**`compose_maze_rows` returns a full 40 × 30 `Field` with row 29 left blank**, rather than
29 rows. A `Field` is always 40 × 30 — there is no other shape — so a partial one was never
an option, and *"leaves row 29 alone"* is now a testable consequence rather than a slice
boundary.

**Backgrounds are left at `field.Cell`'s default of `palette.GROUND`** throughout. WIN-2's
black ground comes from that.

## Two questions for lane C, neither blocking

1. **The status row is still `Sequence[Cell]` of exactly 40.** That keeps WI-4's contract
   with WI-12 unchanged apart from the cell type. But `Field.write`'s docstring says it is
   *"the convenience WI-12 wants for the status line"*, which suggests **WI-12 may prefer
   to hand me text and a colour** and let me write it. That is WI-12's call, it is a
   four-line change, and I would rather make it on request than guess.
2. **Was `background` meant for something I have not thought of?** Nothing WI-4 draws sets
   one.

## Note for the plan

Section 7 lists WI-4 and WI-5 as *"safe to run in parallel — domain, presentation-as-data
and shell"*. **They were not:** both are Presentation and both had to invent the same seam.
**WI-12 ↔ WI-4 is the same shape** and has not started yet, which makes it cheap to get
right. Already reported; repeated here because this PR is the evidence.

## Window hygiene

Pure data. No toolkit is imported by `frame.py`, no window is opened, no `ctypes`, no
`root.update()`. The layer-rule checker passes. No code was broken to watch a test go red.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
