# WI-14 — The anchor

**The headline is not the one the plan expected.** On this machine the
anchor query returns nothing and the game opens at the fallback — and **A2's
permission is not the reason.** The pointer is on a second display, and Tk
8.5 will not report that display's bounds. **No permission grant would clear
that.** Full measurement in `docs/findings/WI-14-anchor-query.md`.

**Branch:** `r6/wi-14-anchor`, based on `main` at `67de3f1`.
**Developer:** DEV-C. **Depends on:** WI-3, landed.

The plan names this branch `r6/wi-14-window-anchor`; the dispatch named it
`r6/wi-14-anchor`. The dispatch won. Noted so nobody hunts for the other.

---

## What this is

WIN-4, under assumption A2. Two modules, the same split as WI-3's:

| Module | What |
| --- | --- |
| `terminal_game/shell/anchor.py` | the arithmetic and the policy. **Names no toolkit.** |
| `terminal_game/shell/tk_anchor.py` | the one module here that meets Tk. |

`WindowAnchor(query, offset, fallback).position_for(size)` gives the screen
position for the game's window. `tools/probe_anchor_query.py` runs the real
query once, deliberately, and is what the findings document is written from.

WI-3 needs no change: `WindowOwner` already takes a `ScreenPosition`, and the
fallback is WI-3's own `DEFAULT_WINDOW_POSITION`, **imported rather than
retyped** — a test asserts they are the same object, because two positions
both meaning "somewhere safe" is the shape of mistake the first-lander rule
exists for.

---

## The permission question: absent, not guarded

**There is no code anywhere in this branch that could raise a permission
dialog.** No `osascript`, no System Events, no window list, nothing that
touches another application. The privileged route is *absent*, which is a
stronger assurance than a flag someone could flip.

Seeing another application's window on this machine needs Accessibility or
Automation permission, which only the user can grant and nobody has, and
whose first use puts a **modal** dialog on the screen. A modal dialog blocks
AppleScript, so it would hang the next scripted call anyone in this run
makes, unwatched.

That leaves A2's literal reading — *the frontmost window the game can see
without asking for Accessibility permission* — resolving to **none, ever**,
with WIN-4 satisfied only by a fixed corner.

**So the query is the mouse pointer instead. This is a deviation from A2's
word "window" and it needs a ruling.** It is permission-free, and it answers
WIN-4's stated purpose — *"so it always lands somewhere visible"* — better
than a fixed corner does. It is one constant's worth of change either way:
hand `WindowAnchor` the `no_anchor` query and the game goes to `(120, 120)`,
which is A2's literal reading, and every fallback test already passes.

---

## Proved by a double is not proved — what was exercised against the real thing

`tools/probe_anchor_query.py`, run twice under the conductor's screen gate:

```
/usr/bin/python3 tools/probe_anchor_query.py
```

| Observed | Run 1 | Run 2 |
| --- | --- | --- |
| Query returned | `None` | `None` |
| Elapsed | **118.6 ms** | **115.0 ms** |
| Permission dialog | none seen | none seen |
| `root mapped` / `root state` | `False` / `withdrawn` | `False` / `withdrawn` |
| `tkinter._default_root` after | `None` | `None` |

**A TCC dialog blocks its calling process until a human answers it, so a
115 ms return is a return that waited for nobody.** That is the evidence, not
the assertion.

**Windows opened: zero.** The root is withdrawn before anything can be
mapped, the event loop is never entered, and the root is destroyed in a
`finally`. `pgrep` afterwards found exactly one Python alive and it was
`orchestration/server.py`, not mine. The project ledger stands at 21 opened,
21 reaped.

---

## What the probe found, and it was a defect in my own code

This is the reason the plan makes us run these, so it is here rather than
quietly fixed.

Measured, Tk 8.5.9 on `aqua`:

```
pointer           : (-175, -448)      stable over 5 consecutive reads
screen (primary)  : (1512, 982)
virtual root      : (0, 0, 1512, 982)
maxsize           : (5120, 2422)
```

**The pointer is on a display up and to the left of the primary.** Tk reports
it in whole-desktop coordinates, but `winfo_screenwidth`/`height` *and*
`winfo_vrootwidth`/`height` all describe the **primary display alone** — they
agree exactly. `maxsize()` knows the desktop is 5120 × 2422, so Tk knows it
is bigger, but a size with no origin is not a rectangle anything can be
clamped into.

The guard had been written as `if x < 0 or y < 0`, with the comment *"Tk
answers -1, -1 when it cannot say where the pointer is"*. **That comment is
false.** Tk answers with real coordinates that happen to be negative. The
guess was right here **by luck** and would have been wrong on a machine with
a display to the *right* of the primary, where the pointer reads past 1512
and is exactly as unbounded — and the window would have gone off the edge
with no clamp able to save it.

It is now `is_on_screen(position, screen)`, written on the measurement and
tested at both edges and both signs.

**No unit test could have found this.** Every test supplies its own query, so
every test was consistent with the wrong belief. Only the real toolkit on the
real machine had the number.

The policy that follows: **an anchor we cannot bound is treated as nothing
seen**, because WIN-4's purpose is visibility and a fixed position on the
primary is certainly visible.

---

## Tests

`tests/test_anchor.py`, 29 tests. **No window, no toolkit and no permission
prompt anywhere in the file** — the query is a collaborator and every test
supplies one.

- **`GivenAnAnchorTheWindowGoesBelowAndToTheRight`** — the placement is the
  anchor plus the offset, and it really is below *and* to the right.
- **`WithNothingToAnchorToItUsesTheFixedOffset`** — a query that sees
  nothing, one that raises, and one that answers with nonsense all fall
  back; what it raised is kept as `.failure` rather than swallowed; the
  fallback **is** WI-3's `DEFAULT_WINDOW_POSITION`.
- **`TheQueryIsAttemptedOnceAndNeverAgain`** — asking three times queries
  once, a failed query is not retried, and nothing is asked until somebody
  asks where the window goes. A repeated privileged query is a repeated
  chance of a dialog.
- **`AWindowPastTheEdgeIsBroughtBack`** — past the right edge, past the
  bottom, the whole window fits afterwards, a window that fits is not moved,
  and a window bigger than the screen goes to the corner.
- **`APointOnASecondDisplayIsNotAPointWeCanUse`** — the measured `(-175,
  -448)` against the measured `1512 × 982`, plus the far edge and the
  right-hand case the real machine does not have.
- **`TheFallbackIsNotClamped`** — because a query that saw nothing told us
  nothing about the screen either.
- **`NothingHereTouchesTheToolkit`** — the policy module's own imports,
  parsed. Not a duplicate of WI-10 rule 1: `anchor.py` is *in* the Shell, so
  rule 1 does not cover it, and this is the narrower statement for this item.

**Suite**, from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
603 passed, 0 failed, 0 skipped   # before merging main
634 passed, 0 failed, 0 skipped   # after merging origin/main (WI-16, WI-17)
```

574 before this branch, so 29 new; the merge was clean with no conflict.
**All six of WI-10's house rules are clean** over the merged tree.

---

## Also on this branch

The four closing lines of `docs/progress/r6-wi-10-house-rules.md`, which
record PR #52's own merge and so could not ride on it, and
`docs/completions/COMPLETION-M2-DEV-C.md`.

---

## Deviations needing a ruling

1. **The anchor is the mouse pointer, not a window.** A2 says *window*. The
   reasoning and the cost of reversing it are above. This is the one that
   matters.
2. **An anchor outside the primary display is treated as nothing seen.**
   Additive, and forced by the measurement: there is no rectangle to clamp
   into, and WIN-4 asks for visibility.
3. **The branch is `r6/wi-14-anchor`, not the plan's `r6/wi-14-window-anchor`.**
   The dispatch named it; recorded so the record is straight.

---

## Contradiction found in the plan

**Section 4 asks for a measurement it also forbids taking, and only the shape
of this item hides it.**

- Amendment 2: *"a stub cannot prove the absence of a permission dialog… the
  real query must be run for real, once, and what happened written down."*
- Section 4 rule, and the standing instruction: *"If you find yourself on a
  code path that could prompt, stop and record it rather than trying it to
  see."*

Both held here **only because the query built cannot prompt.** Had the
privileged query been built they would have contradicted each other outright,
and the honest answer would be that **the absence of a permission dialog is
not establishable by any action available to us** — it needs the user, in
front of the screen.

**WI-21 will meet the same shape** when it asks A2 for real.

---

## What needs a human

1. **Rule on the pointer-versus-window deviation** (A2). One constant.
2. **Look at where the window lands.** Nobody has watched it open. WI-21's,
   with A1 and A4.
3. **The privileged query is untried and should stay that way** until
   somebody who can see the screen decides to try it.

**A1 and SCRN-3 are untouched by this branch and remain open.**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
