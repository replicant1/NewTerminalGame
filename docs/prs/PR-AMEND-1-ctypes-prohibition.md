# PR-AMEND-1 — no Objective-C through `ctypes`, plus the first round of rulings

Amendment 1 to `docs/IMPLEMENTATION_PLAN.md`. No code, no tests, **no schedule change**:
the 23 work items, the five iterations, the 41 developer-days and every gantt boundary
are exactly as they were. What changes is a technique that is now off limits, two
assumptions retired by measurement, two more that arrive, five deviation rulings, an
ownerless toolkit defect given an owner, and the answer to a problem every developer
meets at their first merge.

Everything here arrived before amendment 1 was pushed, so it lands as one amendment
rather than two. That is not batching to save a landing — the landing had not happened.

## Why

Three identical *"Python quit unexpectedly"* crash dialogs appeared on the user's screen
at 01:38:55Z, 01:39:19Z and 01:39:24Z on 17 September 2026:

```
EXC_BAD_ACCESS (SIGSEGV)
objc_msgSend <- libffi <- _ctypes <- Python
```

The source was S-2's first probe route, reading the window list through Quartz via
`ctypes`. The conductor stopped the probe and confirmed at 01:40:38Z and 01:40:50Z that
nothing was orphaned and no modal sheet is blocking AppleScript.

**A segfaulted process runs no `finally` block.** Every window-hygiene protection in the
plan — reap on the failure path, confirm the child is dead before closing, verify with
`visible` — is bypassed at once by a crash. Nothing was left behind this time and only
luck decided that.

## What changed

**Section 1.5, renamed "What you may do to the user's machine".** It now opens with the
prohibition and keeps the window rules underneath it, because 1.5 is where a developer
reads what they may do to somebody's desktop and it previously said nothing about
crashing the interpreter.

> No agent may call into Objective-C, AppKit, Quartz or CoreGraphics through `ctypes` —
> not in a probe, a spike, a test or the application. This is a technique that is off
> limits, not a defect to be fixed and retried. If a question can only be answered that
> way, it is a question for the user, not a probe.

The permitted routes are named — `/usr/bin/lsappinfo`, AppleScript to an application
already permitted, and consent checks known not to prompt — together with the consent
state measured at 01:36:41Z without prompting anyone: Terminal and Finder permitted;
Chrome and VS Code **would prompt**; System Events not running.

**The evidence is recorded at its actual width, not broader.** S-2 found the same
CoreGraphics call ran clean **8 of 8** in a plain process and crashed **3 of 3** inside a
process with a live Tk root: it is the Tk-plus-`ctypes` combination that is lethal, not
the call alone. That does not narrow the prohibition — which is the user's to decide and
has been put to them — because a rule that depends on correctly predicting whether a Tk
root is live somewhere in the process is not a rule anyone can follow. But a finding
should say what was seen.

**S-2** loses the prohibited route and is told not to re-derive what the ruling already
settles. Its remaining job is the started-from-a-terminal fallback.

**WI-15** is rewritten against the permitted routes. Its test already asserted against a
*supplied* anchor position rather than the real desktop; that was right and is now
mandatory. WIN-4's general case is explicitly not WI-15's to solve.

**Assumption P2 is promoted** from "the way we are proceeding" to how WIN-4 is actually
built, pending the user. **Human item 4 becomes the live decision** rather than a
contingency: grant the permission, or accept that WIN-4 holds only when the game is
started from a terminal window.

## What S-1 settled, which is good news

**Assumption P8 is closed favourably.** Measured 01:37:42Z: `Tk()` then `withdraw()` gives
`state=withdrawn`, `ismapped=False`, `viewable=False`, with the frontmost application
unchanged. The Presentation layer is testable headlessly on Tcl/Tk 8.5.
**Human item 5 — consent to install a modern Tk — is closed. Nothing needs installing.**

**Assumption P4 is retired by measurement instead of by eye.** **Menlo 16, cell 10 × 19,
window 400 × 570 for 40 × 30.** Of 180 families only Menlo owns every glyph the game draws
with no substitution, and a 40-character row equals 40 × advance only at sizes 8–16. The
font is now fixed in section 1.2 and named in WI-5 and WI-6. Human item 3 survives,
because only a person can say whether 16 point is *comfortable*.

## Two new questions for the user, and the assumptions covering them

**Human item 7 / assumption P9 — the Dock tile.** A withdrawn Tk root still registers with
Launch Services as a foreground process, so a "Python" tile appears for the duration of
every suite run. Not a window, so the bar in section 1.6 holds, but a visible effect
nobody anticipated. We proceed on "acceptable"; if the user says no, WI-5 and WI-16 each
need a default-excluding marker, which costs the headlessness those tests were pinning.

**Human item 8 / assumption P10 — does Menlo's box-drawing ink span the cell?** S-1 could
measure advance but not ink: Tk 8.5 has no canvas-to-image path and this interpreter has
neither PyObjC nor PIL, so no agent here can capture the pixels. SCRN-3 says the walls
"join up neatly", so this is a requirement nobody can verify without eyes. **WI-7's window
is the first sight of it** and WI-7 is now asked to report an impression; WI-17 puts it
formally to the user.

## A measured Tk defect, which had no owner

S-2 bisected it with `faulthandler` and rightly declined to chase it, since it is not
S-2's question — and S-1 had already merged, so nobody held it.

> **`root.update()` never returns on Tcl/Tk 8.5 under macOS 26 once the window is
> mapped.** `Tk()`, `withdraw`, `geometry`, `deiconify` and `update_idletasks()` all
> return; `update()` hangs at `tkinter/__init__.py` line 1314, and a watchdog killed it
> after eight seconds with a 200 × 120 window visible at +300+300.

SCRN-7's "compose off-screen and present once" is precisely the operation that reaches
for `update()`, so this is now written into **WI-5's** bar — do not call `update()` on a
mapped window; `update_idletasks()` returns and the toolkit's own event loop drives
presentation — and **WI-6** inherits it as the item that maps the window. **S-1's headless
verdict is not contradicted**: it was measured on a withdrawn root, which never reaches
that path.

## AppleScript `position` is wrong, and it is the route the architect used

S-2 measured `position` disagreeing with the same window's `bounds` by exactly the display
height on three secondary-display windows — 7104 `y=52` vs `-1388`, 8007 `36` vs `-1404`,
2420 `30` vs `-1410`, all off by +1440 — while two windows on the main display agreed
exactly. **The architect's V3 placed a window at "position + (40, 40)"; on this desktop
that is 1440 pixels wrong.** WI-15 is told to use `bounds`, and told that the global
coordinate space has negative origins: three displays at (0, 0) 1512 × 982, (−3509,
−1440) and (−949, −1440). Assumption P3's +40/+40 survives as an *offset*; what it was
added to did not.

## Five WI-0 deviations, ruled on

1. **A root `README.md`** — no ruling needed. Section 1.7 now says plainly that the four
   document shapes govern the documents the *process* produces, not the source tree;
   section 1.8 already left the tree to the developers.
2. **`tools/` as a fifth top-level directory** — no ruling needed, same reason. The
   reasoning is recorded because it is right: a layer checker inside the package it scans
   must exempt itself, and an exemption is the first hole anyone uses.
3. **The `needs_window` marker, excluded by default** — **adopted** and named in section
   1.6 as the one mechanism, so S-1, WI-5 and WI-16 do not invent three. Section 1.6
   required the exclusion and said nothing about who built it; that was my omission.
4. **`unplaced-module`** — **upheld and promoted into section 1.3 as plan text.** Without
   it the layer rule is dodged by putting a module one level up, so it is the rule rather
   than an addition to it. The layer rule is one of the few structural things the plan
   owns, which is why this one is mine rather than a matter of layout.
5. **"Application imports Domain only" means *of the four layers*** — **confirmed**, and
   the sentence is rewritten so nobody has to read it twice. The pure standard library is
   free everywhere; what each layer may not touch is now named explicitly.

## The log-tail problem, settled once

Section 8 steps 4 and 6 cannot both be satisfied from one branch: the `MERGE` line and its
count only exist *after* the merge, by which point the branch carrying the log is already
merged. Rather than let five developers invent five answers:

- Land the item with its log as complete as it can be, and merge.
- Write the `MERGE` line the moment you have the count.
- **Carry the tail forward on the next branch you cut** — two lines in a file nobody else
  touches, and no extra pull request.
- **Only if you have no next branch**, use `r7/<item>-completion-record`, which is what
  lane B did for WI-0.

And the case S-1 hit from the other side: **an item that legitimately precedes the suite
reports what is true.** S-1's honest `0 passed, 0 failed, 0 skipped` was right; the plan
now says to report the real counts at the time and re-run once a suite exists. Never
round `0 passed` up to "green".

## Checks

Re-ran the consistency checker against the amended document: 23 bars and 5 milestones;
every iteration's bar durations sum to its table total (9, 10, 11, 8, 3 = 41); every
milestone date equals the table's end date; the lane table matches the chart's lane tags;
23 graph nodes = 23 bars = 23 section-5 headings; all 49 requirement codes present in the
trace table. No lane does two items at once and no item starts before a dependency ends,
WI-16's declared stack excepted.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
