# WI-1 — WIN-3 cannot be met exactly by automation alone

**The claim:** the launcher sets the window's custom title to exactly
`Terminal Game`, and turns off every competing title component the scripting
dictionary exposes — but on this machine the title bar still reads

```
rodneybailey — Terminal Game — sleep 0.1
```

because two of the components are not in the dictionary at all and are governed
by the player's saved Terminal profile, which assumption A3 forbids changing.

This is a measurement, not an opinion, and it changes what WIN-3 can honestly be
recorded as.

## What was measured

Three probes, each opening one window, reading the title, and reaping the window
afterwards.

**Probe A — every scriptable switch off, including the custom title.** The tab's
five `title displays …` switches were all set false and read back false:

```
readback custom=false device=false shellpath=false winsize=false filename=false
name = "rodneybailey — sleep 6"
```

So `rodneybailey` and `sleep 6` are produced by something that is not any of the
five.

**Probe B — the custom title turned on as well.**

```
name = "rodneybailey — Terminal Game — sleep 6"
```

The custom title takes its place in the middle of a list; it does not replace
the list.

**Probe C — the same window once its command had exited.**

```
name = "rodneybailey — Terminal Game"     (busy = false, processes = {})
```

The running-process component disappears when nothing is running. The other one
does not.

## What the two residual components are

The tab class in `Terminal.sdef` exposes exactly five title switches:

```
title displays device name      (TTY name)
title displays shell path
title displays window size      (dimensions)
title displays file name        (working directory or document)
title displays custom title
```

Terminal's own Inspector offers more than five, and the two that are missing are
the ones showing up:

* **the active process name and its arguments** — `sleep 6`, `demo_game.sh`,
  and during a real game it would be whatever the game executable is called;
* **the working directory the login shell publishes** — rendered as
  `rodneybailey`, which is how the home folder's display name comes out.

Neither is reachable from AppleScript. Both are controlled by the settings set
(profile) the window inherits, and writing to a settings set would change a
saved preference of the player's that outlives the game — which assumption A3
rules out, and which is not something an agent should be doing to somebody's
machine in any case.

## What the launcher does about it

`launcher/script.py` sets:

```applescript
set custom title of gameTab to "Terminal Game"
set title displays custom title of gameTab to true
set title displays device name of gameTab to false
set title displays shell path of gameTab to false
set title displays window size of gameTab to false
set title displays file name of gameTab to false
```

— which is everything available, and is asserted by tests in
`tests/test_launcher_script.py`. The residue is out of the launcher's reach.

## What this means for WIN-3

**WIN-3 should not be recorded as "verified" on the strength of the launcher's
code.** What can be verified is that the window's custom title is exactly
`Terminal Game`. Whether the title bar *reads* `Terminal Game` depends on the
player's saved profile and can only be confirmed by a person looking at it.

This belongs in WI-14a's human-check list. The exact steps:

1. Run the launcher against the game.
2. Look at the new window's title bar.
3. If it reads anything other than `Terminal Game`, the extra text is the
   profile's doing. Terminal ▸ Settings ▸ Profiles ▸ *(the default profile)* ▸
   Window ▸ Title has the checkboxes; clearing everything except **Custom
   title** makes the title read exactly `Terminal Game`.

Step 3 is a change to the player's saved preferences. **It is the player's
choice, not the game's**, which is exactly why the launcher does not make it.

## The alternative that was considered and not taken

The game process could emit the OSC title escape sequence for itself. That was
rejected on caution C11: only the launcher touches the desktop, and the moment
two components own the window's title the failure modes multiply. It would not
have helped anyway — the escape sequence sets the same `custom title` the
launcher already sets, and the profile's extra components would still be
appended to it.
