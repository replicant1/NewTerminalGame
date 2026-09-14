# WI-14a — the acceptance pack

**Branch:** `wi-14a-acceptance-pack`, cut from `main` at `01628bd`
**Lane:** DEV-B, iteration M3
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **666 passed, 0 failed, 0 skipped** (8.4 s). `main` was 620.
**Windows opened: 2. Both closed. Census returned to its starting value both times.**

---

## What it is

The machinery WI-14b runs, in two halves, and the division between them is the point of it.

| | |
| --- | --- |
| `acceptance/pack.py` | **the exercises** — drive the real launcher and the real game on the real desktop, and report what they observed |
| `acceptance/checks.py` | **the human-check register** — everything no agent can settle, with the steps and what to look for |
| `acceptance/__main__.py` | `python3 -m acceptance --list` (opens nothing) and `--run` (the real desktop) |
| `tests/test_acceptance_pack.py` | 46 tests |

`--list` is the default, because the half that needs no desktop should be the one you get by accident.

**The five stale root executables were not read, not used and not resurrected.** This is written from
nothing. There is a test that the only command the pack starts is the one it was handed.

## The obligation from `--hold`'s retirement, met by construction

The real game exits on `q` and never on a timer, so **anything that starts a game with nobody at the
keyboard has to arrange its own way out.** This pack writes `q` into the tab it created:

```
do script "q" in selected tab of window id N
```

WI-3 measured that reaching the game in 0.14 s; I measured **0.08 s**. It names the captured id like
every other call in this project, so it does not depend on which window has focus and cannot type into
whatever the person at the machine is looking at. `System Events` keystroke injection is deliberately
not used, and there is a test that it is not.

**The test for this is not a scan for the word "hold".** I tried that first and it was wrong — see
below. The real property is the **order**: `q` must be sent *before* the process list is ever seen
empty, so the ending is **caused** rather than awaited. A pack that merely waited would look identical
on a happy path where the game stops anyway.

`WindowUnderTest` is a context manager. It captures the id at creation and reaps in a `finally`, so a
failure anywhere inside cannot leave a window behind — and it **never closes one with a game still in
it**, leaving it and naming its id instead, because closing it raises the sheet that blocks every later
call including the cleanup (C2 beats C3).

## The pack found a defect in itself on its first real run

The best thing it did. The window opened, the game ran, `q` ended it, nothing was left behind — and the
captured picture was **3 rows, the widest 389 columns**, reported as an SCRN-1 failure.

It was not one. **"Something is running" is not "the game has drawn."** The launcher's command spends
its first moments in a shell loop waiting for the window to reach 40 × 30, so the process list goes
non-empty at +0.40 s while the tab still shows the shell's echo of the command line — which is 389
columns long.

So the pack now waits for **the requirement's own shape**: SCRN-1 says the picture is 30 rows, so it
polls until the tab shows 30 rows, and says plainly if that never arrives rather than judging whatever
the shell left behind.

**And the predicate for that was wrong once too.** My first version was "30 rows that all fit the
window" — which would have made the width check **unreachable**: a picture one column too wide would
stop counting as a picture, and the SCRN-1 failure it represents could never be reported. *A predicate
that swallows the failure it exists to surface is worse than a loose one.* Row count only, with the
reasoning written beside it.

## The second run, clean

```
[ok  ] the game starts in its window      GAME-1,WIN-1
[ok  ] `q` ends the game                  END-6,CTRL-4
[ok  ] nothing is left on the desktop     WIN-5     visible windows 1 before, 1 after
[ok  ] the game drew a picture at all     SCRN-1,SCRN-2   30 rows captured
[ok  ] the picture fits the window        SCRN-1,MAZE-1   30 rows, widest 40 columns
[note] what the picture contains          SCRN-1
[note] the window is the size asked for   WIN-2     357 x 558 points
[note] the title bar                      WIN-3     ... NOT VERIFIED
```

| | |
| --- | --- |
| window created | +0.13 s |
| configured | +0.33 s |
| game running | +0.41 s |
| **picture drawn** | **+0.67 s** |
| `q` sent | +0.90 s |
| **game gone** | **+0.98 s — 0.08 s after the `q`** |
| window closed, `visible=false` | +1.22 s |

**5 ok, 0 failed, 3 observed for a person to judge.** Three states, not two: `note` means *observed,
not judged*, and it exists because several of these record a number a person must look at rather than
a pass or a fail.

**The picture captured is M0's skeleton**, correctly — the real game arrives with WI-12, which is
unmerged. The pack judges the picture's **shape and never its contents**, precisely so that it is
still right when WI-12 lands. A pinned frame would pass today and fail the moment the thing it exists
to check turns up.

## The human-check register is code, and cannot be ticked

The four document shapes have no slot for a checklist, and a markdown checklist can drift from the
requirements in silence. So the register is code — and being code, it can be held to account:

- **`HumanCheck` has nowhere to record an answer.** Not a field set to `False`: **no field at all.**
  There is a test that no `passed`, `verified`, `ok`, `result`, `answer` or `status` field exists, and
  a test that the rendered output carries no tick column.
- Every check names **the requirement codes it settles**, carries **steps somebody could follow**, and
  says **why no machine can answer it** — that last field is load-bearing, because without it somebody
  automates one of these badly and deletes it from the list.
- **12 checks, 21 requirement codes.**

**WIN-3 is recorded as NOT MET**, not softened into "have a look" — there is a test for that wording,
because it is the one requirement this project knows it does not meet.

**GHOST-1's confinement is two lines, not one**, per §11.11: the mechanism is verified and GHOST-2 to
GHOST-4 are met, *and* the purpose clause is a human check with the 1.6 % measurement beside it. There
is a test that both halves are present, because a reader given only the second would take it for a
defect.

The register says in its own words: *"None of these is recorded as verified anywhere, and none of them
can be."*

## Four of my own tests were wrong in the same way

They scanned module source for a **word** when the property was about **behaviour**. "Never uses a
hold" failed because the docstring explains why it does not; "does not resurrect the stale
executables" failed because the docstring *names them in order to say they are not used*.

**That is exactly the weakness I flagged in WI-5a's word-list scan, committed again by me.** Replaced
with behavioural tests — the `q`-before-empty ordering, and the only command started being the one
passed in. Worth recording rather than quietly fixing: the lesson did not transfer on its own, which
says something about how much a rule in a document is worth against a habit.

## Deviations, for a ruling

**1. A new top-level package, `acceptance/`.** The plan names the pack but not where it lives. It is
not part of the game and not part of the launcher: it drives both from outside, and putting it inside
either would give the game a dependency on its own test harness.

**2. The `q`-driving script lives in the pack, not `launcher/script.py`.** WI-3's finding is explicit
that this is a harness technique and that nothing in `launcher/` sends input to the game. The pack
builds its own bounded `ScriptCall`s rather than importing `launcher.script._bounded`, so it depends
on the launcher's public vocabulary and none of its internals.

**3. The human-check register is code rather than a document.** Reasoning above. If the technical lead
would rather it were a markdown file, `checks.render()` already produces exactly that and can be
redirected into one — but then nothing tests it.

**4. `tests/test_layering.py` is not touched.** `acceptance/` is not a layer of the game and the
layering test walks `terminalgame/` and `launcher/`. **Recorded here as a deliberate omission** per
EDIT 11. If the lead wants the pack's boundaries guarded there too — it may import from `launcher` and
from nothing in `terminalgame` — that is a small addition and I would rather it were asked for than
assumed.

## Contradictions found

**None.** The plan's description of WI-14a matches what it needed to be. One thing worth flagging that
is not a contradiction: the pack cannot yet exercise the **real** game, because WI-12 is unmerged and
`main`'s `game_main` is still M0's walking skeleton. That is a sequencing fact, it is why WI-14b waits
on WI-12, and the pack is written so that nothing about it needs to change when WI-12 lands.

## What needs a human

**Twelve checks, twenty-one requirement codes — the whole register.** `python3 -m acceptance --list`
prints them. The largest single gap, worth naming here because it is invisible from inside the code:

**`contents of selected tab` returns text and nothing else, so no automated check anywhere in this
project covers SCRN-3 to SCRN-6 at all.** Not weakly — not at all. Every colour in this game is
unverified, and two of the five are substitutions besides.

And: **nobody has pressed an arrow key in a real window on this project.** The pack drives `q` as
terminal input, which proves the game's read-key path and its quit condition; it does not prove that a
key from a real keyboard reaches the same code, and arrow keys arrive as escape sequences and have
never been exercised that way at all.

## Windows

**Opened 2, closed 2**, one per real run. Both captured at creation and only that id ever named; both
confirmed gone with `visible`, never `exists`; the reap in a `finally`. **Census 1 before and 1 after,
both times. No modal sheet was raised.**

## Commits

| | |
| --- | --- |
| `3312366` | WI-14a: the acceptance pack, and the way out it arranges for itself |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
