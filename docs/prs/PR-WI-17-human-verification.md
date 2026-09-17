# WI-17 — the human-verification pack

**Branch:** `r7/wi-17-human-verification`, cut from the tip of `main` at `da9ec9c`.

| File | |
|---|---|
| `docs/findings/WI-17-human-verification.md` | **the pack.** |
| `tests/test_verification.py` | 1 headless guard, 3 `needs_window`. |
| `docs/progress/r7-wi-17-human-verification.md` | |

**Suite:** `.venv/bin/python -m pytest -q` — **925 passed, 0 failed, 0 skipped, 8 deselected**.
**Crash reports 14 before, 14 after. Zero new. Nothing left on the desktop.**

---

## The pack opens with the sentence that frames the run

> **Nobody has yet seen this game.**

It has opened on this desktop several times and closed itself in about a second every
time, unwatched. Everything anyone knows about how it looks is inferred from data
structures and font outlines.

## One check moved from the human column to the agent column

Which is this item's whole purpose — every check moved out shrinks the pack, and the pack
is only honest if what remains is genuinely irreducible.

**Tk reports the four arrow keysyms as `Up`, `Down`, `Left`, `Right`** — exactly the names
WI-13's table is keyed on — on a real mapped window. WI-6 proved delivery for `q` only,
and a bind-time check proves nothing: a misspelled keysym binds happily and never fires,
so CTRL-1 could have passed every unit test and not worked.

Asserted **through `intent_for`**, as lane B suggested, so it pins the whole path rather
than the raw keysym, and fails whether Tk reports a different name or WI-13 maps it to the
wrong direction. **Only the physical keypress stays human.**

## Everything else an agent could check, in one window

One rather than six, because each is a disturbance on somebody's desk and none of these
needed its own. Read from inside an `after` callback while it was up, closed by the same
callback, under a 90-second deadline outside pytest.

| | |
|---|---|
| a real window of its own (WIN-1) | mapped, confirmed from inside the loop |
| size, ground (WIN-2) | **400 × 570**, `#000000` |
| the title string (WIN-3) | **`Terminal Game`** |
| placed where WI-15 decided (WI-14b) | yes, and **not** at Tk's default (5, 38) |
| an absolute coordinate | **(600, 300) in, (600, 300) out** |

## What the pack refuses to claim, including about me

Lane B asked for this section and it is the one that matters:

- **925 tests pass and not one has seen a pixel.** Every visual check is genuinely open.
- **`test_placement.py` being green says nothing about WIN-4.**
- **A synthetic key event is not a physical one** — it travels through less of macOS.
- **I did not look at the screen either.** Every "checked" above is the toolkit or the data
  structures reporting, not an observation of appearance.

## WIN-4 is presented as a decision with a cost, not as a defect

The trace row reads **not met, wired to the fallback** — the wording matters, because "not
met" alone reads as *the anchor route was unavailable* and leaves a reader believing the
fallback is running. Until WI-14b it was not.

And lane B's residual, which it could only half-close, is placed where it belongs: Tk
*accepts* an absolute coordinate and reports it back — I re-confirmed the round trip today
— but **nobody has shown Tk's (0, 0) is the display server's (0, 0)**. That is dormant
while the reader reads nothing and **load-bearing the moment one does**, so it is part of
the price of granting Accessibility rather than a problem with today's build.

## The glyph check is framed as cosmetic, deliberately

Menlo's box-drawing glyphs are designed to tile and overlap at every joining edge. So the
question put to the user is *"does it look right to you?"* and not *"do we need a
different toolkit?"* — that was the point of measuring it in WI-7 and it would be wasted
by asking it as a risk.

## What I did not do

**I did not run the real entry point.** `python -m terminal_game.shell.game` has no
watchdog **by design** — a game that closed itself on a timer would be a time limit, and
GAME-3 forbids one — so it waits for a key only a person can press. Running it would have
hung with a window on the user's desk. I confirmed the entry point resolves and `main` is
callable without invoking it.

## Window hygiene

WI-7's pattern, unchanged — that was the stated reason this item stayed in lane A: the
hazard is a second pattern, not a second author. Watchdog through `after` inside
`mainloop`, belt-and-braces second close, window reaped in a `finally` whatever happens,
never a second `tkinter.Tk()`, crash reports counted either side.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
