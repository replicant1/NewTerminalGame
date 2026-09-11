# WI-8 — every timeout in the launcher, and the number behind it

Written because WI-8's brief says *"Make the timeout a named constant and say
in the PR summary what you set it to and why"*, and because a PR summary is
not read again. All five constants live in `termgame/window.py`.

Nothing here is a new measurement of Terminal's behaviour — WI-2 did that work
and `docs/findings/WI-2-terminal-window-id.md` is still the source. This is
the arithmetic that turns WI-2's numbers into the constants, so that the next
person to change one of them knows what they are trading away.

---

## The two measurements everything is derived from

Both are WI-2's, §3 of its findings, and both were re-observed across four
live `./launch-smoke` runs on 2026-09-11 between 02:06 and 02:21 UTC:

| Transition | Measured |
|---|---|
| `do script` returns → the tab holds the child's processes | **0.25 s** |
| the child exits → the tab holds none | **0.19 s** |

Everything below is a multiple of the larger of those.

---

## `CLOSE_GRACE_SECONDS = 10.0` — the one the brief asked about

**What it is.** How long the supervisor waits, *on the failure path only*, for
the child to exit before it gives up, reports the window id, and leaves the
window open rather than forcing a close on a busy tab.

**Why ten.** Forty times the larger measured transition. That margin matters
in one direction and one only: the failure it must never produce is *giving up
on a window whose child was about to be reaped anyway*, because the result of
that is a window left on the player's screen for no reason. Forty times the
worst observed transition cannot be tripped by AppleScript latency, by machine
load, or by a slow login shell — and the login shell *is* slow here; see
`WI-8-title-settling-race.md`.

**Why not more.** The other end of the trade is a person who has just been
shown an error staring at a `./play` that appears to have hung. Ten seconds is
about the longest that reads as "it is trying" rather than "it is stuck".

**Why not less.** Five would still be twenty times the measurement, and would
probably be fine. Ten was chosen because the cost of being wrong is asymmetric:
too short leaves a window behind on somebody's desktop, too long delays a
message. A window is worse than a message.

**What happens when it expires.** The window is **left open** and its id is
printed. This is deliberate and it is §2.6 rule 3: a busy tab closed by script
raises Terminal's modal confirmation sheet, which only a human can dismiss and
which blocks every subsequent AppleScript call in the system. One window the
player can close themselves is strictly better than a dialog nobody is
watching.

**It is observed, not asserted about.** `window._sleep` and `window._now` are
module-level indirections so a test can watch the full ten seconds elapse
against a fake clock in a few milliseconds
(`tests/test_window_failure_paths.py::TheChildHangs`). A test that only
compared the constant to `10.0` would pass on a launcher that never waited.

**`launch-smoke` uses the same number**, deliberately: `CLEANUP_SECONDS is
window.CLOSE_GRACE_SECONDS`. The smoke should be neither more patient nor more
forceful than the launcher it is smoking, and a test pins that.

---

## `STARTUP_GRACE_SECONDS = 2.0`

How long an empty tab is *not* yet read as "the game has ended". Eight times
the 0.25 s gap between `do script` returning and the child's processes
appearing. Without it the supervisor reads the momentarily-empty tab as a
finished game and closes the window on a game that has not painted yet.

It applies only until the game has been *seen* running once; after that an
empty tab means the child has gone. That is what lets a child which crashes on
startup still be waited on and still have its window closed.

---

## `POLL_SECONDS = 0.2`

How often Terminal is asked whether the game is still running. WI-2 measured
`q` to window-gone at **0.24 s** with this poll, which is below the threshold
at which a person notices a delay. Each poll is one `osascript` round trip, so
this is also the floor on how much work the supervisor does while somebody
plays: five round trips a second, each trivial.

---

## `OSASCRIPT_TIMEOUT_SECONDS = 20.0`

How long any single AppleScript is given before `run_osascript` raises. This
one is not a performance number at all — it is the **modal sheet detector**. A
sheet on any Terminal window blocks every AppleScript call in the system, and
without this constant the supervisor would simply never return and the person
running it would read that as a crash. With it, they get a message that names
the actual cause:

```
osascript timed out after 20.0s. A modal sheet on a Terminal window blocks
every AppleScript call; check the screen.
```

Twenty seconds is far longer than any script here needs (all are milliseconds)
and short enough to diagnose. No AppleScript on this branch has ever come
close to it.

---

## `INTERRUPTED_EXIT_STATUS = 130`

Not a timeout; recorded here because it is the fifth constant. 128 + SIGINT,
the shell convention, returned when a signal ended the game rather than the
player.

---

## What a later work item would have to re-measure

If the child ever becomes something that can take a long time to *exit* —
writing a save file, say — then `CLOSE_GRACE_SECONDS` is the constant that has
to grow, and the 0.19 s measurement it rests on is the one that has stopped
being true. Nothing else here depends on what the game does.
