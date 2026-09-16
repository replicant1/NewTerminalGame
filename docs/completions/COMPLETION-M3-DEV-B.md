# M3 — DEV-B's lane, complete

**Developer:** DEV-B · **Iteration:** M3, *a whole game with no window* ·
**Mode:** non-local, real pull requests, merged by me

DEV-B's M3 lane is WI-16 (2 days), plus one conforming branch that came out
of amendment 2 and was unblocking another lane. Both merged and green.

---

## What landed

| Item | Branch | PR | State |
| --- | --- | --- | --- |
| **WI-1a** — the specimen fixture leaves `tests/` | `r6/wi-1a-specimen-home` | [#50](https://github.com/replicant1/NewTerminalGame/pull/50) | **merged** |
| **WI-16** — the look, seen | `r6/wi-16-the-look-seen` | [#53](https://github.com/replicant1/NewTerminalGame/pull/53) | **merged** |

---

## Suite, as left

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 605 tests in 4.8s

OK
```

**605 passed, 0 failed, 0 skipped**, on `main` with WI-10's architecture
guard landed. WI-16 passes all six of its rules.

---

## The screen, and the ledger

WI-16 was the first thing in DEV-B's lane to put a window on the user's
screen, and it ran under amendment 4's screen gate.

| | |
| --- | --- |
| Windows opened / reaped | **8 / 8** |
| Modal sheets raised | **none** |
| Errors | **none** |
| Titlebar read back | `Terminal Game`, all 8 |
| Kinds of thing on the canvas | **`["text"]`, all 8** |

**Project ledger: 16 opened, 16 reaped.**

Runs were escalated deliberately so the user's screen was borrowed as little
as possible: one window for two seconds first, to confirm the mechanics and
the reap, before asking for anything longer. The gate was requested before
any window was opened, and released the moment the last one was confirmed
gone, because DEV-A was waiting behind it.

**`canvas_item_kinds` being `["text"]` on all eight is SCRN-2 observed on a
real screen rather than argued.** Under candidate 2 "there are no images" is
a rule rather than a property of the medium (caution C5); now it has been
watched.

---

## The thing I did not do

**I did not answer SCRN-3, and I did not convert my own measurement into an
answer.**

In WI-2 I measured that all 113 glyphs the picture uses share one advance in
Menlo at four point sizes, with a control showing glyphs Menlo lacks fall
back to visibly different advances. That settles the **spacing** — the glyphs
land in the right places. Whether the **strokes meet** at the cell boundary
is a property of the outlines and only an eye can read it. I said so when I
took the measurement, DEV-C reached the same conclusion independently in
WI-8's glyph census, and this item keeps to it.

What WI-16 does instead is make the looking cheap. **The `joinery` view puts
every wall junction on one screen at once** — corners, tees, straights and
the crossing `╬` — so the question is answerable in the few seconds the
window is up rather than by hunting round a maze. It is derived from WI-8's
`wall_layer`, declares no glyph of its own, and there is a test that it
declares none. It is also the only thing on this project that has ever put a
crossing on a screen: the specimen picture does not contain one.

---

## What needs a human — three questions, one command, ~25 seconds

All three are recorded as **unanswered** in
`docs/findings/WI-16-the-look.md`, with the exact command for each.

```
/usr/bin/python3 tools/the_look.py --seconds 8
```

Three self-closing windows. The tool prints the three questions before it
opens anything.

1. **SCRN-3** — in the `joinery` window, is there a hairline gap where two
   cells meet, or do the double lines read as solid continuous rules?
2. **A4** — is Menlo 16pt, in a 400 × 570 window, comfortable to read? To
   settle it by comparison rather than guess:
   `--view game --sizes 14,16,18,20 --seconds 5`. If the answer is not 16,
   the change is **one constant** and the window size follows from it.
3. **A1** — does the titlebar read exactly *Terminal Game*? Tk reported that
   string back on all eight runs, which is worth something but is **not** a
   person seeing a titlebar.

Measured sizes, so the cost of each answer is known in advance:

| Point size | Cell | Window |
| --- | --- | --- |
| 14 | 8 × 16 | 320 × 480 |
| **16 (current)** | **10 × 19** | **400 × 570** |
| 18 | 11 × 21 | 440 × 630 |
| 20 | 12 × 24 | 480 × 720 |

---

## The specimen move, and a violation of my own

Amendment 2 ruled the specimen fixture must leave `tests/` and made the
destination DEV-B's call. DEV-C asked for it on PR #45 because **WI-10's
rule 6 could not go green while `tools/walking_skeleton.py` imported test
code**. I stopped WI-16, decided, and landed it.

**`terminal_game/presentation/specimen.py`**, because the dependency then
runs the right way for both tests and tools, because it is a picture and
that is the layer whose job is to reproduce it, and because it adds no new
top-level package for WI-10's rule 4 to need an exception for.

I moved it and fixed all five importers including DEV-C's own tool, rather
than leaving one line to them, because a rename that leaves `main` broken
between two landings is worse than touching one import in another lane's
file. DEV-C had offered either way.

**And I found a violation of mine on the way past.** `tests/test_frame.py`
contained the real STAT-2 literal. I wrote it in WI-1, before WI-13 existed,
and A7 confines every status-line literal to WI-13 — so my own file was in
breach of a rule I had since been enforcing on other people's work. Fixed.

---

## Still open, carried forward

- **The ownership-table contradiction** (M1) — amendment 1's table gives
  directions to DEV-B, its own first-lander rule gives them to WI-5. The
  tree follows the rule; the table row is what is wrong.
- **`heading=None`** in WI-7's `next_step`, additive to the plan.
- **The modifier-state question on `KeyPress`** (WI-9), with DEV-C,
  unanswered. My recommendation was not to change it.
- **A maze must *fit* the picture** rather than be exactly 19 × 29 (WI-12) —
  a looser contract than the plan's wording implies.
- **`tk_grid.create_surface` and `measure_metrics` have no automated test**
  (M0), because exercising them needs a live toolkit interpreter. They are
  now exercised for real by `tools/the_look.py` as well as WI-4.

---

## Next for DEV-B

M4: **WI-19, the scripted game** — a whole game played headless in the
suite, win path and loss path, frames asserted as text. Two rulings from
amendments 3 and 5 already apply to it and both came from DEV-A: there is
**no clock seam to consume or build** — drive `session.tick()`,
`session.move()` and `session.quit()` directly — and **A7 forbids authoring
a status-line string, not having one in a frame**, so the expected row 29 is
composed with WI-13's own function and joined onto the 29 maze rows.
