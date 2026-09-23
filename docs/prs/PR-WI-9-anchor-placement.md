# WI-9: Anchor and placement

Risk: MEDIUM. It reads other windows' positions and computes a point. It opens, sizes, moves and closes nothing (plan floor, not raised). The C6 harness does open one Terminal window of its own, and it closes that window by its id.

**Base:** `b1adc97`, the merge-base with `main`. **Lane C, Dev C.** Needs no human gate: nothing is marked needs eyes, and it is not HIGH.

## What this is

There are two parts, both in the shell (`terminal_game/shell/`).

- **`anchor.py`, the platform queries, both read-only.**
  - `find_anchor()` reads the window server's on-screen window list with `CGWindowListCopyWindowInfo`, called through `ctypes` with no install. The list comes front to back, and the function returns the first ordinary window that is not this process's: layer 0, not transparent, at least 40 × 40. It gives up after 500 ms, and returns `None` if the query fails or there is no such window. It needs no permission. Only window *titles* are withheld without Screen Recording, and it never asks for them. It activates, moves and changes nothing.
  - `visible_displays()` reads each screen's visible area from `NSScreen`, and the pure `to_global()` flips those areas into top-left-origin global points.
- **`placement.py`, the policy, which is pure.** `place(anchor, window_size, displays)` puts the window's outer top-left 40 points below and to the right of the anchor, on the anchor's display, then clamps it just far enough to lie wholly inside that display's visible area. With no anchor, it centres the window on the main display.

Everything is in global screen points, with the origin at the top-left of the main display. That is the space the window list, Tk's `+x+y` and WI-3's `GameWindow.place` all use, so WI-13 can pass the result straight to `place`.

## Claims

Control for every claim: **n/a**. At the base `b1adc97`, neither `terminal_game/shell/anchor.py` nor `terminal_game/shell/placement.py` exists (the shell package holds only `__init__.py`), so no claim has a counterpart to run against. A test overlaid onto the base would fail on `ImportError`, which proves nothing.

`P::<name>` stands for `.venv/bin/python -m pytest -q -v tests/test_placement.py -k <name>`, whose output lists each selected test as PASSED.

| Claim | Claim text (plan, word for word) | Evidence | Output shows | Control |
|---|---|---|---|---|
| **WI-9/C1** | The game window's top-left corner is placed a little below and to the right of the anchor's top-left corner: a fixed offset of between 20 and 60 points in each direction. | Executable: `P::c1_` — `OFFSET` is 40. For three anchors, one of them on a display at negative coordinates, the result minus the anchor's top-left is exactly (40, 40). Also the C6 harness below, on the real desktop: anchor (322, −1367) → placed at (362, −1327). | `test_c1_top_left_goes_a_fixed_offset_below_and_right_of_the_anchor PASSED` | n/a (new module) |
| **WI-9/C2** | If that position would put any part of the game window off the visible screen, the window is moved just far enough to lie wholly on it. | Executable: `P::c2_` — 4 cases (too far right, too far down, both, hanging off the left). Each lands on the edge, exactly at `area.right − width` or `area.bottom − height`, which is not a point further than that edge, and is wholly inside the display's visible area. A fifth case shows a position already on screen is not moved. `P::a2_` shows the visible area leaves out the menu bar on every display. | `5 passed` (4 parametrised + "not moved") | n/a (new module) |
| **WI-9/C3** | If no anchor can be found (no window on screen, or the query fails), the window is placed wholly on the visible screen at a default position, and start-up carries on. | Executable: `P::c3_` — `place(None, …)` is centred wholly on the main display at (556, 206). `find_anchor` returns `None`, and does not raise, for a query that raises `OSError`, for an empty window list, and for a list holding only our own window. | `4 passed` | n/a (new module) |
| **WI-9/C4** | When the anchor is on a second display, the game window lands on that same display, wholly visible. | Executable: `P::c4_` — an anchor on the left display (measured numbers) lands on it. An anchor at a shared edge, whose offset would cross into the neighbouring display, stays on its own display. An anchor whose corner is off every display goes to the one it overlaps most. Also the C6 harness on the real desktop: the Terminal anchor was on display 2, a secondary display at negative y, and the game window is placed at (362, −1327), wholly on display 2. | `3 passed`; harness line `anchor on display 2; game window placed at [362, -1327], wholly on display(s) [2]` | n/a (new module) |
| **WI-9/C5** | Finding the anchor finishes within 500 milliseconds, or gives up and falls back as in C3. | Executable: `P::c5_ -s` — a query that sleeps 3 s is abandoned: `None` in under 0.6 s. The real query answers in well under half the limit (it prints its time). The C6 harness reports the real anchor time from a Terminal window. | `WI-9/C5: real window list: 37 windows in 15.7 ms`, `2 passed`; harness: `found in 25.0 ms` | n/a (new module) |
| **WI-9/C6** | Run from a Terminal window on the real desktop, finding the anchor returns that Terminal window's position and size, matching what Terminal itself reports for its front window. | Executable (a harness that opens one Terminal window): `.venv/bin/python evidence/WI-9/terminal_anchor.py`. It opens one Terminal window (Terminal comes to the front, as it does when a person types a command into it) and runs `evidence/WI-9/report_anchor.py` there. That script calls `find_anchor()`, then asks Terminal `get {id, bounds} of front window`. The harness waits for the process to exit, closes that window by the id it captured, and prints the comparison. Record: `evidence/WI-9/terminal-anchor-0b45a46.json`. | `anchor (x, y, w, h) : [322.0, -1367.0, 597.0, 385.0] … owner {'id': 21243, 'owner': 'Terminal', …}` / `Terminal front window id 21243: bounds {322, -1367, 919, -982} -> (x, y, w, h) [322, -1367, 597, 385]` / `agree: True`; `window 21243 after closing: visible=false` | n/a (new module). The query is not simply returning Terminal: run from this session while Google Chrome was frontmost, it returned the Chrome window (`Rect(-3351, -1398, 2248, 1374)`, progress log line 03:59:18Z). |
| **WI-9/A1** | `place` given no display at all refuses with a `ValueError`, rather than inventing a position. | Executable: `P::a1_` | `1 passed` | n/a (new module) |
| **WI-9/A2** | The visible areas come out in global top-left points, and a secondary display's menu bar is left out even though `NSScreen` reports that display's whole area as visible; a display whose visible area already excludes its top is not trimmed twice. | Executable: `P::a2_` — `to_global` is fed the `NSScreen` numbers measured on this desk and yields exactly main (0, 33, 1512, 949), left (−3509, −1407, 2560, 1407) and middle (−949, −1407, 2560, 1407). | `2 passed` | n/a (new module) |

The rest of `tests/test_placement.py` covers the frontmost-window choice (`test_the_first_ordinary_window_that_is_not_ours_is_the_anchor`: it skips menu-bar items, our own window, invisible windows and slivers) and the real display list (the main display comes first, at x = 0). It serves C3 and C6. The whole file runs in the default suite and opens no window: `.venv/bin/python -m pytest -q tests/test_placement.py` → `20 passed`.

## Diff map

```
terminal_game/shell/placement.py:1-21     -> docstring; OFFSET (C1)
terminal_game/shell/placement.py:23-50    -> Rect and its geometry (C2, C4)
terminal_game/shell/placement.py:52-62    -> display_for (C4)
terminal_game/shell/placement.py:65-75    -> clamp (C2)
terminal_game/shell/placement.py:78-92    -> place (C1, C2, C3, C4); the no-display ValueError (A1)
terminal_game/shell/anchor.py:1-41        -> docstring, ANCHOR_TIMEOUT_S (C5), MIN_SIDE (C6), CG constants
terminal_game/shell/anchor.py:44-125      -> the ctypes window-list query (C5, C6)
terminal_game/shell/anchor.py:128-140     -> frontmost_window (C6, C3)
terminal_game/shell/anchor.py:143-163     -> find_anchor with its timeout and fallback (C5, C3)
terminal_game/shell/anchor.py:169-197     -> visible_displays, the NSScreen query (C2, C4)
terminal_game/shell/anchor.py:200-222     -> to_global (A2, C2, C4)
tests/test_placement.py (new)             -> evidence for C1-C5, A1, A2
evidence/WI-9/terminal_anchor.py, report_anchor.py (new) -> evidence for C6 (and C1, C4, C5 on the real desktop)
evidence/WI-9/terminal-anchor-0b45a46.json -> the C6 record
docs/progress/r8-wi-9-anchor-placement.md, docs/prs/PR-WI-9-anchor-placement.md -> records
```

## For WI-13

```python
from terminal_game.shell.anchor import find_anchor, visible_displays
from terminal_game.shell.placement import place
anchor = find_anchor()                                  # before the game window exists
x, y = place(anchor, (400, 570 + 32), visible_displays())   # outer size: WI-3's size plus a 32-pt title bar (macOS 26, measured)
window.place(x, y)
```

Call `find_anchor()` **before** creating the Tk window. It skips this process's windows anyway, but the query should see the desktop as it was at start-up. If `visible_displays()` returns an empty list, `place` raises (A1). WI-13 decides what start-up does then.

## Findings

- **F1.** `NSScreen` reports a secondary display's visible area as the whole display, even though a menu bar is drawn across its top. Control Centre's items sit at y = −1440 with height 30 on a 2560 × 1440 display whose `visibleFrame` is also 2560 × 1440. So `to_global` takes the main display's menu-bar height off any display that reports nothing taken off its top.
- **F2.** Terminal's AppleScript `bounds` agreed exactly with the window server's bounds, **on a secondary display at negative coordinates** (run 7 had found an AppleScript `position` off by a display height; `bounds` shows no such problem here).

<!-- VERIFIER-STATUS:BEGIN -->
_Awaiting the verifier._
<!-- VERIFIER-STATUS:END -->

🤖 Generated with [Claude Code](https://claude.com/claude-code)
