# WI-1 — what the terminal application actually does when you automate it

Measured on this machine during WI-1, against the real desktop. Everything here
was run, not reasoned. The numbers are what WI-3, WI-12 and WI-13 will be
building on, and the reason for writing them down is that the spike scripts that
produced them are gone.

Machine: macOS (Darwin 25.6.0), Terminal.app at
`/System/Applications/Utilities/Terminal.app`, Python 3.9.6.

## Reading the scripting dictionary

`sdef(1)` needs Xcode and is not installed here — it fails with
`tool 'sdef' requires Xcode`. The dictionary is readable straight out of the
bundle instead:

```
/System/Applications/Utilities/Terminal.app/Contents/Resources/Terminal.sdef
```

## Which class owns what

This matters because the obvious guesses are wrong.

| Property | Lives on |
| --- | --- |
| `id`, `position`, `size`, `bounds`, `frame`, `visible`, `name` | **window** |
| `number of rows`, `number of columns` | **tab**, not window |
| `custom title`, the `title displays …` switches | **tab**, not window |
| `background color`, `normal text color`, `cursor color` | **tab** |
| `font name`, `font size`, `font antialiasing` | **tab** |
| `busy`, `processes`, `tty` | **tab** |

So everything WIN-2 and WIN-3 ask for is set on `selected tab of window id <n>`,
and only the position and the measurement are set on the window itself.

The same properties also exist on a `settings set`, which is one of the player's
**saved profiles**. Writing there would outlive the game and assumption A3
forbids it. Nothing in `launcher/script.py` mentions `settings set`, and a test
asserts that it does not.

## Capturing the window's identity (caution C1)

`do script` returns a **tab**, and there is no `window of <tab>` property. The
window is found by asking which window contains that exact tab object:

```applescript
set launchedTab to do script "exec <command>"
set launchedWindow to first window whose tabs contains launchedTab
set launchedId to id of launchedWindow
```

**Verified working.** This is identity capture rather than a positional guess:
the tab is the one this very call just created, and both statements are in the
same script, so there is no moment in between at which another window could
become "the newest".

The by-id specifier then works for everything else:

```applescript
tell application "Terminal" to get name of window id 7653
```

**Verified working** for `name`, `position`, `size`, `visible`, `selected tab`
and `close`.

## `exec` is load-bearing

`do script "exec <command>"` rather than `do script "<command>"`. With `exec`
the login shell is replaced by the game, so the tab reports `busy` = false the
moment the game exits. Without it the shell stays alive underneath and the tab
would never be safely closable.

A side measurement worth knowing: the login shell on this machine runs
`ssh-add --apple-use-keychain` from its start-up files, and `processes of tab`
read `login`, `-zsh`, `ssh-add` for over a second after `do script` returned.
So the window is **busy with something that is not the game** for a moment
after creation, and any "is it finished yet?" check that runs immediately would
be answering about the shell.

## The window's real size

40 columns x 30 rows of Menlo 14 measured **357 x 558 points**. A default
80 x 24 window measured 597 x 385. `number of columns` / `number of rows` read
back as 40 and 30 after being set, so curses inside the window should see a
40 x 30 grid.

Because the font changes the pixel size, the launcher configures the window
first and measures it second; a measurement taken before the font was applied
would clamp against the wrong rectangle.

## `set position` is a request, not an instruction

This is the finding most likely to catch someone out.

```
asked for : Point(x=-876, y=-1353)
landed at : Point(x=-876, y=30)
```

The reference window was on a display above the main one. macOS constrains a
window to the screen it is on, so the y was overridden while the x was honoured.
**Always read the position back**; `Desktop.move()` returns where the window
actually went, and `GameWindow` records both that and what was asked for.

## The desktop bounds are the union of the displays

```applescript
tell application "Finder" to get bounds of window of desktop
```

returned `-3509, -1440, 1611, 982` on this machine — a rectangle much of which
is over no display at all. Negative window coordinates are therefore normal
here: a terminal window was measured at `position` = `(-879, 84)`.

Two consequences:

* a clamp that assumes coordinates start at zero would teleport the game window
  onto a different screen;
* clamping into this rectangle is a **backstop, not a guarantee** of visibility.

The guarantee in `launcher/geometry.py` comes from somewhere else: the new
window's corner is kept inside the **reference window's own frame**, and the
reference window is by definition one the player was looking at, so that corner
is over a real display. AppleScript offers no way to enumerate individual
display frames, which is why the union is the best the screen query can do.

## Closing, and checking it went

`close window id <n>` works and, on a window whose process has exited, raises no
sheet.

After the close, `visible of window id <n>` returned **false** — it did *not*
error. A read-only enumeration of Terminal's windows after a run showed the
closed window still listed with `visible=false`. **This is why the check is
`visible` and not `exists`**: `exists` would answer true for a window that is
gone.

## A real end-to-end run

Window id 7671, through `WindowLauncher.open()` and `WindowLauncher.reap()`:

```
reference window        Rect(left=-908, top=-1385, right=102, bottom=-90)
screen                  Rect(left=-3509, top=-1440, right=1611, bottom=982)
measured window size    Size(width=357, height=558)
position asked for      Point(x=-876, y=-1353)
position it landed at   Point(x=-876, y=30)
grid reported back      40x30
background colour       0,0,0
font                    Menlo-Regular 14
reap                    closed=True, "window 7671 closed"
```

Afterwards, exactly one visible Terminal window remained — the user's own
session. Nothing was left on the desktop.

## What was not established

The Automation and Accessibility permissions were already granted on this
machine, so the **refused** path (assumption A2) was exercised only against a
stood-in desktop, never against a real refusal. No agent can grant, revoke or
verify that permission; it is a dialog in front of a person. It is carried as a
human check.
