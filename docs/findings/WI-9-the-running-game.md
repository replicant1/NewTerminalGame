# WI-9 — what the wired game does when it is actually running

Measured on the WI-9 branch, after the stand-ins were deleted and the real
rules and the real renderer were wired into `loop.run_game`. Everything below
is from a **real process**: a real generated maze, real ncurses on a 40 × 30
pseudo-terminal, the real `view.render`, and `time.monotonic`. Nothing is
simulated except the terminal itself, which is a pty rather than a Terminal
window because this agent has no controlling tty and will not script
keystrokes into somebody else's application.

Three runs of about 11.7 seconds each, with **nobody pressing anything** until
a `q` arrives at the end. `/usr/bin/python3` 3.9.6, macOS 25.6.0.

The probe is `scratchpad/tickprobe.py`, which is not kept — the numbers are.

## 1. GHOST-1 holds in the real process, with the real picture being drawn

| Run | Ticks | Rate | Gap mean | Gap min / max | Drift vs. an ideal ¹⁄₇ s grid |
|---|---|---|---|---|---|
| 1 | 83 | **6.99990 /s** | 142.859 ms | 128.390 / 154.043 ms | mean 1.195, max 10.895 ms |
| 2 | 83 | **7.00078 /s** | 142.841 ms | 130.839 / 155.530 ms | mean 1.130, max 12.222 ms |
| 3 | 83 | **6.99999 /s** | 142.857 ms | 138.429 / 147.337 ms | mean 0.727, max 4.469 ms |

The architect measured 6.997 ticks/s against a stand-in that did nothing and a
picture that was not the real one. **The real game keeps the same rate**: three
runs inside 8 parts in 100 000 of seven per second. The additive deadline
(`ticker.advanced`) is why — an individual gap wanders by up to 13 ms, and the
*cumulative* drift stays near a millisecond because the lateness is thrown away
each time rather than added in.

## 2. Painting every turn costs far more than the architecture records, and it still does not matter

`loop.py`'s docstring says the loop paints on every turn even when nothing
changed, and that "it costs 0.25 ms of a 143 ms tick". That number is
`ARCHITECTURE.md` §7's *Repaint cost* row, which measured a **naive
`addstr` loop against a bare curses window** — not this adapter, and not the
renderer that feeds it. Measured here, per turn:

| | mean | max |
|---|---|---|
| `view.render` — building the `Frame` | 3.4 – 11.8 ms *(varies with machine load)* | 20.3 ms |
| `screen.paint` — the curses adapter | 0.5 – 1.4 ms | 3.1 ms |
| **together** | **3.9 – 13.2 ms = 2.7 % – 9.2 % of a tick** | 14 % of a tick |

So the real per-turn cost is of the order of **50 times** the documented
figure, and essentially all of it is the pure renderer, which nobody had
measured. The spread between runs is machine load, not the game.

**This is a documentation defect, not a game defect.** Even the worst single
frame observed left 86 % of the tick unused, and §1 above shows the tick rate
never moved. But someone who later reads "0.25 ms" and concludes there is a
thousandfold of headroom would be wrong by two orders of magnitude, so the
number is worth correcting where it is written down.

## 3. The ghost never reverses — WI-7's finding, confirmed in a running game

**0 reversals in 195 live ghost moves**, across the three runs. 149 of those
195 (76 %) were the GHOST-2 clause — straight on — and the other 46 were
GHOST-3 random turns at a junction, none of which was a turn back the way it
came.

WI-7 measured this over 30 seeds of the generator and explained it: MAZE-5
leaves no corridor square with fewer than two ways on, so the last clause of
`ghost_heading` — reverse when there is nothing else — is unreachable on a
generated maze. It is now also true of games that were actually played.

**If you ever see the ghost turn round in a real game, something is wrong.**

## 4. A game ends by itself

One of the three runs came back **`CAUGHT`**, score 0, all 267 dots still on
the board, the status line reading ` CAUGHT  score 0   q quits`. The player
never moved from `(14, 9)`, where START-1 put them; the ghost started at
`(1, 1)`, took no notice of where the player was (GHOST-4), and arrived on
`(14, 9)` after **29 ticks — 4.14 seconds**. The other two runs were still in
play after 83 ticks (11.9 s).

That is END-1's second half — *"whether the player walked into the ghost or the
ghost walked into the player"* — happening unprompted in a real process, and
the whole of END-5 and END-6 with it: the remaining 54 ticks of that run
changed nothing, the last picture stayed, and the `q` at the end was what
returned.

One sample of three is not a survival curve, so do not read a rate into it.
What it does establish is that **standing still is not safe**: a game can end
without the player doing anything at all.

## 5. The first picture, drawn by the real entry point

`/usr/bin/python3 "Terminal Game"` with no controlling terminal takes the
plain-text path — it paints one frame and returns rather than blocking in a
window nobody could then close. The frame it wrote:

```
╔═══════╦═══════════════════════════╗
║▗█▖▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║
║ ▪ ║ ▪ ║ ▪ ║ ▪ ═════════ ▪ ╔════ ▪ ║
║ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║
║ ▪ ║ ▪ ║ ▪ ╠═══════════════╣ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ║
╠═══════════╣ ▪ ■ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║
║ ▪ ■ ▪ ■ ▪ ║ ▪ ╔═══╝ ▪ ╠════ ▪ ║ ▪ ║
                     ... 20 more rows ...
╚═══════════╩═══════════╩═══════════╝
 score 0    arrows, q quits
```

29 maze rows and the status line; the maze's 19 columns at two picture columns
each fill 0–36 and columns 37–39 are blank (MAZE-1); walls joining into
corners, tees and crossings with lone wall squares as `■` (SCRN-3); the player
`▐█▌` at the centre (START-1); the ghost `▗█▖` at the far corner (START-2); a
dot on every corridor square but the player's (START-3); `score 0` (START-4,
STAT-2).

**What this does not show is colour.** The plain-text path carries style
identifiers, not attributes, and a pty capture is bytes rather than what a
human sees. SCRN-3's *blue*, SCRN-4's *dim gold*, SCRN-5's *bright yellow* and
*pink*, SCRN-6's *cyan*, and SCRN-7's *no flicker* are the user's to judge —
they are human checks H3–H5 and this finding does not claim them.
