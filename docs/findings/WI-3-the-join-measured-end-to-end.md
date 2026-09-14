# WI-3 — the join, measured end to end against the real desktop

macOS 25.6.0, Terminal.app, Python 3.9.6. Every run below opened exactly one
window and closed it; the visible-window census was `7104` before and after each.

## Why timing is the evidence

The launcher's own success signal is worthless as proof that the game ran. It
reports on the *window*, not on what was in it — and it was measured saying
`window 7684 closed`, exit status 0, on a session in which the game never
started at all. So the question "did the real game really run in there?" has to
be answered by something the launcher cannot fake.

The game takes `--hold N`: it draws its frame and exits by itself after N
seconds. **If the session's elapsed time moves with N, the game ran.** If it
does not, the game was killed and the launcher is reporting on an empty window.

## The measurement that exposed the defect

`python3 -m launcher.game`, timed from outside, before the signal was fixed:

| asked for | session took |
| --- | --- |
| `--hold 5` | 1.00 s |
| `--hold 12` | 0.98 s |

Flat. The hold made no difference, because the game was being closed out from
under itself during the login shell's start-up. Both runs reported success.

## The same measurement afterwards

| asked for | session took |
| --- | --- |
| `--hold 5` | 6.13 s |
| `--hold 12` | 12.92 s |

**A 7-second difference in the hold shows up as a 6.79-second difference in the
session.** That is what establishes that the game really runs for as long as it
is told to, rather than being killed early or exiting on some other path.

### Does the residual matter?

The two fixed costs are visible in the numbers and neither is a concern:

- **Overhead per session: 1.13 s at `--hold 5`, 0.92 s at `--hold 12`.** That is
  window creation, configure, measure, move, and the final poll-and-close. It is
  consistent with the per-call timings measured separately (created +0.124 s,
  configured +0.316 s) plus the login shell's start-up before the game begins.
- **The 0.21 s by which 6.79 s falls short of 7 s** is polling granularity and
  ordinary scheduling noise. The launcher asks what is running every 0.1 s, so
  it may notice the game has ended up to a tenth of a second late, and the two
  runs need not round the same way. There is nothing systematic in it and it
  accumulates with nothing.

Neither number is load-bearing. What is load-bearing is that the difference
tracks the hold roughly one-for-one, which a killed game cannot do.

## The game really draws

Read back from a live window (7693) with `contents of selected tab`, three
seconds into a session — the whole frame, in 40 columns by 30 rows:

```
╔══════════════════════════════════════╗
║            Terminal Game             ║
║       the screen port is alive       ║
║   ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪    ║
║                 ▐█▌                  ║
║                 ▐▓▌                  ║
║           press q to quit            ║
╚══════════════════════════════════════╝
 score 0    arrows, q quits
```

(Blank rows elided; the real capture is 30 rows.) Walls, title, dots, the player
glyph, the ghost glyph and the status line all reach the glass through the
screen port, in a window the launcher created, sized and placed.

## The game exits on `q`, and the launcher then takes the window

This is the clause of WI-3 that a `--hold` expiry does *not* demonstrate, so it
was measured separately (window 7719):

| | |
| --- | --- |
| hold it was given | **30 s** |
| game running at | +0.76 s |
| `q` sent at | +2.76 s |
| game gone at | **+2.90 s** |
| window closed, session over at | +3.15 s |
| leaked windows | none |

The game ended **0.14 s after the `q`**, twenty-seven seconds before its hold
would have expired, so the `q` is the only thing that can have ended it. The
launcher then saw the process list go empty and closed the window by the
identity it had captured.

**How the `q` was delivered, and why it is safe:** `do script "q" in selected
tab of window id N` writes to that one tab's terminal. It names the captured
window id like every other call the launcher makes, so it does not depend on
which window has focus and does not inject a keystroke into whatever the person
at the machine happens to be looking at. `System Events`-style `keystroke` was
deliberately not used for exactly that reason.

This is a test harness technique, not something the launcher does — nothing in
`launcher/` sends input to the game. It is recorded here because it is the way
to exercise the `q` path again without a human, and the next person to touch
END-6 or WIN-5 will want it.

## What still needs a person

That `q` arrived as terminal input rather than from a keyboard. It proves the
game's read-key path, its quit condition and the launcher's response to the game
ending — but not that a human pressing `q` on a real keyboard reaches the same
code. That last step, and everything about how the window *looks* (font legible,
colours right, title bar), remains a human check.
