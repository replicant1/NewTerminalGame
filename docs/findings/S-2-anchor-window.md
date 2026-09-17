# S-2 — the anchor question

**Spike:** S-2, plan section 5, lane C, M0. Settles **WIN-4** before WI-15 is written.
**Measured:** 17 September 2026, 01:34Z – 01:40Z, on the machine this project is being
built on. macOS 26.6.2, `/usr/bin/python3` 3.9.6, Tcl/Tk 8.5.
**Everything below is something that was run.** Where I did not measure a thing, it says so.

---

## The question, and the short answer

> Can a Python process read the position of "whatever window the player was last looking
> at" — and specifically, can the terminal application's own frontmost window be read
> without an Accessibility permission prompt, now that the caller is the game process
> itself rather than a launcher started from the terminal?

**Yes, and better than that: the frontmost window of *any* application can be read, with no
permission of any kind, by any caller, in about 3 milliseconds.** The architect's assumption
**A2 is wrong on its premise** and the measurement that shows it is in the next section.

### The one thing to read before anything else

This spike crashed Python three times. **The crash was not `ctypes` into CoreGraphics. It
was `ctypes` into CoreGraphics *inside a process with a live Tk root*.**

| Context | Runs | Outcome |
|---|---|---|
| plain Python process, no Tk | **8** | **clean every time** |
| process with a live `tkinter.Tk()` root | **3** | **crashed every time** |

That distinction is the whole decision. The recommended option below —
**option A** — is built specifically to avoid the combination: it reads the anchor in a
short-lived child process, **before the Tk window exists**, so the two are never in the same
process at the same time. Section 6 has the three crashes and their exact signatures, and is
honest that one real signature error was found and corrected along the way, so the fault may
be mine rather than the platform's.

The conductor has ruled that no agent may call into Objective-C, AppKit, Quartz or
CoreGraphics through `ctypes`, and that the prohibition holds for shipped code too until the
user rules otherwise. **So the reading is established, and whether the product may use it is
a question for the user, not for me.** Section "What needs the user" puts that in front of
them in two minutes.

---

## What was measured

### 1. The anchor is readable, and it needs no consent

`CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements)`
returns every on-screen window, front-to-back, with owner name, owner pid, window number
and bounds. Called from `/usr/bin/python3` through `ctypes` — no third-party package, and
`/usr/bin/python3` has no pyobjc at all (no `Quartz`, no `AppKit`, no `objc`), so `ctypes`
is the only native route available to it.

| | |
|---|---|
| Windows returned | 31, of which 7 at layer 0 (ordinary application windows) |
| Frontmost layer-0 window | `Google Chrome` pid 34162, origin (−3477, −1389), size 2309 × 1364 |
| Call cost | 12 consecutive calls: **min 3.0 ms, median 3.2 ms, max 23.2 ms** |
| Consent prompts raised | **none** |
| Windows opened | **none** |

**Cross-checked against LaunchServices.** `lsappinfo front` returned `ASN:0x0-0x4f24f2:`,
which `lsappinfo info -only pid,name` resolved to pid 34162, `Google Chrome` — the same
window the window list put first at layer 0. Two independent unprivileged routes agree on
which window is frontmost.

### 2. Geometry is ungated; only the *title* is gated — proven on both sides of the gate

This is the measurement that settles A2, and it took running the probe twice under two
different callers.

| Caller | Responsible process | `CGPreflightScreenCaptureAccess()` | Titles returned | **Geometry returned** |
|---|---|---|---|---|
| child of my shell | Terminal.app (pid 1191) | `True` | 21 of 31 | Terminal (−917, −1388, 1038 × 1295); Chrome (−3477, −1389, 2309 × 1364); Finder; Code |
| `launchctl submit` | launchd — **not** Terminal | not granted | **3 of 31**, `name=None` for every layer-0 window | **identical, to the pixel** |

The second row is the whole finding. Detaching the probe from Terminal through
`launchctl submit` puts it in exactly the situation the architect's caution **C3** turns on
— a caller that was *not* started from the terminal application. Its titles collapsed to
nothing, which proves it had no Screen Recording grant. **Its geometry came back in full
and identical.** No prompt appeared, and the process exited cleanly.

So: `kCGWindowName` is gated behind Screen Recording. `kCGWindowBounds`,
`kCGWindowOwnerName`, `kCGWindowOwnerPID` and `kCGWindowLayer` are not gated at all.
**WIN-4 needs only the bounds.**

The launchd job was named `s2anchorprobe`, submitted at 01:40:06Z and removed at 01:40:10Z;
`launchctl list` shows nothing matching. Nothing was left registered on the machine.

### 3. What a refusal looks like — measured without causing one

`AEDeterminePermissionToAutomateTarget(target, typeWildCard, typeWildCard, askUserIfNeeded=False)`
reports the current Automation state and, with `askUserIfNeeded` false, is documented not to
prompt. It did not.

| Target | OSStatus | Meaning |
|---|---|---|
| `com.apple.Terminal` | `0` | already permitted — no dialog would appear |
| `com.apple.finder` | `0` | already permitted |
| **`com.google.Chrome`** | **`-1744`** | **`errAEEventWouldRequireUserConsent` — would prompt** |
| `com.microsoft.VSCode` | `-1744` | would prompt |
| `com.apple.systemevents` | `-600` | `procNotFound` — not running (a script targeting it would launch it first) |

**Chrome was the frontmost window at that moment.** So the AppleScript route to the *actual*
anchor would have raised a per-application consent dialog, right then, on this desktop. The
architect's V6 ("automation consent is free here") is true only for Terminal, and only
because the caller was Terminal's own descendant. Automation consent is **per target
application**, and the anchor is by definition whichever application the player was last
looking at — so the AppleScript route prompts for each new application in turn, forever.

`AXIsProcessTrusted()` returned **`True`**: Accessibility is already granted to
Terminal.app on this machine. So the Accessibility route would also work here without a
prompt — but only for callers Terminal is responsible for, and only because this particular
user granted it at some point for something else.

### 4. The Accessibility route buys nothing the free route does not already give

Run only because step 3 had already established the process was trusted, so no dialog was
possible. Messaging timeout 2 s.

| Window | Accessibility `AXPosition` / `AXSize` | `CGWindowBounds` |
|---|---|---|
| Chrome `AXFocusedWindow` | (−3477, −1389) 2309 × 1364 | (−3477, −1389) 2309 × 1364 |
| Terminal `AXFocusedWindow` | (−917, −1388) 1038 × 1295 | (−917, −1388) 1038 × 1295 |

**Identical, to the pixel, in both cases.** The privileged route returns exactly what the
unprivileged one does.

### 5. A defect in the route the architect actually used

The architect's V3 says he "placed it at the anchor window's position + (40, 40)". On this
desktop that would be wrong by 1440 pixels.

`tell application "Terminal" to get {id, position, bounds} of every window`, five windows:

| Window id | AppleScript `position` | AppleScript `bounds` (top) | `CGWindowBounds` Y | On |
|---|---|---|---|---|
| 7104 | y = **52** | −1388 | −1388 | secondary display |
| 8007 | y = **36** | −1404 | −1404 | secondary display |
| 2420 | y = **30** | −1410 | — | secondary display |
| 367 | y = 33 | 33 | — | main display |
| 2440 | y = 300 | 300 | — | main display |

Terminal's AppleScript `position` property is **out by exactly the height of the display the
window sits on** (1440 px here) whenever that window is not on the main display. Its
`bounds` property is correct and agrees with CoreGraphics and with Accessibility. The
architect measured on the main display, where the two happen to coincide.

**Nobody should use AppleScript `position` for WIN-4.** If the AppleScript route is used at
all, use `bounds`.

**This defect kills option B on its own merits, independently of the consent dialog.** The
architect's V3 is the only place the AppleScript route has ever been exercised for WIN-4,
and it used `position`. Anyone reaching for option B because the dialog seems tolerable
would be reaching for a measurement that is wrong by a display height on two of this
machine's three screens.

Display layout for context — three active displays, so negative coordinates are normal here:

| Display | Origin | Size | |
|---|---|---|---|
| id 1 | (0, 0) | 1512 × 982 | **main** |
| id 2 | (−3509, −1440) | 2560 × 1440 | |
| id 3 | (−949, −1440) | 2560 × 1440 | |

### 6. The crash, which is the reason this route is now in question

The same `ctypes` code, unchanged:

| Context | Runs | Outcome |
|---|---|---|
| plain Python process, no Tk | 8 | clean every time |
| process with a live `tkinter.Tk()` root | 3 | **crashed every time** |

The three crashes, all from one probe that read the window list from inside a Tk process:

- `01:38:49Z` — `NSInvalidArgumentException`, `-[__NSTaggedDate length]: unrecognized selector`,
  thrown out of `CFPropertyListCreateData` via `libffi` → `_ctypes`. Exit 134.
- `01:39:18Z` — `SIGSEGV`, no output at all. Exit 139.
- `01:39:23Z` — `SIGSEGV`, no output at all. Exit 139.

Three crash reports were written, `Python-2026-09-17-113855.ips`, `-113919.ips` and
`-113924.ips` (local time is UTC+10). **I did not establish whether the fault is in the
declared `ctypes` signatures or in the interaction with AppKit**, and on the conductor's
ruling I did not investigate further. One real signature error was found and corrected
along the way — `CFPropertyListCreateData`'s `format` parameter is `CFPropertyListFormat`,
which is `CFIndex`, a signed long, not a `uint32` — so the fault may well be mine rather
than the platform's. It is recorded here because either way the conclusion is the same:
**reading the window list from inside the Tk process is not a thing to do.**

### 7. A separate Tk finding, which turns out to be unowned

**`root.update()` blocks forever on Tcl/Tk 8.5 under macOS 26, once the window is mapped.**
`tkinter.Tk()`, `withdraw()`, `geometry()`, `deiconify()` and `update_idletasks()` all
return normally; `update()` never does. A `faulthandler` watchdog pinned it at
`tkinter/__init__.py` line 1314, in `update`.

I set this aside as S-1's ground and plan assumption P8. The conductor reports that S-1 has
already finished and merged, and that **its headless verdict was measured on a *withdrawn*
root**, which never reaches this. So this is new and belongs to nobody yet, and it lands on
**WI-5 and WI-6**, which are the items that have to drive a *visible* window. It is
recorded here rather than left in a progress log for that reason.

---

## What WI-15 should do

1. **Do not use AppleScript for the anchor.** It prompts per target application, and the
   anchor is by definition a different application each time. Measured: Chrome `-1744`.
   If it is used anyway, use `bounds` and never `position` — see section 5.
2. **Do not read the window list from inside the Tk process.** Measured: 3 crashes out of
   3. If the CoreGraphics route is permitted at all, read the anchor **before Tk is
   initialised**, or in a short-lived child process, and hand the result in.
3. **Exclude your own pid.** The game's own window is frontmost the instant it appears, so
   filter on `kCGWindowOwnerPID != os.getpid()`, or read the anchor before the window
   exists. Both work; the filter is the robust one.
4. **Take the whole rect, not just the origin**, so the fallback and any future "centre on
   the anchor" behaviour have what they need.
5. **The fallback, when there is no anchor.** `CGDisplayBounds(CGMainDisplayID())` gives
   (0, 0, 1512, 982) here. Centring on the main display is a sane default, and the plan's
   own bar for WI-15 is that a failure to read the anchor "degrades to a sane default
   rather than crashing or prompting".
6. **Coordinate space.** CoreGraphics bounds and Accessibility agree: origin at the top-left
   of the main display, y increasing downward, negative values legal. **Whether Tk's
   `wm geometry +x+y` uses the same space is NOT established** — the probe that would have
   settled it is one of the three that crashed. It is cheap for WI-15 to settle, and note
   that Tk's geometry string has no natural spelling for a negative x: `+-877+-1348` is what
   falls out of naive formatting and it needs checking before it is relied on.
7. **WI-15's tests use a supplied anchor**, per the plan. Nothing here changes that, and
   nothing here belongs in the default suite.

**Nothing in the default suite may query the desktop.** No test was added by this spike;
there is no suite yet (WI-0 is in flight in lane B). That rule is currently written down and
nothing re-runs it — **WI-0 or WI-16 should own a test that pins it**, in the same spirit as
the layer rule in plan section 1.3.

---

## What needs the user — plan section 9, item 4

Item 4 asks: *decide what to do about WIN-4 if the anchor cannot be read without permission.*

**The measurement changes the question.** The anchor **can** be read without permission —
proven above, on both sides of the Screen Recording gate, for any application. What is now
in question is not permission but **technique**: the only route `/usr/bin/python3` has to
CoreGraphics is `ctypes`, it crashed three times inside a Tk process, and the conductor has
ruled `ctypes`-into-Objective-C off limits for agents. So the user is choosing between
routes, not between granting and declining.

Three options, and what each costs:

| | What the game would do | What the user grants | What WIN-4 becomes |
|---|---|---|---|
| **A** | Read `CGWindowListCopyWindowInfo` via `ctypes`, **in a short-lived child process before the Tk window exists** | **nothing at all** — no dialog, ever, for any application | **Fully met, in general.** The window lands below and right of whatever the player was actually looking at, whichever application that was |
| **B** | Ask the frontmost application for its window over AppleScript | A macOS **Automation** dialog — *"Terminal Game wants to control Google Chrome"* — **once per application**, forever, as the player's focus moves | Met, but with a dialog the first time the player has been looking at each new application — **and section 5 kills this option even if the dialogs are tolerated**, because the only property the architect's V3 ever used is wrong by a display height off the main screen |
| **C** | Don't read anything; place the window at a fixed spot, or centred on the main display | nothing | **WIN-4 not met.** The window appears in the same place regardless of what the player was looking at |

**My recommendation is A**, with the child-process isolation in point 2 above, because it is
the only one that meets WIN-4 as written and it is the only one that asks the user for
nothing. **It needs the user's say-so only because of the conductor's `ctypes` ruling, not
because macOS objects.**

Note that plan assumption **P2** ("the anchor is the terminal window the game was started
from") and the architect's **A2** are both superseded by option A: under A the anchor is
genuinely whatever window was frontmost, terminal or not. Under B or C, P2 stands and WI-15
must say so in its PR body, exactly as plan section 5 requires.

**A good answer from the user is one sentence: "use A", "use B", or "use C".** If they pick
A, WI-15 also needs to know whether the `ctypes` ban applies to shipped product code or only
to agent probing — the ruling as written says "no agent", and WI-15's output is not an agent.

---

## Window hygiene, stated for the record

Plan section 1.5 governed this spike. What happened:

- **No Terminal window was created and no window was closed.** Not one `close` command was
  issued to anything, all run. The only AppleScript sent was two read-only `get` calls to
  Terminal, and only after `AEDeterminePermissionToAutomateTarget` had confirmed Terminal
  was already permitted, so no dialog was possible.
- **The only windows that reached the screen were this spike's own Tk root**, in four
  attempts. They were identified by the process's own object reference, which is stricter
  than an id, and every one of those processes is dead. One was visible for about 8 seconds
  at 200 × 120 on the main display; the rest were momentary or never painted.
- **Every probe carried a hard deadline** — `signal.alarm`, `faulthandler.dump_traceback_later(exit=True)`,
  or a `subprocess` timeout. Nothing could block forever, and nothing did.
- **Checked after every crash, not just at the end.** Layer-0 window count returned to its
  pre-spike value of 7 each time, `pgrep` found no surviving process each time, and
  `lsappinfo metainfo` reports `visibleApplicationCount=7`, the same as before the spike
  started. No crash-reporter application is registered as visible.
- **Three crash reports were written to `~/Library/Logs/DiagnosticReports/`.** Whether a
  *dialog* was shown at the time I cannot confirm; none is on screen now. They are not mine
  to dismiss and I did not touch them.
- **The one thing registered on the machine** was the launchd job `s2anchorprobe`, submitted
  01:40:06Z and removed 01:40:10Z.
- Scratch files live in this session's scratchpad under `devc-s2/` and nowhere else.
