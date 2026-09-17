# WI-20 — release readiness

**The last item in the run.** Measured 17 September 2026, 02:32Z – 02:34Z, against
`main` = `c57fce3` plus this branch, on macOS 26.6.2.

---

## The counts

Both, because they answer different questions.

### The suite as it is normally run

```sh
.venv/bin/python -m pytest -q
```

> **967 passed, 0 failed, 0 skipped, 10 deselected**

The ten deselected are the `needs_window` tests. `pytest.ini` excludes them so that the
command every developer runs all day can never put a window on somebody's screen — ground
rule 1.6.

### The suite with nothing excluded

```sh
.venv/bin/python -m pytest -q -m "needs_window or not needs_window"
```

> **977 passed, 0 failed, 0 skipped, 0 deselected — in 17.49 s**

**This is the first run in the project in which all ten window tests executed together.**
There were four when it became WI-20's requirement.

| | before | after |
|---|---|---|
| crash reports (`~/Library/Logs/DiagnosticReports/Python-*.ips`) | **14** | **14** — zero new |
| visible applications | **7** | **7** — nothing left behind, nothing lost |

Run under a **180-second deadline in a parent process**, not a pytest timeout, because a
hang inside `mainloop` is not something pytest can interrupt. It finished in 17.65 s
wall-clock and was never close to it.

---

## That run found a real defect, which is the whole argument for requiring it

The first attempt was **1 failed, 974 passed**. Lane C's
`test_the_real_entry_point_runs_and_reaps_itself` caught this:

> **A game that ends between two beats leaves a scheduled beat outstanding.**

`Game._schedule` declines to book the *next* beat once the session stops accepting play —
but it runs *after a beat*, not after a quit. So a `q`, or the close button, or
`run_game`'s watchdog, would end the game with an `after` still pending. `timer_is_running`
went on reporting `True` for a game that was over, and on a shared Tk interpreter — which
is what a test suite has — the pending callback was still live and still fired.

**Nothing in the default suite could have seen it.** The defect is in the assembly's
shutdown path, reachable only by actually running the entry point on a real window.

Fixed in `game.py`: closing the window now stops the game's timer as well as quitting its
session. **Two tests were added in the default suite** so it cannot come back quietly —
one for the `q` route and one for the close-button route, because a fix that handled only
the quit intent would have left the real entry point exactly as it was.

Counted honestly: **WI-20 changed product code.** A release-readiness item that finds a red
test must fix it or report the suite as red; reporting green was not available.

---

## Requirement status, from WI-18's audit, read carefully

**38 MET · 3 MET pending a human formality · 4 NOT MET on unanswered human questions ·
1 NOT MET, not implemented · 2 PARTLY · 1 claimed by nothing.**

### The rows a reader will get wrong if they skim

**WIN-4 — the window is placed, and WIN-4 is still not met.** Both halves are true and the
first one makes the second easy to miss. WI-14b and WI-14c wired the placement that WI-15
had built and nobody was calling, so the window now lands where it was designed to — but
the shipped reader is `NoAnchor`, which follows nothing, so it centres on the main display
instead of appearing beside whatever the player was last using. **"Placement fixed" and
"WIN-4 met" are not the same sentence.** The honest row is *not met, wired to the
fallback*.

**WIN-5, END-5, END-6 — 34 tests, and the question they answer is one we chose.** These
are contradiction C-1: WIN-5 says the window closes as soon as the game ends, END-5 says
the last picture stays, END-6 says `q` is the only way out. They cannot all be literally
true. The suite pins **assumption P1** — the architect's reading — thoroughly and well.
**It does not pin the requirement**, because nobody has told us which reading is right.
A green suite here means *we implemented what we assumed*.

**WIN-2 — the size is verified, the comfort is not.** 400 × 570 on a black ground is
measured. Whether Menlo 16 is *"large enough to read comfortably"* has no test and never
will.

**GAME-1 was claimed by nothing** — no test, no source, no docstring — while being
realised by everything. WI-20 gives it one: the `terminal_game` package docstring now
states it. That converts an assumption into a claim, which is the cheapest thing in this
document.

### And a caution about the audit's own numbers, from the lane that wrote it

Lane B's first scanner reported WIN-1, WIN-3 and STAT-1 as untested. All three were false —
those files carry the requirement code on the enclosing class rather than in each test
body. It caught this before publishing. Its conclusion is worth keeping:

> **A false gap is worse than a missing one: it sends somebody to fix what is not broken
> and spends the credibility of the rows that are true.**

Even corrected, **the counts measure labelling, not coverage.**

---

## What is still for a person

Five checks, two minutes, in **`docs/findings/WI-17-human-verification.md`** — the
titlebar; the four arrow keys; `q`, `Q` and that nothing typed is echoed; whether 16 pt is
comfortable; and whether the wall runs look joined. Each is written as a *failure shape*
rather than as "does it look right", because the second is not a question anyone can
answer.

Plus **one decision**: WIN-4, presented there as an option with a cost rather than as a
defect — including that granting Accessibility makes a currently-dormant assumption
load-bearing, namely that Tk's (0, 0) is the display server's (0, 0), which nobody has
shown.

**And the sentence this run should be handed over with: nobody has yet seen this game.**
It has opened on this desktop five times across four items and closed itself in about a
second every time, unwatched. 977 tests pass and not one of them has seen a pixel.

---

## Setting it up from nothing

Lane B verified this by actually cloning.

```sh
git clone git@github.com:replicant1/NewTerminalGame.git
cd NewTerminalGame
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q          # 967 passed, 10 deselected
.venv/bin/python -m terminal_game.shell.game
```

**`/usr/bin/python3`, not bare `python3`.** On this machine `python3` may resolve to a
Homebrew 3.14 with no `_tkinter` at all, and the game cannot open a window without one.
`tests/test_runtime.py` fails immediately and says so if the environment was built any
other way, which is the point of it.

`pip` in the bundled venv is 21.2.4 and prints a notice that a newer version exists. It is
cosmetic; nobody upgrades it, so that every environment is built the same way.
