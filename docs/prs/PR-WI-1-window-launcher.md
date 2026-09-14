# WI-1 — the window launcher and the desktop automation adapter

**Branch:** `wi-1-window-launcher`, cut from `main` at `d4c1a7f`
**Lane:** DEV-A, iteration M0
**Local mode** — this document stands in for the pull request.
**Suite:** `python3 -m unittest discover` from the repository root — **107 passed, 0 failed, 0 skipped.**

---

## What this is

The only component in the system that touches the desktop. It asks the desktop
for the geometry of the window the player was last looking at *before* creating
anything, opens a new terminal window running a given command, captures that
window's identity at the moment of creation, sets 40 x 30, the title, a black
ground and a fixed-width font on that identity alone, moves it a small fixed
offset down and right of the remembered geometry, and closes that identity once
the window is idle.

Requirements it answers: **WIN-1, WIN-2, WIN-3, WIN-4, WIN-5** (WIN-5 under
assumption A1, and joined to the game by WI-3).

## The shape of it

A new top-level package, `launcher/`. It imports only the standard library, and
imports nothing from `terminalgame/` — DEV-B's package — which is caution C11:
the launcher process shares no code with the game.

| File | What it is |
| --- | --- |
| `launcher/geometry.py` | Pure arithmetic. The offset, the clamp, and the rectangles. No I/O of any kind. |
| `launcher/script.py` | Pure text. The AppleScript each operation would run, as a return value. |
| `launcher/runner.py` | **The seam.** The single place a subprocess is started, always bounded. |
| `launcher/desktop.py` | The adapter: script plus runner, parsing answers back into typed values. |
| `launcher/lifecycle.py` | The policy: the order things must happen in, and what happens when they do not. |
| `launcher/__main__.py` | `python3 -m launcher <command>` — the launcher process end to end. |

## The decision worth arguing with

**The seam a test stands in for is the subprocess runner, not the adapter.**

That puts the *AppleScript source text* in front of the tests. It matters
because caution C1 — "never act on the front window" — is a claim about the
words in a script. A test that watched Python method calls could watch a
perfectly well-behaved adapter emit `close front window` and notice nothing. A
test that reads the script sees it.

So `tests/test_launcher_script.py` asserts, over every builder that acts on the
game's window, that it contains `window id <n>` and contains none of
`front window`, `frontmost window`, `window 1`, `first window`, `last window`,
`custom title is`, `whose name`. A completeness test fails if a new builder is
added to the module without being listed, so the rule cannot be escaped by
writing a sixth function.

## What the tests establish

The plan asks WI-1's tests for five things. Each is a named class in
`tests/test_launcher_lifecycle.py`:

| The plan asks | Where |
| --- | --- |
| the frontmost query is issued **before** creation and never after | `AskBeforeYouCreate` — five tests, including that nothing is sent to the terminal application at all before the creation call |
| every subsequent operation names the captured identity | `EverythingAfterwardsNamesTheCapturedIdentity` — over the real script text, and a test that a different captured id moves every later script with it |
| the offset is applied to the remembered geometry and clamped visible | `WhereTheWindowLands`, plus eleven pure tests in `tests/test_launcher_geometry.py` |
| a failure after creation still closes the captured identity | `WhenSetupFailsAfterTheWindowExists` — a refusal, a timeout and a `KeyboardInterrupt`, at each of the three stages after creation |
| every call has a timeout | `EveryCallIsBounded`, and `WhenItDoesNotComeBack` in `tests/test_launcher_runner.py` |
| one **real** run against the real desktop | `docs/findings/WI-1-terminal-window-automation.md` |

The runner is tested against a **real subprocess** with `/bin/sh -` standing in
for `osascript`, because it takes its script on standard input in exactly the
same way. So the bound is not asserted by inspecting an argument — a hanging
script really is killed, and the file it was appending to really does stop
growing.

## The placement, and the guarantee behind it

Assumption **A4** is pinned here: the offset is **32 points down and 32 right**.

WIN-4 asks that the window "always lands somewhere visible", and the obvious way
to get that — clamp into the screen — does not actually deliver it. The desktop
reports its bounds as the **union of all displays**, measured on this machine as
`-3509, -1440, 1611, 982`, much of which is over no display at all. AppleScript
offers no way to enumerate individual display frames.

So the guarantee comes from somewhere else. The new window's top-left corner is
kept inside the **reference window's own frame**. The reference window is by
definition one the player was just looking at, so every point in it is over a
real display — which means the new window's corner, with its title bar and its
close button, lands somewhere the player can see and reach. The screen clamp is
applied afterwards as a backstop.

In the ordinary case — a reference window bigger than the offset, not jammed
into a corner — the offset is applied unchanged and none of this shows.

## Two places the real desktop disagreed with the code

**macOS constrains a move.** The launcher asked for `Point(-876, -1353)` and the
window landed at `Point(-876, 30)`, because the reference window was on a
display above the main one. `GameWindow.position` is now the value read back
from the desktop and `GameWindow.asked_for` keeps the arithmetic. A launcher
that recorded its own arithmetic would believe something untrue about the
player's desktop, and WI-13 would inherit the lie.

**A window is busy with something that is not the game for a moment after
creation.** The login shell on this machine runs `ssh-add` from its start-up
files; `processes of tab` read `login`, `-zsh`, `ssh-add` for over a second
after `do script` returned. Anything that asks "is it finished?" immediately is
answering about the shell.

## Where C2 and C3 pull against each other

Caution C2 says never close a busy window. Caution C3 says clean up on the
failure path. If setup fails while the game is running, those two want opposite
things.

**C2 wins, and it is deliberate.** The reap waits, bounded — two seconds on the
failure path, because a failure milliseconds after creation means either the
shell has not got going or a player is already playing, and waiting longer
changes neither. If the window is still busy it is **left open**, and the
`LaunchFailed` that comes out names the window id so a person can deal with it.

Closing it anyway would raise the modal sheet, and the sheet blocks every
automation call that follows — including the ones that would have cleaned up.
The cure would be worse than the disease. This is worth WI-13 (DEV-B) looking at
again, and is flagged to the technical lead.

## Assumptions this proceeds on

- **A1** — nothing here depends on it. The launcher closes the window when the
  game process exits; *when* the game decides to exit is WI-11's business.
- **A2** — a refused geometry query degrades: `WhenTheDesktopWillNotSayWhereThePlayerWasLooking`
  covers the reference query refused, the screen query refused, and both. The
  window is still created, still configured and still placed. The permission was
  already granted on this machine, so the refusal path has been exercised
  against a stood-in desktop only, never against a real refusal.
- **A3** — nothing is written to a `settings set`. Every appearance property
  goes to the window's own tab, and a test asserts the string `settings set`
  appears in no script.

## What needs a human

1. **WIN-3, the title.** The launcher sets the custom title to exactly
   `Terminal Game` and turns off every competing component the dictionary
   exposes — but the title bar still reads `rodneybailey — Terminal Game —
   <running command>`, because two components are not scriptable at all and
   belong to the player's saved profile. A3 forbids changing it. Full
   measurements and the exact steps are in
   `docs/findings/WI-1-terminal-title-components.md`. **WIN-3 must not be
   recorded as verified without a person looking at the title bar.**
2. **WIN-2, legibility.** Menlo 14 is fixed-width and ships with macOS; whether
   it is "large enough to read comfortably" is a judgement only a person can
   make.
3. **A2, the permission dialog.** No agent can grant, refuse or confirm the
   macOS Automation / Accessibility permission.
4. **WIN-4 as rendered.** That the window visibly lands below and right of the
   previous one, on a machine with one display and with several.

## Files

```
launcher/__init__.py          launcher/geometry.py    launcher/script.py
launcher/runner.py            launcher/desktop.py     launcher/lifecycle.py
launcher/__main__.py

tests/__init__.py             tests/launcher_fakes.py
tests/test_launcher_geometry.py   tests/test_launcher_script.py
tests/test_launcher_runner.py     tests/test_launcher_desktop.py
tests/test_launcher_lifecycle.py  tests/test_launcher_main.py

docs/findings/WI-1-terminal-window-automation.md
docs/findings/WI-1-terminal-title-components.md
docs/progress/wi-1-window-launcher.md
```

## Agreed with DEV-B

The game package is `terminalgame/`, the launcher package is `launcher/`, and
neither imports the other. Tests live in one top-level `tests/` package with an
**empty** `tests/__init__.py` — which is not optional, because `unittest
discover` on Python 3.9 silently skips a directory that is not an importable
package. The whole-suite command is `python3 -m unittest discover` from the
repository root, which plan §2 asks the two lanes to settle before the first
merge.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
