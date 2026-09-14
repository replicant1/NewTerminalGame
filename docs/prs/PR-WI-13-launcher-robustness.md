# WI-13 — launcher robustness

**Branch:** `wi-13-launcher-robustness`, cut from `main` at `16b4dac`
**Lane:** DEV-B, iteration M2
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **658 passed, 0 failed, 0 skipped** (8.4 s), on this branch with `main` at `01628bd` merged in (620 + 34).
**Windows opened: 17. All 17 closed. The visible-window census returned to its starting value after every probe.**

---

## The headline

**The launcher no longer kills the game and reports success.** Proved on the real desktop through the
production path, against WI-3's own signature for the defect — *"a session takes the same 1.0 s
whether the game was asked to run for 5 seconds or for 12"*:

| hold asked for | session took | reported |
| --- | --- | --- |
| 3 s | **4.04 s** | `closed=True` |
| 8 s | **9.03 s** | `closed=True` |

Holds differ by 5 s; sessions differ by 4.99 s. The game runs its full length and the window closes
cleanly afterwards.

**Re-run on the merged tree** after `main` at `01628bd` — WI-11's loop and twelve plan edits — landed
in this branch, because "it worked before those landed" is not the claim worth making: **3 s → 4.00 s,
8 s → 8.95 s, differing by 4.96 s, both closed.** Two more windows, census returned.

## The first obligation, and why it was deletion rather than deprecation

`WindowLauncher.run` waited on the tab's `busy` flag. The process list was **already there** — DEV-A
built `script.window_processes`, `Desktop.processes` and `has_live_processes` in WI-3 and pointed
`game.play` at them — but `run` and `wait_until_idle` still *defaulted* to the flag. So the defect
survived on the path the docstring told people not to use.

**So the fix is not another helper. It is removing the choice.**

- `wait_until_idle` defaults to `has_live_processes`; `run` inherits it.
- **`Desktop.is_busy` and `script.window_is_busy` are deleted.** Not deprecated, not left with a
  comment — gone, with a tombstone comment at each site explaining the absence.
- The reap's failure message no longer says "still busy": `busy` is a removed concept, so it says
  *"something is still running in window …"*.
- The warning docstring is gone, as ruled. **What it knew is kept** — `run` still says what it waits
  on and why, and there is a test that it does, so deleting the warning did not delete the knowledge.

The condition was *exactly one answer in the system*. Two things answering one question differently is
the trap, and **this defect is the proof of how it plays out**: both existed for the whole of WI-3, the
correct one was documented at length in a warning, and the wrong one was still the default. **A warning
is not a guard.** There are now tests asserting the second answer is *gone*, so putting it back is a
deliberate act rather than a convenience somebody adds in passing.

## The measurement refines WI-3 rather than merely confirming it

WI-3 says *"it is the grid alone"*. **The first thing I measured contradicted that**: one window,
`sleep 6`, the full 40 × 30 configure applied, and `busy` tracked the process correctly from start to
finish. The defect would not reproduce.

Rather than report a fix to a defect I could not reproduce, I ran the four cells — one window each:

| command | grid applied? | samples where `busy` lied |
| --- | --- | --- |
| `sleep` | no | **0** of 9 |
| `sleep` | yes | **0** of 8 |
| the real game command | no | **0** of 15 |
| the real game command | yes | **8 of 9** |

**It takes both.** The grid is necessary and not sufficient. That matters because anyone trying to
keep `busy` by *not* setting the grid would test with a simple command, see it work, and ship a
launcher that fails on the real game — and anyone testing the grid with a simple command concludes
`busy` is fine. Both roads lead back here. The `window_processes` docstring now carries the table.

**I have not established the true cause** and say so in the finding. The real command differs from
`sleep` in several ways — it waits on `stty size`, runs under `/bin/sh -c`, and puts the terminal into
curses raw mode. Raw mode is a suspicion, untested, and it stays a suspicion.

With the real command the defect reproduces exactly, twice: `busy` false at +0.75 s while
`login|Python` ran on to +4.2 s. **The process list was accurate across the whole span and never once
empty while something was running** — which is the property `has_live_processes` depends on and the one
I most expected to find broken.

**One false alarm of mine, recorded because it would mislead the next person.** An earlier probe saw an
empty process list at +0.33 s and looked exactly like a start-up race. It was my error: `do script`
starts in the player's home directory, where `python3 -m terminalgame.game_main` is not importable, so
the game died instantly and the empty list was honest.

## The rest of WI-13

Per §11.2 this item is hardening and verification, not first implementation. **The A2 fallbacks and
their failure injection are already covered by WI-1** in `test_launcher_lifecycle.py`
(`WhenTheDesktopWillNotSayWhereThePlayerWasLooking`, `WhenSetupFailsAfterTheWindowExists`) and are
**not duplicated** — a refused reference query still places at the documented default, a refused screen
query still falls back to the documented screen, and both refused still produces a running window.

`tests/test_launcher_robustness.py` adds 35 tests covering what WI-13 itself is for:

| Class | What it holds |
| --- | --- |
| `TheDefectThatMadeThisItemNecessary` | the regression at the level the defect was at — `run`, not `reap` |
| `OneQuestionOneAnswer` | no module in `launcher/` reads `busy`; the builder and the method are gone; the one that remains is the process list |
| `TheWarningIsGoneBecauseTheDefectIs` | and the knowledge in it is not |
| `NothingSurvivesAFailure` | every post-creation stage closes the captured identity — and a failure *before* the window exists closes nothing |
| `C2BeatsC3WhenTheyDisagree` | a window that will not go idle is left open, named, with the reason saying *why* |
| `AGameNothingBoundsButAPerson` | what happens when the command genuinely never ends — see below |
| `GoingIsCheckedWithVisible` | `visible`, never `exists` |
| `EveryCallIsStillBounded` | caution C4 |

**Each negative is paired.** "Does not close a busy window" is matched by "does close an idle one" and
by the middle case that actually happens — the game runs, then ends, then the window goes, with the
poll count and the sleeps proving it waited. "Closes the captured window on failure" is matched by
**"a failure before the window exists closes nothing"**, because a launcher that closed something on
every failure would pass the first and be dangerous.

## C2 over C3, revisited against the real thing

The established resolution holds and I changed nothing about it. A window that will not go idle within
the bound is **left open and its id named**, because closing it raises the modal sheet that blocks
every later automation call *including the cleanup itself* — so "reap anyway" does not even achieve
reaping.

I practised it as well as tested it: every probe that found its command still alive at the bound left
the window open rather than closing it. **In the event none had to — all 17 windows went idle and
closed.**

## A game nothing bounds but a person

M0's `--hold` was scaffolding, and the technical lead ruled it was not a precedent: the real game
exits on `q` and never on a timer. DEV-A is retiring it for `--seed`, which means **the launched
command will be bounded by nothing the launcher controls.**

That is correct for a game, and it is safe *only* because of the obligation this item exists for — the
launcher waits on the process list and never closes a window something is running in. But it makes
what happens at the end of the wait stop being hypothetical, so it is now tested rather than reasoned
about: a game that never ends is never closed out from under itself; the wait still ends rather than
hanging (caution C4); **the window left behind is named in the result**, because an orphan nobody can
identify is a hunt rather than a nuisance; and — the pair, without which a launcher that never closed
anything would pass all three — a player pressing `q` still gives the ordinary ending.

**Anything that starts a game with nobody at the keyboard must arrange its own way out.** That is
WI-14a's to carry, and it is the one consequence of the `--seed` change that reaches beyond DEV-A's
lane.

**Checked rather than carried:** I was told `--hold` is already gone from both sides. On `main` at
`01628bd` it is **still there** — `game_command` still takes `hold_seconds` and still emits `--hold`.
So the change has not landed, my measurement is reproducible on this tree, and when `--seed` does land
the equivalent probe needs the new argument and the timing measurement wants re-running.

## One thing I got wrong, and the code was right

I asserted that a reap reports `closed=False` whenever any call refuses. It reports `closed=True` when
only the **confirmation** refuses, with *"could not be checked"* in the reason. That is the better
behaviour — reporting "not closed" would send a person hunting a window that is almost certainly
gone — so I split the test to pin the distinction rather than flattening it. Three states, three
tests.

## Deviations, for a ruling

**1. `Desktop.is_busy` and `script.window_is_busy` are removed from the public surface.** This is the
ruled fix, but it is an API deletion and it changed other people's tests: `test_launcher_desktop.py`
and `test_launcher_script.py` lost their `busy` cases and gained process-list equivalents plus two
tests asserting the removal. **Nobody outside `launcher/` used them.**

**2. The `window_processes` docstring now carries my 2 × 2 table**, correcting "it is the grid alone"
in place. **I did not edit DEV-A's finding** — `WI-3-busy-is-false-after-a-grid-resize.md` is its
document and stands as written; mine cites it and records the refinement. If the technical lead would
rather the WI-3 finding carried a pointer, that is a one-line edit somebody should make deliberately.

**3. The reap's failure message changed text** from "is still busy after" to "something is still
running in … after". One test asserted on the old wording and now asserts the new.

## Contradictions found

**One, measured: WI-3's attribution of the defect to the grid alone is incomplete.** Evidence is the
2 × 2 table above, four windows, one per cell. It confirms the defect and the fix; it refines the
cause. Not a blocker and nothing depends on it — except the next person who tries to avoid the defect
by avoiding the grid.

## What needs a human

Three, none of them recorded as verified anywhere:

1. **Q2 — the Automation permission.** Every measurement here was taken on a machine where it had
   already been granted. No agent can grant it or confirm a refusal, and it stays on WI-14b's list.
   The *code path* for a refusal is tested by injection; the *real refusal* is not.
2. **Pressing `q`.** All 15 sessions ended because `--hold` ran out. Whether a person pressing `q`
   ends the session cleanly and the window is reaped is WI-14b's.
3. **What the window looked like.** Font coverage for the box-drawing and block characters, and colour
   legibility. Unchanged by this item and still human checks.

## Windows

**Opened: 15. Closed: 15.** Across six probes — 1, 3, 3, 2, 4 and 2. Every one had its id captured at
the moment of creation and only that id was ever named; no probe ever addressed "the front window" or
matched by title. Every close was verified with `visible`, not `exists`. The reap ran in a `finally`
so it also ran on the failure path. **The visible-window census returned to its starting value after
every probe without exception, and no modal sheet was raised at any point.**

## Commits

| | |
| --- | --- |
| `f180d1b` | WI-13: one answer to "is it still running", and the game stops being killed |
| `5495fba` | WI-13: the finding and the PR summary |
| `5764938` | WI-13: merge main, and harden for a game nothing bounds but a person |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
