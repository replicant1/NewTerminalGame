# M2 — DEV-C — completion record

**Developer:** DEV-C · **Iteration:** M2, *the rules and the picture* · **Run:** 6
**Mode:** non-local, real pull requests, developer merges their own.

DEV-C's M2 lane was **WI-13 (day 9)** and **WI-14 (days 10–11)**.

**WI-13 moved to DEV-A in amendment 3** and landed there, so this lane's M2
is **WI-14 alone.** The move was right and worth recording from this side:
A7 confines the status-line literals to WI-13 and DEV-A already owned the
outcome vocabulary WI-13 selects by, so putting the two in one lane removed a
cross-lane conform rather than creating one.

| PR | Branch | What |
| --- | --- | --- |
| [#54](https://github.com/replicant1/NewTerminalGame/pull/54) | `r6/wi-14-anchor` | WI-14, this record, and WI-10's closing log lines. |

---

## WI-14 — The anchor · **DONE**

| | |
| --- | --- |
| Branch | `r6/wi-14-anchor`, cut from `main` @ `67de3f1` |
| Pull request | [#54](https://github.com/replicant1/NewTerminalGame/pull/54) |
| PR summary | `docs/prs/PR-WI-14-anchor.md` |
| Finding | `docs/findings/WI-14-anchor-query.md` |
| Progress log | `docs/progress/r6-wi-14-anchor.md` |

The plan names the branch `r6/wi-14-window-anchor`; the dispatch named it
`r6/wi-14-anchor`, and the dispatch won.

### What was built

- `terminal_game/shell/anchor.py` — the arithmetic and the policy.
  `ScreenBounds`, `Anchor`, `WindowAnchor`, `is_on_screen`,
  `brought_onto_screen`, `no_anchor`. **Names no toolkit.**
- `terminal_game/shell/tk_anchor.py` — `pointer_anchor()`, the one module
  here that meets Tk. Withdrawn root, no event loop, destroyed in a
  `finally`.
- `tools/probe_anchor_query.py` — runs the real query once. Bounded by a
  hard `SIGALRM`. Not part of the suite.
- `tests/test_anchor.py` — 29 tests, no toolkit anywhere in them.

WI-3 needed no change. The fallback is WI-3's own `DEFAULT_WINDOW_POSITION`,
imported rather than retyped, with a test asserting they are the same object.

---

## The two things this item found that nobody predicted

### 1. A2's permission is not what is stopping us

The plan treats Accessibility permission as the one obstacle to a real
anchor. There is **a second one underneath it, and no permission grant would
clear it.**

Measured, Tk 8.5.9 on `aqua`:

| | |
| --- | --- |
| `winfo_pointerxy()` | **`(-175, -448)`**, stable over 5 reads |
| `winfo_screenwidth/height` | **1512 × 982** |
| `winfo_vrootx/y/width/height` | **`(0, 0, 1512, 982)`** |
| `maxsize()` | **`(5120, 2422)`** |

The pointer is on a display up and to the left of the primary. Tk reports it
in whole-desktop coordinates, but every bounds query describes the **primary
display alone**. `maxsize` knows the desktop is bigger and gives no origin,
so it is not a rectangle anything can be clamped into.

**So on this machine the game opens at the fallback `(120, 120)` for a
reason that has nothing to do with permissions.**

### 2. The probe found a defect in the code written to run it

The guard had been `if x < 0 or y < 0`, commented *"Tk answers -1, -1 when it
cannot say"*. **False.** Tk answers with real coordinates that happen to be
negative. Right here by luck; wrong on a machine with a display to the
*right* of the primary, where the pointer reads past 1512 and the window
would have gone off the edge with no clamp able to save it.

Now `is_on_screen(position, screen)`, written on the measurement.

**No unit test could have caught it** — every test supplies its own query, so
every test was consistent with the wrong belief. This is precisely the shape
amendment 2's *"proved by a double is not proved"* was written about, and it
is the second time this run that the real medium has found what the doubles
could not.

---

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

| Moment | Result |
| --- | --- |
| `main` @ `67de3f1`, before WI-14 | **574 passed, 0 failed, 0 skipped** |
| `r6/wi-14-anchor`, complete | **603 passed, 0 failed, 0 skipped** |
| after merging `origin/main` (WI-16, WI-17) | **634 passed, 0 failed, 0 skipped** |

29 new; the merge was clean with no conflict. **All six of WI-10's house rules clean** over the tree with this
branch on it — including rule 5, which is what keeps the suite from ever
constructing the Tk interpreter that `tk_anchor.py` needs.

---

## Windows opened in this lane during M2

**Zero.** The probe ran twice; both runs withdrew the root before anything
could be mapped, never entered an event loop, and reported `root mapped:
False`, `root state: withdrawn`, with `tkinter._default_root` back to `None`
afterwards. `pgrep` found no leftover process of mine.

Run under the conductor's screen gate, held exclusively, and released
explicitly when done. The project ledger stands unchanged at **21 opened, 21
reaped, no modal sheet ever raised**.

**DEV-C's own count across WI-8, WI-10 and WI-14 is zero.**

---

## Deviations needing a ruling

1. **The anchor is the mouse pointer, not another application's window.**
   A2 says *window*; on this machine the game can see no window without a
   permission nobody has granted, and the pointer is what it can see without
   asking. Reversing it is one constant — hand `WindowAnchor` the
   `no_anchor` query — and every fallback test already passes.
2. **An anchor outside the primary display's bounds is treated as nothing
   seen.** Additive, forced by the measurement above.
3. **The branch name** differs from the plan's, per the dispatch.

---

## Contradiction found in the plan

**Section 4 asks for a measurement it also forbids taking.** Amendment 2
requires the real query to be run because *"a stub cannot prove the absence
of a permission dialog"*; the same section says to stop rather than run
anything that could prompt. Both held here **only because the query built
cannot prompt**. Had the privileged one been built, the honest answer would
be that **the absence of a dialog is not establishable by any action
available to us** — it needs the user, in front of the screen. **WI-21 will
meet the same shape.**

---

## What is open, and was not closed here

- **A2** — pointer versus window. With the lead.
- **A1** — does the titlebar read exactly *Terminal Game* to a human eye?
  Untouched by this lane. Three developers have declined to close it; so
  does this one.
- **SCRN-3** — do the blue double lines' strokes actually meet? Recorded as
  open in four places by WI-8 and still open.
- **Where the window actually lands**, to a person looking at it. WI-21's.
- **The privileged query is untried and should stay that way** until
  somebody who can see the screen decides to try it.
