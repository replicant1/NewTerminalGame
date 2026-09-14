# WI-14b — what the machine could settle, and what it could not

**Item:** WI-14b, the acceptance run. **Lane:** DEV-B, iteration M3.
**Measured on:** `wi-14b-acceptance-run` at `38926b1`, `main` at `84e09be`, macOS, Terminal.app, Python 3.9.6.
**Windows opened: 7. All 7 closed. Census returned to its starting value every time. No modal sheet.**

---

## What was settled, on the real thing

### The whole join, against the real game

The acceptance pack was written in WI-14a against M0's walking skeleton, because the real game was not
merged yet. This is the first run against the wired game.

| | |
| --- | --- |
| window created | +0.12 s |
| configured (40 × 30, title, font, colours) | +0.32 s |
| game running in the tab | +0.39 s |
| **picture drawn** | +0.65 s |
| `q` sent | +0.88 s |
| **game gone** | **+0.96 s — 0.08 s after the `q`** |
| window closed, `visible=false` | +1.20 s |
| visible windows before / after | **1 / 1** |

**5 exercises ok, 0 failed, 3 observed for a person.**

### The picture is the specification's

Read back from the live tab: 30 rows, widest 37 columns, three blank margin columns. Joined-up double
walls, a dot on every corridor square, the player `▐█▌` near the middle, the ghost `▗█▖` across the
maze, two lone blocks `■`, and the status row ` score 0    arrows, q quits`.

**One detail closes an open thread.** A `╬` crossing appears in the live picture. That is the single
entry in WI-5a's glyph table with **no worked example behind it** — the specification's own picture
never contains a four-way crossing, and the entry was inferred from SCRN-3's word *"crossings"* plus
the Unicode name. It is now observed in a real generated maze on a real screen.

### GHOST-1's rate, measured live rather than against an injected clock

78 samples over 5.97 s of a real window, tracking the ghost's glyph: **43 distinct positions, 7.0
moves per second.** GHOST-1 asks for about seven.

In the same run, with nobody pressing anything, the **player occupied exactly one position** for the
whole six seconds — which is GHOST-1's *"whether or not the player is moving"* seen from the other
side, and CTRL-1's "the player moves only when a key is pressed".

*Caveat, stated because the number looks better than it is:* each capture takes ~0.08 s, so this
counts changes between samples. At 7 moves a second the sampling is faster than the ghost and the
count is close, but it is an estimate rather than a tick count.

### The game is unbounded, as §11.15 says

With `--hold` retired, a session ran for **6.0 s with nobody at the keyboard and was still going**. It
ended when the pack sent `q`, in 0.08 s. This is why anything that starts a game unattended has to
arrange its own way out, and why the pack does.

---

## The arrow keys: three attempts, and no answer

**This is the one gap nobody has closed, and I did not close it either.** The whole sequence is here
because two of the attempts nearly became false findings, and the shape of the failure is the useful
part.

**Attempt 1.** Six arrow escape sequences into the tab via `do script`. **0 of 6 moved the player.**
Not reported: I had not checked which directions were walls, and an arrow into a wall correctly
changes nothing at all (CTRL-3). A dropped key and a wall look identical if you do not know which is
which.

**Attempt 2 — a hypothesis with a named mechanism, and it was wrong.** With `keypad(True)`, ncurses
waits **ESCDELAY** ms (default **1000**) after a bare ESC to decide whether a sequence follows. WI-11's
loop recomputes its key-read timeout as the time to the next tick, which at seven ticks a second is at
most **143 ms**. That would abandon the sequence before ncurses could assemble it.

Both arms, one window each: **as shipped 2 of 6 moved; with `ESCDELAY=25`, 1 of 6.** So the delay is
not the cause — and the arrows evidently work *sometimes*, which killed attempt 1's result at the same
time.

**Attempt 3.** Read the maze out of the captured picture, press only a direction the picture says is
open, and watch continuously rather than sampling once. **10 presses of `right` into an open way,
watched for 2 s at 12 Hz — the player never moved.** `q` on the same channel ended the game
immediately.

**Attempt 4, and the one that had to be withdrawn.** To tell *"the game drops arrow keys"* from
*"`do script` does not deliver escape sequences"*, I ran the game in a **pseudo-terminal** — no window,
WI-2's technique — and wrote the exact arrow bytes to the master. The player did not move, and the
probe concluded the defect was in the game.

**Then the probe had to `SIGTERM` the child — which means `q` had not worked either.** Re-run with `q`
as the control, first: **the game does not exit on `q` through that pty harness within 4 s.** Input is
not reaching the game there at all. The conclusion was my instrument, not the game, and it is
**withdrawn**.

### So what is actually known

- `q` sent as terminal input through `do script` ends the game reliably — many trials, 0.08 s.
- Arrow escape sequences sent the same way did **not** move the player in a controlled run into a
  demonstrably open way, and **did** move it twice in a less controlled one.
- A pseudo-terminal harness that cannot deliver `q` cannot say anything about arrows.

**I cannot distinguish "the game drops arrow keys" from "`do script` does not reliably deliver an
escape sequence".** Both are consistent with everything above. **Nothing here is evidence of a defect,
and nothing here is evidence against one.**

This does not weaken the case for the human check. It is the strongest argument for it this project
has produced: three automated attempts, two of which produced confident wrong answers before being
caught.

---

## What no machine on this project has ever checked

**Every colour in this game is unverified.** Not weakly — not at all. `contents of selected tab`
returns text and nothing else, so there is no path by which any automated check here could read a
cell's colour. SCRN-3 (blue walls), SCRN-4 (dim gold dots), SCRN-5 (bright yellow player, pink ghost)
and SCRN-6 (cyan status line) rest entirely on a person looking. Two of the five are substitutions
besides: an eight-colour terminal has no gold and no pink, so dim yellow and bold magenta stand in.

**Nobody has pressed a key on a real keyboard.** Every session that has ever ended on this project
ended on a timer or on a scripted `q`.

**WIN-3 is not met.** The title bar reads `rodneybailey — Terminal Game — Python -m
terminalgame.game_main`. Two of those components are absent from Terminal's scripting dictionary and
are governed by the player's saved profile, which assumption A3 forbids changing. Recorded as NOT MET,
and it stays that way.

**Q2 — the Automation permission — was granted before this project began.** Every measurement here and
in every other item was taken on a machine where it was already allowed. No agent can grant it, refuse
it, or confirm it. **The first-run behaviour of this software on a machine that has never granted it is
completely untested.**

---

## Two lines, not one — §11.11

Where the mechanism is met and the purpose clause is not, both halves are reported separately.

| | mechanism | purpose clause |
| --- | --- | --- |
| **WIN-2** | the window is 357 × 558 points for 40 × 30 at Menlo 14 — **measured, met** | *"legible"* — a human check, unsettled |
| **WIN-3** | the custom title is set on the captured window — **measured, met** | *"the title bar reads Terminal Game"* — **NOT MET**, and cannot be without changing the player's profile |
| **START-2** | the ghost starts on the corridor square at greatest straight-line distance — **tested exhaustively** | *"so the two always start well apart"* — the metric is an assumption, not a ruling; Euclidean was chosen and Manhattan and Chebyshev fit the words equally |
| **GHOST-1** | seven moves a second, independent of the player — **measured live at 7.0/s** | *"one ghost roams the maze"* — in **8 games of 500 (1.6 %)** the ghost circles a loop reaching 4.5 %–37.2 % of the maze and no random source can change it |

---

## What this does not establish

- **Nothing about how any of it looks.** Colour, legibility, flicker, the cursor, where the window
  lands — all of it is on the register and none of it is recorded as verified.
- **Nothing about a real keyboard**, as above.
- **Nothing about a refused permission**, as above.
- **Nothing about whether it is any good to play.** The maze properties are floors; the tick rate is a
  number. Whether the game is enjoyable is not a measurement and nobody has made the judgement.
