# S-2 — the anchor question

Settles **WIN-4** before WI-15 is written against a guess. Plan section 5, lane C, M0.

**This PR adds two documents and no code.** The plan's bar for S-2 is *"nothing in the
default suite may query the desktop; the spike's conclusions live in the finding"*, so there
is nothing here to import and nothing to run.

## What it found

**The anchor can be read with no permission of any kind, for any application, in about
3 ms.** `CGWindowListCopyWindowInfo` returns every on-screen window front-to-back with owner
and bounds. Cross-checked against `lsappinfo front`, which named the same window.

**Proven on both sides of the permission gate.** The same probe run detached through
`launchctl submit` — so its responsible process is launchd, not Terminal, which is exactly
the case the architect's caution C3 turns on — returned **no window titles at all**
(`name=None`, 3 of 31, so it plainly had no Screen Recording grant) and **identical geometry
to the pixel**. `kCGWindowName` is gated; `kCGWindowBounds` is not.

**The architect's assumption A2 is wrong on its premise.** A2 says reading the frontmost
window of any application needs Accessibility. It does not. And where Accessibility *was*
available, it returned exactly the same numbers as the free route.

**What a refusal looks like, measured without causing one.**
`AEDeterminePermissionToAutomateTarget(..., askUserIfNeeded=False)` reports the current state
and does not prompt: Terminal `0`, Finder `0`, **Chrome `-1744` (would prompt)**, VS Code
`-1744`. Chrome was the frontmost window at that moment, so the AppleScript route to the
real anchor would have raised a dialog. Automation consent is **per target application**, and
the anchor is by definition a different application each time.

## Two defects found in routes the project was about to rely on

1. **Terminal's AppleScript `position` is out by the height of the display**, on any window
   not on the main display — measured across five Terminal windows, all three off-main ones
   out by exactly 1440 px, both on-main ones correct. Its `bounds` property is right. The
   architect's V3 placed a window at "position + (40, 40)"; on this desktop that lands
   1440 px away.
2. **The CoreGraphics route crashed 3 times out of 3 when run inside a live Tk process**, and
   0 times out of 8 outside one. One real signature error was found and fixed along the way
   (`CFPropertyListCreateData`'s `format` is `CFIndex`, not `uint32`), so the fault may be
   mine rather than the platform's — I did not establish which, on the conductor's ruling.
   Either way WI-15 must not read the window list from inside the Tk process.

## Also measured, and it turns out to be unowned

**`root.update()` blocks forever on Tcl/Tk 8.5 under macOS 26, once the window is mapped.**
`Tk()`, `withdraw()`, `geometry()`, `deiconify()` and `update_idletasks()` all return;
`update()` never does, pinned by a `faulthandler` traceback at `tkinter/__init__.py:1314`.

I set it aside as S-1's ground and did not pursue it. S-1 has since merged, and its headless
verdict was measured on a **withdrawn** root, which never reaches this. So it belongs to
nobody yet, and it lands on **WI-5 and WI-6** — the two items that have to drive a *visible*
window.

## What this needs from the user

Plan section 9 item 4 asks what to do about WIN-4 *if the anchor cannot be read without
permission*. It can. So the choice is between routes, not between granting and declining, and
the finding puts it as three options with their costs:

- **A** — CoreGraphics via `ctypes`, read in a short-lived child process before the Tk window
  exists. Grants nothing, prompts never, **meets WIN-4 in general**. My recommendation.
- **B** — AppleScript. An Automation dialog once per application, forever, as focus moves.
- **C** — no anchor; fixed or centred placement. **WIN-4 not met.**

If the user picks A, WI-15 also needs to know whether the conductor's `ctypes` ban covers
shipped product code or only agent probing — as written it says "no agent", and WI-15's
output is not an agent.

## Suite state

```
.venv/bin/python -m pytest -q          →  56 passed, 0 failed, 0 skipped
```

Run from the repository root at 01:43Z, on this branch after `git merge origin/main`
brought in WI-0 and S-1, in a `.venv` built from `/usr/bin/python3` 3.9.6 with pytest 8.4.2.
That is the same 56 `main` carries. **This spike adds no test**, by the plan's own
instruction for S-2: *"nothing in the default suite may query the desktop; the spike's
conclusions live in the finding."* The merge was clean — S-2 touches only `docs/findings/`,
`docs/prs/` and `docs/progress/`, which nobody else wrote to.

`lsappinfo visibleApplicationCount` was 7 before and after the suite run, so the default
suite put no window on the screen.

One thing that should become a test and currently is not: *"nothing in the default suite may
query the desktop"* is written down in plan section 1.6 and nothing re-runs it. **WI-0 or
WI-16 should own a guard for it**, in the same spirit as the layer rule in section 1.3.

## Window hygiene

No Terminal window was created and **no window was closed** — not one `close` command was
issued, all run. The only windows that reached the screen were this spike's own Tk root, in
four attempts, each identified by the process's own object reference and each now dead with
its process. Every probe carried a hard deadline. The desktop was re-checked after every
crash, not just at the end: layer-0 window count back to its pre-spike 7 every time,
`lsappinfo visibleApplicationCount=7` as before, no surviving process. Three crash reports
were written to `~/Library/Logs/DiagnosticReports/`; no crash dialog is on screen now, and
they are not mine to dismiss. The one thing registered on the machine, the launchd job
`s2anchorprobe`, was removed four seconds after it ran.

## Files

| File | |
|---|---|
| `docs/findings/S-2-anchor-window.md` | The finding: the measurements, seven recommendations for WI-15, and section 9 item 4 as a decision the user can make in two minutes |
| `docs/progress/r7-s-2-anchor-window.md` | The progress log for this branch |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
