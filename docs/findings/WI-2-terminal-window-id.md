# WI-2 — driving Terminal.app: what worked, what did not, and the exact text

Every line below was executed against Terminal.app on this machine
(macOS 26.6.2, Darwin 25.6.0, arm64) between 00:50 and 01:10 UTC on
2026-09-11, in windows this work item created and closed by id. Three displays
were attached. **WI-8 and WI-10 will need this; the PR summary will not be read
again.**

Terminal's visible windows were `[367, 2486]` before the first probe and
`[367, 2486]` after the last.

---

## 1. The WIN-3 title recipe reproduces, exactly as the architect measured it

```
window name: 'Terminal Game'
```

Read back with `name of (first window whose id is N)` one second after the
window was created. All three parts of the recipe are needed and all three are
now pinned by tests:

| Part | What pins it |
|---|---|
| the child is named literally `Terminal Game` and is launched `do script "exec '<repo>/Terminal Game'"` with no arguments | `tests/test_executables.py`, `tests/test_window_geometry.py::ChildCommandTest` |
| the child's first write is `\033]7;\007` | `tests/test_executables.py` |
| every scriptable title component set false, `title displays custom title` included | `tests/test_window_script.py::SettingsTest` |

**Not tried, deliberately:** `title displays custom title = true`. The
architect measured that it produces `Terminal Game — Terminal Game`, and
reproducing a known-bad title on the user's screen buys nothing.

## 2. WIN-2 reproduces

```
tab: 40x30 | font Menlo-Regular 18 | busy false
child reports size: '|         40 columns x 30 rows         |'
```

The second line is the child's own `os.get_terminal_size()`, painted into the
window and read back out of `contents of tab 1` — i.e. the game process really
does see 40 × 30, which is the same fact `stty size` reports. Whether 18 pt is
comfortable to read is **human check H4** and no agent can answer it.

## 3. `busy of tab 1` does NOT mean "the game is running" — WIN-5

**This contradicts ARCHITECTURE.md §6.3**, which prescribes polling `busy`
until false and closing then, and reports that poll going `true, true, true,
false`.

Measured, polling every ~0.11 s from the moment `do script` returned:

```
   0.138  opened 3933
   0.255  busy=true  visible=true nprocs=3      <- the shell being replaced
   0.363  busy=true  visible=true nprocs=3
   0.472  busy=true  visible=true nprocs=2
   0.580  busy=false visible=true nprocs=2      <- the game is painting and
   1.447  busy=false visible=true nprocs=2         waiting for a keypress
   1.447  --- q typed into the tab ---
   1.638  busy=false visible=true nprocs=0      <- the child has exited
   2.750  closed: True
   2.831  after close: visible=False
```

`busy` is **false for the whole of a running game**. Polling it as prescribed
closes the window about a second after opening it: the game would flash and
vanish.

It is not `exec` that does it. Same window, three commands:

| command | `processes of tab 1` | `busy` |
|---|---|---|
| `exec '<repo>/Terminal Game'` | `login, Python` | **false** |
| `exec /bin/sleep 4` | `login, sleep` | true |
| `/bin/sleep 4` | `login, -zsh, sleep` | true |

The difference is that the game spends its life blocked reading the tty, and
Terminal does not count that as busy — which is also why it does not raise its
confirmation sheet when such a window is closed.

**What this project does instead:** the game is running while
`busy or (count of processes of tab 1) > 0`, and the close is guarded by
**both** halves — no processes means the game has really ended, and `busy`
false is what keeps Terminal's modal sheet away, since `busy` *is* briefly true
while the exec happens.

## 4. AppleScript and CoreGraphics do not share a coordinate space — WIN-4

Writing a position to a window of our own, then reading that same window's
frame out of `CGWindowListCopyWindowInfo`:

| written via AppleScript | CoreGraphics reports |
|---|---|
| `(600, 300)` | `(600, -1140, 477, 707)` |
| `(-898, 76)` | `(-898, -1364, 477, 707)` |
| `(-3000, -1000)` | `(-3000, -1410, 477, 707)`, and AppleScript read the position back as `-3000 30` |

A constant offset of **1440 in y** and **none in x**. AppleScript's origin is
the top of the *topmost* display; CoreGraphics' is the top of the *main* one,
and here the topmost display sits 1440 px above the main one.

`CGGetActiveDisplayList` + `CGDisplayBounds` on this machine:

```
main 1
1 (0.0, 0.0, 1512.0, 982.0)
2 (-3509.0, -1440.0, 2560.0, 1440.0)
3 (-949.0, -1440.0, 2560.0, 1440.0)
```

Why it matters: the reference window reported `(-898, 76)`. Read as
CoreGraphics coordinates that point is on **no display at all**, so the clamp
moved the game window to the main display — a screen the player was not
looking at. Converted into AppleScript's space the same point is on display 3,
and the game window lands at `(-868, 106)`, which is exactly reference + 30.

**Also measured:** AppleScript refuses to place a window above `y = 30` and
clamps the write **silently** — `(-3000, -1000)` read back as `(-3000, 30)`.

## 5. `front window` can answer with a window the player cannot see

`position of front window` returned `(-898, 76)` while Terminal's *visible*
windows were `[367, 2486]`. Terminal's window list is front-to-back and
includes windows that are not visible. The reference query now walks the list
and takes the first `visible` one.

## 6. A closed window stays in `windows` — use `visible`, not `exists`

Three probe runs left ids `3924`, `3927` and `3930` in `id of every window`
after those windows had been closed. Only `visible` goes false. Any
before/after census must therefore count **visible** windows or it will never
match itself.

## 7. Exact error text for a window id that is gone

Useful for WI-8: every script that addresses `first window whose id is N`
fails like this when there is no such window, and `run_osascript` raises
`WindowError` carrying the text verbatim.

```
osascript failed (1): 36:40: execution error: Terminal got an error:
Can’t get window 1 whose id = 999999. Invalid index. (-1719)
```

The exception to that is `script_window_visible`, which wraps the read in
`try … on error` and answers `gone`, so liveness can always be asked safely.

## 8. Things deliberately NOT tried on the user's machine

- **Closing a busy tab.** It raises a modal sheet only a human can dismiss and
  that sheet blocks every later AppleScript call in the system. There is no
  safe way to measure it and no reason to.
- **`tell application "Finder" to get bounds of window of desktop`**, and the
  System Events equivalents, to find the screen size. Both can raise a TCC
  automation prompt on the player's screen for an application this project
  otherwise never touches. CoreGraphics through `ctypes` needs no permission
  and was used instead.
- **Any per-profile or global Terminal preference.** Nothing here changes a
  setting outside the tab of the window it created.

## 9. The end-to-end run of `./play`

The window id below came from `play`'s own report on stderr — the id it
captured when it created the window — not from enumerating windows.

```
   0.132  visible before: [367, 2486]
   1.062  play said: 'play: game window 3984 at (-868, 106) (reference (-898, 76) from front)'
   3.227  name: 'Terminal Game' ; visible: True ; play alive: True
   3.303  typed q
   3.544  play exited with 0
   3.628  visible: False
   3.824  visible after: [367, 2486] ; unchanged: True
```

`q` to the window gone: **0.24 s**. Note that `q` was typed by AppleScript
because no agent here has a controlling tty; a person pressing the key is
**human check H2**.
