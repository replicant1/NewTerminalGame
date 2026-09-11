# WI-8 — two things WI-2's measurements could not have shown, and the census

Measured against Terminal.app on this machine (macOS 26.6.2, Darwin 25.6.0,
arm64) on 2026-09-11 between 02:06 and 02:21 UTC, across **six** live window
openings in three runs of `./launch-smoke --repeat 2`. Every window was created
by this work item and closed by the id captured at creation.

Terminal's visible windows were `[367, 2486]` before the first run and
`[367, 2486]` after the last — the same set WI-2 and WI-4 measured and left
unchanged.

**Both findings below contradict nothing WI-2 wrote.** They are things WI-2
could not have seen, because of *when* it looked.

---

## 1. The window title is wrong for the first half-second, and it is not WIN-3's fault

The very first live smoke read the window's `name` and got:

```
window name: 'rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519'
```

That looks exactly like a WIN-3 failure and is not one.

`do script` does not run our child. It opens a window running the user's
**login shell**, which sources their startup files — and this user's profile
runs `ssh-add --apple-use-keychain ~/.ssh/id_ed25519` — and only then does the
`exec '<repo>/Terminal Game'` line replace it. Terminal's active-process title
component follows whatever that shell is doing in the meantime, so for the
first fraction of a second the title is the user's own profile, not ours.

**Why WI-2 never saw it.** WI-2 read the title *"one second after the window
was created"* (its findings, §1). The shell has finished by then. WI-8 reads
it from the `on_window_ready` hook, which fires as soon as the window has been
configured and positioned — roughly 0.4 s earlier — and that is inside the
window where the shell is still starting.

**Measured settling time**, polling every 0.2 s from `on_window_ready`:

| run | window id | title settled after |
|---|---|---|
| 1 | 4102 | 0.4 s |
| 2 | 4103 | 0.4 s |
| 3 | 4248 | 0.8 s |
| 4 | 4251 | 0.4 s |

**What this project does about it.** `launch-smoke` polls the title until it
equals `Terminal Game` or `TITLE_SECONDS` (5.0) expires, and prints how long it
took. It does not sleep a fixed amount, because the number above is a property
of *this user's* shell profile and somebody else's will differ.

**What it means for anyone else who reads a window property back.** The tab's
*size and font* are safe to read the instant they have been written — they are
ours and nothing else touches them, and all four runs read `40 30
Menlo-Regular 18` immediately. It is only the **title** that has a third party
(the shell) writing to it, so it is only the title that has to settle.

**This does not change the WIN-3 recipe.** All three parts of it still hold
exactly as WI-2 measured. It changes only when you may believe the answer.

---

## 2. `displays()` fell back to a fake screen, silently, on a machine with three real ones

Between the first and second smoke attempts, `window.displays()` returned

```
[(0, 0, 1440, 900)]
```

which is `FALLBACK_SCREEN_BOUNDS` — the constant WI-2 put there for a machine
whose displays cannot be read at all. Seconds later, in a fresh process, the
same call returned the truth:

```
1  (0.0, 0.0, 1512.0, 982.0)
2  (-3509.0, -1440.0, 2560.0, 1440.0)
3  (-949.0, -1440.0, 2560.0, 1440.0)
```

and a direct `CGGetActiveDisplayList` through `ctypes` reported `err: 0,
count: 3` both times it was asked. So the fallback was **transient**, and it
happened while the smoke was opening and closing windows.

**The consequence is not cosmetic.** The reference window sits at
`(-898, 76)`. Against the real layout that point is on display 3, and the game
window lands at `(-868, 106)` — reference + 30, exactly where WIN-4 wants it.
Against the fallback rectangle that point is on **no display at all**, so
`choose_display` falls through to the first display and `offset_position`
clamps:

| screen layout `displays()` returned | game window landed at |
|---|---|
| the real three | `(-868, 106)` |
| the 1440 x 900 fallback | `(0, 106)` |

Both were observed, in consecutive runs, from the same reference position. The
second is the game appearing on a screen the player is not looking at — WIN-4
quietly not holding, with nothing printed anywhere.

**What this project does about it.** `displays()` now takes the supervisor's
`report` and says why it fell back:

```
could not read the screen layout (CGGetActiveDisplayList failed (N));
assuming one 1440 x 900 display. The game window may land on the wrong screen.
```

The **behaviour is unchanged** and deliberately so: the game must start whether
or not the screen layout can be read, and WI-2's choice of a conservative
fallback rectangle is still the right one. What changed is that it is no longer
silent — the same principle WI-8 applies to `osascript` errors.

**What was not done, and is a judgement for somebody else.** A transient
failure could be retried once before falling back. That was not added, because
the cause is not understood: the failure was seen once, was not reproducible on
demand, and a retry that papers over an unexplained CoreGraphics failure is
worth less than a line of output that lets the next person recognise it. If it
recurs, the report line is now what will show it.

---

## 3. The live smoke runs, in full

Six windows, three runs, no window left open, no error, no timeout, no modal
sheet.

| attempt | run | window id | title settled | position | result |
|---|---|---|---|---|---|
| 1 (before the title fix) | 1 | 4081 | — (sampled once) | `(-868, 106)` | FAIL — title read as the shell's |
| 1 | 2 | 4085 | — | `(-868, 106)` | FAIL — same |
| 2 | 1 | 4102 | 0.4 s | `(0, 106)` | PASS |
| 2 | 2 | 4103 | 0.4 s | `(0, 106)` | PASS |
| 3 | 1 | 4248 | 0.8 s | `(-868, 106)` | PASS |
| 3 | 2 | 4251 | 0.4 s | `(-868, 106)` | PASS |

The census was `[367, 2486]` before and after **every one** of those six
windows. Attempt 2 is where the silent display fallback shows up as `(0, 106)`.

Whole-run wall clock, attempt 3: **9.7 s** and **9.4 s**, of which 8 s is the
stand-in child deliberately staying alive.

---

## 4. Things deliberately NOT done on the user's machine

- **The real game was not launched by the smoke.** It blocks until a person
  presses `q`, and §2.6 rule 4 forbids launching, in a window you opened,
  anything you cannot end. The smoke's child is a Python script named literally
  `Terminal Game` that makes the same first write and then exits by itself. A
  person pressing `q` is **human check H2**.
- **No keystrokes were scripted into another application.** WI-4 declined this
  because it needs Accessibility, which this design does not require, and WI-8
  holds that line. The smoke's child ends on its own, so there is nothing to
  type at.
- **No busy tab was closed**, and no attempt was made to measure the modal
  sheet. There is no safe way to and no reason to.
- **No Terminal preference, profile or global setting was touched.** Nothing
  outside the tab of the window we created.
