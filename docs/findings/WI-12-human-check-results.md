# WI-12 — the six human checks, and where their answers go

This is the **answer sheet** for the six checks in
`docs/findings/WI-10-human-checks.md`. That document says what to do; this one
records what was seen.

**Status of this file as it stands: all six are NOT RUN.** Every verdict field
below is deliberately, visibly empty. Nothing here has been filled in from a
passing test, a green `./verify`, or an agent's inference, and nothing here may
be. When the answers arrive, somebody fills them in — they are not to be
discovered later to have been quietly guessed.

---

## Why they are not run

**The user was not reachable from the session that produced this document.**
WI-12 was run by an agent, the six checks need a person at the screen, and the
request has been put to the user by the technical lead. That is the whole of the
reason for H2–H6.

**H1 is different, and permanently so.** H1 asks where the game's window lands
*relative to the window `./play` was typed in*. Every agent in this project runs
without a controlling tty — `tty` reports "not a tty" — so there is no window it
was typed in, and therefore no reference window for the offset to be measured
from. **This is not "not run this time".** No agent on this project, on this run
or on any future run, can ever make check H1, however the code is changed,
because the thing being measured does not exist on an agent's side of the
seam. It is the user's, permanently. WI-10 reduced it to one command —
`./check-window-placement` — so that it costs the user a minute rather than an
afternoon.

---

## What a green suite and a green `./verify` do *not* say

`./verify` passed 3 of 3 stages on this build, and the suite reports 749 tests,
OK (skipped=2). **Neither is evidence for any line in this table**, and neither
has been recorded as such.

The machine checked the arithmetic that decides where a window *should* go, the
script that *asks* Terminal for a 40 × 30 window in Menlo 18 titled *Terminal
Game*, and the pictures the renderer *produces*. It did not see a screen. The
six below are exactly the residue: where a window actually landed, what a title
bar actually read, whether text was actually comfortable to read, whether
anything actually flickered, whether two blocks could actually be told apart,
and whether pressing `q` actually left everything else alone.

---

## The answer sheet

For each check: the requirement it demonstrates, what the user does, what they
should write back, and an empty verdict.

---

### H1 — where the game window lands · **WIN-4**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.** *Structurally impossible for any
agent, on this run or any future one — see above.*

**What the user does**

> Move the Terminal window you are about to type in near the **bottom-right
> corner** of a screen — and, if there is more than one screen, a screen that is
> **not** the main one. Then, in that window:
>
> ```
> ./check-window-placement
> ```
>
> A window titled *Terminal Game* opens. Look at where it landed, then press
> `q` in it. The script prints its verdict.

**What they write back**

- The two positions the script printed and the offset it worked out.
- Which of `LANDED_RIGHT`, `LANDED_SHIFTED`, `LAYOUT_UNREADABLE`, `NO_REPORT`
  it ended with.
- **In their own words:** where the window actually appeared relative to the one
  they typed in, and whether all four of its edges were on the screen.

**Two things worth knowing when the answer is read.** `LANDED_SHIFTED` is not by
itself a failure — the launcher deliberately pulls the window back on screen
when the plain offset would have pushed it over an edge, which is precisely what
should happen when launching from a corner. And if the game opens on the *main*
screen having been launched from another, the output should be searched for a
line beginning `could not read the screen layout`: that line is the known fault,
it has been seen once, it has never been reproduced on demand, and a second
sighting is worth a great deal.

---

### H2 — that `q` closes the game's window and nothing else · **WIN-5**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.**

**What the user does**

> Open three or four other Terminal windows and put something recognisable in
> each. Then, in a different window, `./play`, and press `q`.

**What they write back**

Whether the game's window closed, how quickly, whether anything else on screen
changed, and **whether any dialog appeared** — in particular *"Do you want to
terminate running processes in this window?"*. If one does appear: **Cancel**,
not Terminate, and the exact wording.

**This one is also entangled with open question A1** (§9 of the plan): whether
WIN-5 means the window vanishes on the final frame or when the player presses
`q`. The build the user will be testing takes the second reading — the last
picture stays up and `q` closes the window — so H2's instructions describe that
behaviour. **A1 is unanswered.** If the answer turns out to be "on the final
frame", H2 must be re-run against a changed build, and this line becomes a
verdict about the wrong behaviour.

---

### H3 — that the title bar reads exactly *Terminal Game* · **WIN-3**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.**

**What the user does**

> `./play`, look at the title bar of the new window, press `q`.

**What they write back**

The title, **copied exactly**, including any dashes and anything on either side
of them. If it settled from something else, what it started as and roughly how
long it took.

**Note for whoever reads the answer.** A brief wrong title in the first
half-second is expected and is not a failure — it is the user's own login
profile running before the game starts; on this machine it has shown
`rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519`. Judge the title
**after** the game's picture has appeared. This check is also version-sensitive:
the title recipe was measured on macOS 26.6.2 only and depends on Terminal's
per-profile title settings, so it must be re-run on any other macOS version.

---

### H4 — that 18 pt Menlo is large enough to read comfortably · **WIN-2**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.**

**What the user does**

> `./play`, sit at a normal distance from the screen, decide, press `q`.

**What they write back**

Comfortable, too small, or too big — and if it is wrong, **what size they would
want instead**. Also whether the characters look stretched, squashed or unevenly
spaced, which would mean the font is not the one intended.

**This is a judgement, not a measurement**, and if it is wrong it is one
constant. The *measurable* half of WIN-2 — that the window really is 40 × 30 —
is covered by a test and by `./verify`'s smoke stage; the font's legibility is
not, and cannot be.

---

### H5 — that nothing flickers while the ghost moves · **SCRN-7**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.**

**What the user does**

> `./play` and **do not touch the keyboard** — watch the ghost cross the maze
> and turn corners. It will probably catch the stationary player (measured once
> at 4.14 s); press `q` and run again. Two or three runs, then watch once more
> while moving with the arrow keys.

**What they write back**

What they saw. *"Nothing flickered"* is an answer; *"there is a flicker at the
bottom of the screen about once a second"* is the more useful one. If the
ghost's movement felt wrong rather than looked wrong, that too, and in what way.

**Two things already measured, so the user does not chase them.** The redraw
budget is 143 ms between ghost moves and the slowest single redraw measured was
20.3 ms — about a seventh of it. And the ghost really does move seven times a
second: three runs of about twelve seconds measured 6.99990, 7.00078 and
6.99999 moves per second. So flicker, if seen, is not a timing shortfall, and a
ghost that *feels* wrong is not running at the wrong rate.

---

### H6 — that the picture looks right · **SCRN-3, SCRN-5**

**Verdict:** *(empty — not run)*
**Status:** **NOT RUN — awaiting the user.**

**What the user does**

> `./play`, and compare what is on screen with the full-size drawing in
> `docs/FUNCTIONAL_REQUIREMENTS.md` §3. Press `q` when done.

**What they write back**

Whether the walls join up into corners, tees and crossings with no gaps; whether
a lone wall square is a single solid block; whether the player (`▐█▌`, bright
yellow) and the ghost (`▗█▖`, pink) can be told apart **instantly, by both
colour and shape**; and any square of the picture that looked wrong, with
roughly where it was.

**This is the one human check with the most machine work behind it, and it still
needs eyes.** All 16 wall masks and both entity glyphs are asserted
character-for-character against a golden fixture, and three scripted games are
compared to a recorded final picture. What no test can do is look at 18 pt Menlo
on a real screen and say that yellow and pink are distinguishable *at a glance*,
which is what SCRN-5 actually asks for.

---

## Summary table

| # | Check | Requirement | Verdict | Status |
|---|---|---|---|---|
| **H1** | Where the game window lands | WIN-4 | | **NOT RUN — awaiting the user. No agent can ever run this one.** |
| **H2** | `q` closes the game's window and nothing else | WIN-5 | | **NOT RUN — awaiting the user** (and see open question A1) |
| **H3** | The title bar reads exactly *Terminal Game* | WIN-3 | | **NOT RUN — awaiting the user** |
| **H4** | 18 pt Menlo is comfortable to read | WIN-2 | | **NOT RUN — awaiting the user** |
| **H5** | No visible flicker while the ghost moves | SCRN-7 | | **NOT RUN — awaiting the user** |
| **H6** | The walls look right; player and ghost tell apart | SCRN-3, SCRN-5 | | **NOT RUN — awaiting the user** |

**0 of 6 run. 6 of 6 awaiting the user.**

---

## What to do when the answers arrive

1. Fill the **Verdict** column with `pass`, `fail`, or `not run`, and paste the
   user's words **verbatim** under the corresponding section — their words, not
   a paraphrase, and not a tidy-up.
2. Change that section's **Status** line from *NOT RUN* to the date it was run.
3. Update the count under the summary table.
4. If any check **failed**, it is a defect against the requirement named in its
   row, and the project's definition of done (plan §13, item 4) is not met until
   it is either fixed or the failure is recorded as accepted by the user.
5. **H1's note stays as it is** whatever the answer. It is a statement about what
   an agent can do, not about what happened on one particular run.
