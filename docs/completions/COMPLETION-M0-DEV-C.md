# M0 — developer C — completion record

**Iteration:** M0, *Ground to stand on*.
**Lane:** C. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-a319e57ac3a444133`.
**Recorded** 17 Sep 2026, 01:44Z.

## What was finished

**S-2 — the anchor question.** Lane C's other M0 item, **WI-5 (the character grid
surface)**, has not been dispatched to me and is not covered here; the plan allows one
completion record per lane per iteration, so this document should be extended in WI-5's own
pull request rather than duplicated.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#76](https://github.com/replicant1/NewTerminalGame/pull/76) | S-2: the anchor question | `main` | `77c422e` |

Merged by me. Branch `r7/s-2-anchor-window`, cut from `main` at `4015c96`, then merged with
`origin/main` at `c76bc37` before being marked ready. No conflicts — S-2 touches only
`docs/`.

**Files added:**

- `docs/findings/S-2-anchor-window.md` — the verdict, six measurement sections, seven
  instructions for WI-15, and plan section 9 item 4 posed as a three-option choice.
- `docs/prs/PR-S-2-anchor-window.md`.
- `docs/progress/r7-s-2-anchor-window.md`.

No code and no test, by the plan's own bar for S-2: *"nothing in the default suite may query
the desktop; the spike's conclusions live in the finding."*

## The verdict

> **The anchor can be read with no permission of any kind, for any application, in about
> 3 ms** — `CGWindowListCopyWindowInfo` returns every on-screen window front-to-back with
> owner and bounds. **The architect's assumption A2 is wrong on its premise.**

Proven on both sides of the permission gate. The same probe run detached through
`launchctl submit`, so its responsible process is launchd rather than Terminal — the case
caution C3 turns on — returned **no window titles** (`name=None`, 3 of 31) and **identical
geometry to the pixel**. `kCGWindowName` is gated behind Screen Recording; `kCGWindowBounds`
is not, and WIN-4 needs only the bounds.

## The caveat that decides what happens next

**The crash was not `ctypes` into CoreGraphics. It was `ctypes` into CoreGraphics inside a
process with a live Tk root.**

| Context | Runs | Outcome |
|---|---|---|
| plain Python process, no Tk | 8 | clean every time |
| process with a live `tkinter.Tk()` root | 3 | crashed every time |

Three crash reports were written. The conductor has ruled `ctypes` into
Objective-C/AppKit/Quartz/CoreGraphics off limits for agents, and — pending the user's
answer — for shipped code too. So **WI-15 implements nothing until the user chooses**, and
the finding poses the choice as three options: **A** CoreGraphics in a short-lived child
process before Tk exists (meets WIN-4 in general, grants nothing — my recommendation),
**B** AppleScript (a dialog per application, and defeated anyway by the defect below),
**C** no anchor (WIN-4 not met).

## Two defects found in routes the project was about to rely on

1. **Terminal's AppleScript `position` is out by the height of the display** on any window
   not on the main one — five Terminal windows measured, all three off-main out by exactly
   1440 px, both on-main correct. Its `bounds` is right. The architect's V3 placed a window
   at "position + (40, 40)"; on this desktop that lands 1440 px away. This kills option B on
   its own merits, independently of the consent dialog.
2. **The CoreGraphics route crashed 3 of 3 inside a live Tk process**, 0 of 8 outside one.
   One real signature error was found and corrected along the way
   (`CFPropertyListCreateData`'s `format` is `CFIndex`, not `uint32`), so the fault may be
   mine rather than the platform's; I did not establish which, on the conductor's ruling.

## One measurement that belongs to nobody yet

**`root.update()` blocks forever on Tcl/Tk 8.5 under macOS 26 once the window is mapped.**
`Tk()`, `withdraw()`, `geometry()`, `deiconify()` and `update_idletasks()` all return;
`update()` never does, pinned by a `faulthandler` traceback at `tkinter/__init__.py:1314`.

This does not contradict S-1. S-1's headless verdict measured `update_idletasks()` and
`update()` on a **withdrawn** root, which never maps and never reaches this. Mine is the
untested half: a root that has been `deiconify()`'d. It lands on **WI-5 and WI-6**, the two
items that have to drive a *visible* window.

## Suite state

```
.venv/bin/python -m pytest -q          →  56 passed, 0 failed, 0 skipped
```

Run from the repository root, in a `.venv` built from `/usr/bin/python3` 3.9.6 with pytest
8.4.2, three times:

| When | Head | Result |
|---|---|---|
| 01:43:11Z, before marking ready | branch merged with `origin/main` `c76bc37` | 56 passed, 0 failed, 0 skipped |
| 01:43:51Z, immediately before merging | same | 56 passed, 0 failed, 0 skipped |
| **01:44:20Z, after PR #76 landed** | **`77c422e`, `main` with S-2 in it** | **56 passed, 0 failed, 0 skipped** |

S-2 adds no test, so 56 is the count `main` already carried. `lsappinfo
visibleApplicationCount` was 7 before and after every run: the default suite puts no window
on the screen.

## Window hygiene

No Terminal window was created and **no window was closed** — not one `close` command was
issued, all run. The only windows that reached the screen were this spike's own Tk root, in
four attempts, each identified by the process's own object reference and each now dead with
its process. Every probe carried a hard deadline (`signal.alarm`,
`faulthandler.dump_traceback_later(exit=True)`, or a `subprocess` timeout). The desktop was
re-checked after every crash rather than only at the end: layer-0 window count back to its
pre-spike 7 each time, no surviving process each time. The launchd job `s2anchorprobe` was
submitted at 01:40:06Z and removed at 01:40:10Z. Three crash reports sit in
`~/Library/Logs/DiagnosticReports/`; no crash dialog is on screen, and they are not mine to
dismiss.
