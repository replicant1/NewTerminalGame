# M0 — DEV-C — completion record

**Developer:** DEV-C · **Iteration:** M0, *the two hard things proved* · **Run:** 6
**Mode:** non-local, real pull requests, developer merges their own.

DEV-C's M0 lane is **WI-3 (days 1–3)** and **WI-4 (day 5)**.
**WI-3 is finished and merged. WI-4 has not been started** — it depends on WI-2 as
well as WI-3, and the conductor is holding it back to dispatch separately. This
record will be added to when it lands.

---

## WI-3 — The window and its event loop · **DONE, MERGED**

| | |
| --- | --- |
| Branch | `r6/wi-3-window-event-loop`, based on `main` @ `1f6ea32` |
| Pull request | [#25](https://github.com/replicant1/NewTerminalGame/pull/25) — **merged** as `1fa9490` |
| Commits | `50565d4`, `54b65eb`, `8fa97ab` |
| PR summary | `docs/prs/PR-WI-3-window-event-loop.md` |
| Finding | `docs/findings/WI-3-tk-window-probe.md` |
| Progress log | `docs/progress/r6-wi-3-window-event-loop.md` |

### What was built

The process's own native window, under the adopted architecture (candidate 2), and
nothing that belongs inside it.

- `terminal_game/shell/toolkit.py` — the seam. An abstract `Toolkit` plus the plain
  values `PixelSize`, `ScreenPosition`, `KeyPress`, `WindowSpec`. Imports no toolkit.
- `terminal_game/shell/tk_toolkit.py` — the only module in the application that names
  the windowing toolkit.
- `terminal_game/shell/cadence.py` — GHOST-1 as two constants: 7 a second, 143 ms.
- `terminal_game/shell/tick_timer.py` — the repeating tick, built from Tk's one-shot
  scheduler.
- `terminal_game/shell/window_owner.py` — creates the window, delivers ticks and keys
  to a collaborator it is given, ends the session once.
- `tests/recording_toolkit.py` — the recording double that keeps the suite
  window-free.
- `tools/probe_tk_window.py` — a bounded, self-quitting probe. **Not part of the
  suite.**

### The state of the test suite as it was left

The pinned command, from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| When | Result |
| --- | --- |
| On the branch, before merging | **54 passed, 0 failed, 0 skipped** |
| On the branch after `git merge origin/main`, confirming what landed | **167 passed, 0 failed, 0 skipped** |

The 167 is the whole tree: WI-3's 54 alongside DEV-B's WI-1 and DEV-A's WI-5, both of
which merged while WI-3 was in flight. **What is on `main` is green.**

**No test in the suite constructs a toolkit window.**

### Windows opened on the user's screen

**Three**, all by `tools/probe_tk_window.py`, each for about a second, each quitting
itself on Tk's own scheduler, each confirmed gone — `pgrep -fl probe_tk_window` empty
afterwards and `window_reaped` true in the probe's own output. None was left behind.

### What is still open

- **Assumption A1 — WIN-3's titlebar has not been looked at by a human.** Tk reports
  the title back as exactly `Terminal Game`, which is strictly more than the architect
  could establish under candidate 1, but that is a string read back from the toolkit
  that set it, not a person seeing a titlebar. The plan asks for the look at WI-4 and
  again at WI-21.
- **WI-4 is not started**, and is held by the conductor pending WI-2.
