# WI-17 verification checklist — lane B's input

**From:** developer B, who built WI-13 (input translation) and WI-15 (window
placement).
**For:** lane A, which writes and runs WI-17.
**Written:** 17 September 2026, 02:19Z, against `main` = `dc6fce3`.

Under the lead's rule for verification items, **the checklist comes from the
lanes that built the things being verified, and a different lane runs it**.
This is lane B's half. It covers what a person must look at in WI-13's and
WI-15's work, what WI-17 can convert from a human check into an agent check,
and — the part I care most about — **what must not be claimed.**

I have not tried to write WI-17. Where I suggest steps, treat them as the
content and not the form.

---

## 0. The one that will bite: placement is not wired to anything

**Checked at 02:19Z against `dc6fce3`: nothing in the project calls
`placement_for` or `move_to`.** `terminal_game/shell/placement.py` is
complete and tested, `GameWindow.move_to` exists and is tested, and **no
caller invokes either**. WI-14 owns that wiring.

So, as things stand:

> The game window appears wherever **Tk** puts it — measured at `(5, 38)` on
> this build — and not where WI-15 decided.

**Nothing in the suite catches this.** `test_placement.py` tests the
arithmetic in isolation; `test_window_placement.py` tests the join through a
window a test made itself. Neither knows whether the assembled game ever
asks. A person looking at the running game would see a window near the
top-left corner, which looks plausible and is wrong.

**What WI-17 should do:** before anything else, confirm the assembled game
actually calls `placement_for(...)` and `move_to(...)`. If it does not, the
rest of section 3 below is checking a default rather than a decision, and
should say so.

---

## 1. What must not be claimed

These are the sentences that would be wrong in a verification pack, and each
is wrong in a way a green suite actively encourages.

### 1.1 WIN-4 is **not met**, and `test_placement.py` being green says nothing about it

WIN-4 asks the window to appear *"a little below and to the right of whatever
window the player was last looking at."*

**The shipped anchor reader is `NoAnchor`. It reads nothing.** The route for
reading the real anchor is an unanswered question with the user (plan section
9, item 4; three routes measured in `docs/findings/S-2-anchor-window.md`), so
WI-15 deliberately chose none of them.

What is actually true today:

| claim | status |
|---|---|
| Given an anchor, the window is placed at anchor + (40, 40) | **verified, in the suite** |
| A failure to read the anchor degrades rather than crashing | **verified, in the suite** |
| The window follows the player's last window | **false** |

> **WI-17 must not record WIN-4 as verified.** The honest form is: *WIN-4 is
> met under assumption P2 and not in general; the shipped behaviour is to
> centre the window on the main display, which is a sane default and is not
> WIN-4.*

This is the single easiest mistake for WI-17 to make, because `test_placement.py`
names WIN-4 three times and passes.

### 1.2 "The keysym names are valid" is not "the arrow keys work"

WI-13 has a test that binds all six translated keysyms on a real Tk and
requires a nonsense name to be rejected. That proves **the names exist and
are spelled correctly**. It does not prove that pressing an arrow produces
them. See section 2.

### 1.3 A green suite says nothing about how anything looks

Obvious, but worth writing where somebody tired will read it. The suite has
never seen a rendered glyph. Everything in section 4 is genuinely open.

### 1.4 Tk's coordinate space has not been shown to match the display server's

S-2 flagged this and WI-15 only half-closed it.

**What WI-15 established** (`docs/findings/WI-15-tk-geometry-signs.md`): Tk
*accepts* a negative absolute origin, `+-877+-1348` round-trips exactly, and
the tidy `"{:+d}"` format means something else entirely.

**What WI-15 did not establish:** that Tk's geometry `(0, 0)` is the *same
point* as the display server's `(0, 0)`, or that a window asked for at Tk
`(x, y)` actually appears at display-server `(x, y)`.

It does not matter while the shipped reader is `NoAnchor` — centring is
computed and applied in one space. **It matters enormously the moment a real
anchor is read**, because the anchor's coordinates come from the display
server and the placement goes to Tk. Section 3.3 is a cheap check for it and
is worth doing now rather than after the user rules.

---

## 2. What WI-17 can convert from a human check to an agent check

The lead has ruled this is WI-17's work rather than a new item, and it
shrinks the human pack, which is that item's purpose.

**Extend `tests/test_window.py::test_a_key_event_reaches_the_callback` from
`q` to the four arrows.**

That test already opens, focuses, generates, reaps and closes correctly. It
proves `event_generate("<Key-q>")` delivers and that `event.keysym` comes
back `"q"`. Doing the same for `<Key-Up>`, `<Key-Down>`, `<Key-Left>` and
`<Key-Right>` would prove the four arrow keysyms survive real Tk event
delivery — which is strictly more than WI-13's bind-time check.

Better still, assert through the translator rather than on the raw string, so
the test pins the whole path:

```python
from terminal_game.presentation.keys import intent_for
# ... bind "<Key>", generate "<Key-Up>", then:
assert intent_for(seen_keysym) is Intent.MOVE_NORTH
```

**What it still would not prove:** that the *physical* arrow key on this
keyboard generates that event. `event_generate` is Tk talking to itself.
That residue is section 3.1 and it is the honest irreducible.

---

## 3. What only a person can settle — WI-13 and WI-15

Each with what to do, and **what failure looks like**, because "does it seem
right?" is not answerable and "is it doing this specific wrong thing?" is.

### 3.1 The four arrow keys each move the player the right way (CTRL-1)

**Do:** in the running game, press Up, Down, Left, Right in turn, from a
square with corridor on all four sides if one is available.

**Look for, in order of likelihood:**
- **An arrow that does nothing at all** — that keysym is missing from
  `ARROW_INTENTS` or misspelled.
- **Two arrows that do the same thing** — a duplicated entry in the table.
- **Up and Down swapped, or Left and Right swapped** — the direction mapping
  is inverted. Up must move the player *towards the top of the screen*.
- The player moving more than one square per press (CTRL-2), or continuing to
  drift after the key is released.

**Note:** a press towards a wall doing nothing is **correct** (CTRL-3), not a
failure. Test on a square with a free side.

### 3.2 `q` and `Q` both quit (CTRL-4), and nothing else does anything (CTRL-5)

**Do:** press `q`. Restart. Press `Shift`+`q`. Then restart and type a few
letters, digits and function keys — `hello`, `12345`, `F1`, `Escape`, `Tab`,
`space` — and watch the maze.

**Look for:**
- **`Q` not quitting while `q` does.** These are two distinct keysyms, not one
  case-folded comparison, and the shifted one is the likelier to be wrong.
- **Anything typed appearing on screen.** CTRL-5 says *"nothing typed is
  echoed into the maze"*. A character appearing anywhere in the grid, or a
  text caret becoming visible, is a failure. This is the only way to check it:
  no automated test can see the screen.
- `Escape` or `space` quitting, or doing anything at all. They must not.

### 3.3 The window's position, and the coordinate-space question (1.4)

**Given section 0, first establish which you are looking at**: a window
placed by WI-15, or Tk's default corner.

**If placement is wired**, the shipped behaviour is *centred on the main
display*:

**Do:** start the game and look at where the window is.

**Look for:**
- **Top-left corner, roughly (5, 38)** — placement is not being called at
  all. This is section 0.
- **Off the screen, or half off it** — the display rect passed to
  `placement_for` is wrong, or something is clamping.
- **Not centred but plausible** — the window size passed in does not match
  the real one (it should be 400 × 570).

**And the cheap check for 1.4, worth doing while a window is open:** place
the window at a known absolute coordinate — say `(600, 300)` — and compare
where it lands against a ruler or another window whose position is known. If
Tk's space matches the display server's, it lands at 600 across and 300 down
from the top-left of the main display. **This is the check that de-risks
WIN-4 before the user rules**, and it costs one extra placement in a window
that is already open.

**Do not** drag the window to a second display to test negative coordinates.
That proves nothing about placement and risks a modal sheet on a screen
nobody is looking at.

---

## 4. What a person must settle that is not lane B's, listed for completeness

These are not mine and I have not checked them; they are here so the pack is
whole and because two have moved since the plan was written.

- **WIN-3, the titlebar reads exactly `Terminal Game`** (plan section 9, item
  2). Set directly under candidate 2, so this should be a formality — but
  nobody has looked at a titlebar.
- **WIN-2 / P4, the type is large enough to read comfortably.** No objective
  test exists. P4 is retired *by measurement* for the metrics (Menlo 16, cell
  10 × 19, window 400 × 570) but not for legibility, which is the part that
  needs eyes.
- **SCRN-3, the wall glyphs join up neatly.** Lane A's `Menlo.ttc` parse
  established that the box-drawing glyphs are *designed* to tile — they
  overlap at every joining edge. **That is evidence at the font level, not at
  the rendered level.** The remaining check is cosmetic rather than
  structural, and that is a real change in its status.
- **STAT-1/2/3, the status line literals** (ruling C-4, and plan section 9
  item 6). The specimen is normative including its leading space. Low stakes.
- **END-4, the final picture on a loss.** I checked this through the real
  stack — 106 games played to a genuine `CAUGHT`, the ghost drawn over the
  player every time, zero violations — so what remains is only whether it
  *looks* like what happened, not whether it is composed correctly.

---

## 5. Two things that would make the pack better, offered not prescribed

**Say what was checked and what was not, per requirement code.** WI-18 is
building exactly that table. A verification pack that hands the user five
questions is more useful than one that hands them "does it look right?", and
WIN-4 in particular needs to appear as *not checked because it is not
implemented* rather than being quietly absent.

**Put section 0 at the top of the run, not the bottom.** If placement is not
wired, several of section 3's checks are checking Tk's defaults and the
person's time is better spent knowing that first.

---

## Provenance

Everything asserted here as measured was measured by me on this machine:
the Tk geometry behaviour (02:12Z, `docs/findings/WI-15-tk-geometry-signs.md`),
the keysym validation (02:07Z, WI-13's PR), the END-4 stack check and the
"nothing calls placement" check (02:19Z, against `dc6fce3`). Everything I
took from another lane is attributed to it. Where I am reasoning rather than
measuring — sections 1.3 and 4 — it says so.
