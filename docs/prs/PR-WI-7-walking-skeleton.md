# WI-7 — the walking skeleton

**Branch:** `r7/wi-7-walking-skeleton`, cut from the tip of `main` at `2599b1a`. Not
stacked.

| File | |
|---|---|
| `terminal_game/shell/skeleton.py` | the entry point, the fixtures, and the `q` policy. |
| `tests/test_skeleton.py` | 11 headless tests and 2 marked `needs_window`. |
| `docs/findings/WI-7-box-drawing-ink.md` | **human item 8, answered by measurement.** |
| `docs/progress/r7-wi-7-walking-skeleton.md` | |
| `docs/progress/r7-wi-11-session-controller.md` | *(modified)* WI-11's tail, carried forward. |

**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**716 passed, 0 failed, 0 skipped, 4 deselected**. 705 before.

**Crash reports: 14 before, 14 after. Zero new.**

---

## The window really opened, and it closed itself

The `needs_window` suite was run under a **90-second deadline in a parent process**, not a
pytest timeout — a pytest-internal timeout does not help when the hang is inside
`mainloop`.

```
.venv/bin/python -m pytest -q -m needs_window tests/test_skeleton.py
2 passed in 1.42s          (elapsed 1.54s, no timeout, exit 0)

crash reports   14 before  ->  14 after   (0 new)
visible apps     7 before  ->   7 after   (nothing left behind)
```

Asserted from inside an `after` callback while it was up: the window **was mapped**, it
carried **the composed frame on all 30 rows**, and it measured **400 × 570** — S-1's Menlo
16 cell, 10 × 19, times 40 × 30. Then it closed itself and `run()` returned.

Nothing was left on the user's desktop. `lsappinfo visibleProcessList` listed the same
seven applications before and after.

## The join is the one thing this item owns

Asserted **cell by cell over all 40 × 30**: the field the composer produced is the field on
the glass. A join that dropped a row or shifted a column would still produce something
plausible, so rows alone would not do.

**Nothing else is re-proved here.** That the picture is *right* is WI-4b's and is pinned
against the specimen there. That a canvas shows what it was given is WI-5's. That Tk
delivers a key event to a binding at all is **WI-6's**, and its own `needs_window` test
already pins it — including the trap that `event_generate` on a withdrawn toplevel is
accepted and silently delivers nothing, which I hit in a probe before reading their test.

So `quit_on_key(window)` is returned rather than merely bound, and WI-7 asserts what
happens *when a key arrives* — which is WI-7's decision — in the default suite, with
nothing on the screen.

**The join test has a control.** Comparing the painted window against a *blank* field shows
the comparison can disagree, on all 30 rows. Without it, a `shown_row` that echoed its
input would make the join test pass on anything.

## Human item 8 — answered, and not by looking

**I cannot see the screen.** WI-7 put a real window on the user's desktop, but an agent has
no eyes on it and it was up for under a second under a watchdog. *"It looked continuous to
me"* is not something I am in a position to say.

So I measured the thing the impression was a proxy for. **The font knows.** A TrueType
`glyf` record begins with the glyph's bounding box and `hmtx` gives the advance, so *does
the ink reach the edge of the cell* is arithmetic on a file the system already ships — pure
`struct` parsing, no install, no `ctypes`, no permission, nothing on screen. It is exactly
what S-1 and WI-5 could not do, because both asked **Tk**, and Tk will not talk about ink.

> **Menlo's box-drawing glyphs are designed to tile. They overlap at every joining edge
> rather than merely meeting.**

| | |
|---|---|
| horizontal overshoot, each side | **0.156 px** (ink −20 → 1253 against a 1233-unit advance) |
| vertical overshoot, above | **0.562 px** |
| vertical overshoot, below | **0.828 px** (ink −618 → 1992 against a cell of +1920 → −512) |

**The controls are what make that mean something.** An ordinary `M` stops well inside its
advance (36 → 1095) and the dot `▪` stops a long way inside it (219 → 1013) — so "reaches
the edge" is a property of the box-drawing set, not of every glyph. Sharper still: **each
corner reaches the edge on exactly the two sides where it has an arm** and stops at the
centre stub on the other two. A font that merely drew fat glyphs would not do that.

**What this does not settle**, and the finding says so plainly: the font's geometry is not
the renderer's output, and at 0.156 px the horizontal overlap is a fraction of a pixel.
**But it changes the question the user is asked** — from *"is this font unusable, should we
go and get a different toolkit?"*, which is a decision, to *"does it look right to you?"*,
which is an ordinary cosmetic check like human item 3. **WI-17 should put it that way
rather than as a risk.**

**Nobody has yet seen this game.** I observed that a window mapped, what it contained, its
size, and that it closed. Not what it looked like.

## Decisions taken (section 1.8 — reported, not asking)

**The fixture is the specification's own picture** — its maze, its actors, its dots, its
status line — rather than an invented maze. It costs nothing and buys two things: the
window can be held against the requirements document side by side, and it is dense with the
long wall runs human item 8 needed. A guard test asserts the fixture really *is* the
specimen, because if the two drifted the window would still look fine and the comparison
would quietly stop meaning anything. A second guard runs WI-1's structural checker over it.

**Key handling goes through WI-13's `intent_for`** rather than hard-coding `q`/`Q`, so
CTRL-4's mapping lives in one place. One binding on `<Key>`, so **CTRL-5 is a consequence of
the translation returning `None`** rather than of this module having listed the keys it
likes. A move intent is read and deliberately dropped — the skeleton has no rules.

**The watchdog is kept, and is not set in production.** WI-6 guarantees a way out *exists*;
it does not guarantee anybody takes it. A binding that silently failed to fire would leave
a window on a real desk waiting for a key that can never arrive. The watchdog turns that
from a hang into a closed window and a red test. In `main()` it is absent — a game that
closed itself on a timer would be a time limit, and GAME-3 forbids one.

**Identity guard**, per the section 7 rule: `skeleton.Field is frame.Field is surface.Field`.
The skeleton is the first thing to hold the composer and the painter at once, so it is the
first place they could be pointed at different types.

## Window hygiene

Never a second `tkinter.Tk()` — everything goes through `GameWindow`, which owns the one
interpreter. No competing `destroy`. No `update()` anywhere. The watchdog goes through
`GameWindow.after`, inside `mainloop`. Every headless test closes its window in a `finally`.
Crash reports counted before and after, because the command output is not a crash detector.
No `ctypes`, no AppleScript, no permission dialog, no Terminal window opened.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
