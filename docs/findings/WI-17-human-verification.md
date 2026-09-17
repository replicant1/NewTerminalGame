# WI-17 — the human-verification pack

**Nobody has yet seen this game.**

It has opened on this desktop several times — WI-6's, WI-7's, WI-14's and this item's
window tests — and every time it closed itself in about a second under a watchdog, with
nobody watching. Everything anyone knows about how it *looks* is inferred from data
structures and font outlines. **You are the first.**

**Written** 17 September 2026, 02:28Z, against `main` = `874e0ca`,
**925 passed, 0 failed, 0 skipped, 7 deselected**.
**Input:** lane B's checklist, `docs/findings/WI-17-verification-checklist.md` — written by
the lane that built the input translation and the window placement, because *"the checks I
fail to think of are exactly the ones I failed to think of when writing the code."*

---

## Part 1 — What you have to do, and it takes two minutes

### Start it

```sh
cd /Users/rodneybailey/CursesProjects/NewTerminalGame
.venv/bin/python -m terminal_game.shell.game
```

A 400 × 570 window appears, **centred on your main display**, showing a maze. The ghost is
already moving. **Press `q` to quit** — that is the only way out apart from the window's
close button, and there is no time limit, so it will wait as long as you like.

> **This is the real game with no watchdog.** If a key ever fails to close it, use the
> window's close button, which is wired independently and always works.

### The five checks, in order

Each says **what a failure looks like**, because "does it seem right?" is not a question
anyone can answer and "is it doing this specific wrong thing?" is. Lane B's form, kept.

---

**1. The titlebar** *(WIN-3, plan human item 2)*

**Look at the titlebar.** It should read exactly **`Terminal Game`** — two words, nothing
before or after it.

*A failure looks like:* anything appended — a filename, `python`, a path, a modification
dot. Tk reports the string as correct; what nobody can check without you is whether macOS
draws something else around it.

---

**2. The arrow keys** *(CTRL-1, CTRL-2)*

**Press Up, Down, Left and Right in turn**, from a square with corridor on more than one
side.

*A failure looks like, in order of likelihood:*
- **An arrow that does nothing at all.**
- **Two arrows doing the same thing.**
- **Up and Down swapped, or Left and Right swapped.** Up must move the player *towards the
  top of the screen*.
- The player moving **more than one square per press**, or drifting on after you let go.

*Not a failure:* a press towards a wall doing nothing. That is CTRL-3 working. Try a
direction with a free side.

---

**3. `q`, `Q`, and everything else** *(CTRL-4, CTRL-5)*

**Press `q`.** Start it again. **Press `Shift`+`q`.** Start it again and **type `hello`,
`12345`, `F1`, `Escape`, `Tab` and the space bar**, watching the maze.

*A failure looks like:*
- **`Q` not quitting when `q` does.** These are two separate keys to Tk, and the shifted
  one is the likelier to be wrong.
- **Anything you type appearing on the screen** — a character anywhere in the grid, or a
  text cursor becoming visible. **This is the only way to check CTRL-5; no automated test
  can see the screen.**
- `Escape` or the space bar quitting, or doing anything at all. They must not.

---

**4. Is the type big enough to read comfortably?** *(WIN-2, assumption P4, human item 3)*

**Menlo at 16 point**, giving a 10 × 19 pixel cell. There is no objective test for
"comfortable" and there never will be.

*If it is too small*, say so — it is **one constant** (`metrics.FONT_SIZE`) plus the two
tests that quote it. One thing to know before you ask for bigger: **16 is the largest Menlo
size whose cell grid is exact.** Above it a 40-character row drifts by up to 18 pixels
against 40 separately-placed characters. It is still workable, but WI-19 would need to
force per-cell placement, so "make it 18" is not quite free.

---

**5. Do the maze walls look joined up?** *(SCRN-3, human item 8)*

**Look at a long run of wall.** It should read as **one unbroken double line**, not as a
row of short dashes with gaps.

**This is a cosmetic check and not a risk**, and that distinction is the result of a
measurement. Menlo's box-drawing glyphs are **designed to tile**: every glyph with an
east–west arm overshoots its cell by 0.156 px on each side, and every glyph with a
north–south arm by 0.562 px above and 0.828 px below — deliberate overlap, so there is no
gap for a seam to show through. *(`docs/findings/WI-7-box-drawing-ink.md`.)*

What that measurement cannot tell you is whether the renderer preserves it at 16 pt, where
the horizontal overlap is a fraction of a pixel. **So the question is "does it look right
to you?", not "do we need a different toolkit?"**

---

### And one thing to notice while you are there

**A "Python" tile appears in your Dock** whenever the test suite runs, for as long as it
runs — a few seconds. It is not a window, it never takes focus, and it goes when the suite
finishes. *Measured: 7 visible applications before a run, a Python one during it, gone
after.* Building a Tk root registers the process as a foreground application and there is
no way to suppress that on Tk 8.5.

**If that is fine, nothing changes.** If it is not, the Presentation and Shell tests would
have to be excluded from the default suite, which costs the suite its coverage of
everything that touches a window. *(Plan human item 7, assumption P9 — currently proceeding
on "acceptable".)*

---

## Part 2 — A decision only you can make

### WIN-4: the window does not appear beside whatever you were last looking at

**WIN-4 is not met.** It is *wired to a fallback*, which is a different thing, and the
distinction matters:

| | |
|---|---|
| **What WIN-4 asks for** | the window appears a little below and right of whatever window you were last using |
| **What it does** | it centres on your main display — at (556, 206) on this 1512 × 982 screen |

Reading another application's window position needs macOS **Accessibility permission**,
which no agent can grant itself and which S-2 measured as prompting once per target
application. So the game ships with a reader that reads nothing, deliberately, rather than
guessing or prompting.

**Your options:**

1. **Leave it.** The window centres on the main display. Predictable, no permission, and
   WIN-4 stays formally unmet. *This is what ships today.*
2. **Grant Accessibility permission** and let the real reader work.

**If you are considering option 2, there is a cost nobody has paid yet.** WI-15 established
that Tk *accepts* a negative absolute origin and reports it back unchanged — I re-confirmed
the round trip on a real window today, placing it at (600, 300) and reading (600, 300)
back. **What has never been shown is that Tk's (0, 0) is the display server's (0, 0).**
While the reader reads nothing that assumption is dormant and harmless. **The moment a real
anchor is read, it becomes load-bearing** — and if the two spaces disagree, the window will
land somewhere wrong in a way that only shows up on a second display or a rearranged desk.

*The cheap way to settle it, if you want to:* with the game open, note where the window is,
then tell someone to place it at a known coordinate and measure where it lands against a
ruler or another window. One extra placement in a window that is already open.

**Do not drag the window to a second display to test this.** It proves nothing about
placement and risks a dialog on a screen nobody is looking at.

---

## Part 3 — What an agent checked, so you do not have to

All on the real, running, assembled game, on this desktop, today. **Crash reports: 14
before, 14 after. Zero new. Nothing left behind — the same visible applications before and
after every run.**

| Checked | Result |
|---|---|
| A real window of its own opens (WIN-1) | **yes** — mapped, confirmed from inside the event loop |
| Its size (WIN-2) | **400 × 570 px** — 40 × 30 cells of Menlo 16 |
| Its background (WIN-2) | **`#000000`** |
| The title string Tk holds (WIN-3) | **`Terminal Game`**, exactly |
| It is placed where WI-15 decided (WI-14b) | **yes** — and *not* at Tk's default (5, 38) |
| An absolute coordinate round-trips | **(600, 300) in, (600, 300) out** |
| The four arrow keysyms Tk reports | **`Up`, `Down`, `Left`, `Right`** — exactly the names WI-13's table expects, each mapping to the right direction |
| A key with no meaning | **delivered, and translated to nothing** (CTRL-5's mechanism) |
| It closes on `q` and on the close button | **yes**, both, and the loop returns |
| The whole picture reaching the glass | **all 30 rows**, cell for cell |

**The arrow-key check used to be yours.** It was moved into this item and automated, so
what is left for you in check 2 is only the *physical* keypress — which is the honest
irreducible, and the only part of it a machine cannot do.

---

## Part 4 — What must not be claimed, including by me

Lane B asked for this section and it is the most important one.

- **A green suite says nothing about how anything looks.** 925 tests pass. Not one of them
  has seen a pixel. Every visual check above is genuinely open.
- **`test_placement.py` being green says nothing about WIN-4.** It tests the *decision*;
  the shipped reader follows nothing. WIN-4's trace row reads **not met, wired to the
  fallback**, and "not met" alone would wrongly imply the fallback was the problem.
- **"The keysym names are valid" is not "the arrow keys work."** That gap is now closed by
  a real key event on a real window — but only for a *synthetic* event. A physical key
  travels through more of macOS than `event_generate` does.
- **Tk's coordinate space has not been shown to match the display server's.** See Part 2.
- **I did not look at the screen.** Every "checked" above is something the toolkit or the
  data structures reported. I have never seen this game either.

---

## Part 5 — The state of the requirement codes this item touches

| Code | Settled by | Status |
|---|---|---|
| WIN-1 | agent, on a real window | **verified** |
| WIN-2 (size, ground) | agent | **verified** |
| WIN-2 (comfortable type) | **you**, check 4 | open |
| WIN-3 (title string) | agent | **verified** |
| WIN-3 (titlebar as drawn) | **you**, check 1 | open |
| WIN-4 | — | **not met, wired to the fallback**; your decision, Part 2 |
| WIN-5 | agent — `q` and the close button both end it | **verified** |
| CTRL-1 (keysym names and directions) | agent, synthetic events | **verified** |
| CTRL-1, CTRL-2 (physical keys) | **you**, check 2 | open |
| CTRL-4 (`q`, `Q`) | **you**, check 3 | open |
| CTRL-5 (nothing echoed) | **you**, check 3 — *no automated test can see the screen* | open |
| SCRN-3 (glyphs join) | measured from the font; **you** confirm, check 5 | open, low risk |
| SCRN-7 (no caret) | agent — the surface refuses focus and has no insertion cursor | **verified**, but check 3 would catch it |

---

## Provenance

The human checks in Part 1 are lane B's, from
`docs/findings/WI-17-verification-checklist.md`, kept in its form because its form is the
point. Part 2's WIN-4 framing is lane B's finding, corrected after I measured that the
fallback was not running either — that is WI-14b, now fixed. Part 3's numbers are mine,
measured today. Part 4 is lane B's list with one line added about myself.
