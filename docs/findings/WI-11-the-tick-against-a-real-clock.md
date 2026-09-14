# WI-11 — the ghost's tick, measured against a real clock

macOS 25.6.0, Python 3.9.6. **No window and no terminal**: the screen is a stub
that sleeps for the timeout it is handed and reports nothing pressed, which is
what a real `read_key` does when the player is not touching the keyboard.

## Why this measurement exists

Every test of the loop in the suite injects a clock. That proves the
*arithmetic* — that the timeout is recomputed, that keys do not postpone the
tick — and it proves nothing about what the machine does with it. An injected
clock cannot show the loop's own work accumulating on each pass and the ghost
sliding slower and slower.

## What was measured

| asked for | elapsed | ticks | ticks/second | frames | reads |
| --- | --- | --- | --- | --- | --- |
| 2.0 s | 2.007 s | 14 | **6.975** | 15 | 15 |
| 4.0 s | 4.011 s | 28 | **6.981** | 29 | 29 |

Target: 7.000 (GHOST-1, "about seven times a second"). The error is under
0.4 %, and it is in the direction of the loop's own overhead, as expected.

**The anti-drift property is visible in the tick counts rather than in the
rate.** Fourteen ticks in two seconds and twenty-eight in four: exactly double,
for exactly double the time. A loop that set its next deadline to *now plus a
tick* would add its own overhead to every interval, and the second run would
show fewer than twice the first. It does not, because the deadline advances by
whole ticks from the schedule (`next_tick += TICK_SECONDS`) and is never
rebased on the present.

**Frames = ticks + 1.** One opening picture — START-5, up before anything is
pressed — and then one redraw per tick, because the ghost moved every tick on
this maze. Nothing is drawn twice, which is SCRN-7's half of this item.

## What it does not show

The rate under load, on another machine, or with a player actually typing. The
first two are properties of the machine rather than of the loop; the third is
covered in the suite, where a run with fifty keys and a run with none produce
the same number of ticks.

It also says nothing about how the picture *looks*. That needs a person, and it
belongs to WI-12 and WI-14b.

## How to run it again

The script is not kept in the tree — it is eleven lines of stub screen around
`terminalgame.application.loop.play`, with `time.monotonic` left as the default
clock and a counting wrapper around `ghost_move`. Anyone repeating it should
watch the **ratio of the two tick counts** rather than the rate, because that is
the part that catches drift and the rate alone does not.
