# M3 — developer C — completion record

**Iteration:** M3, *A game you can play*.
**Lane:** C. **Mode:** non-local, real pull requests.
**Worktree:** `/Users/rodneybailey/CursesProjects/NewTerminalGame/.claude/worktrees/agent-a319e57ac3a444133`.
**Recorded** 17 Sep 2026, 02:30Z. **This is lane C's last iteration** — the lane has no
M4 item, and WI-19 exists to spend answers the user has not given.

## What was finished

**WI-16 — the end-to-end behaviour suite**, and **WI-16b — the assembled game uses what
was built for it**, added to WI-16's bar after the placement defect.

| PR | Title | Base | Merged as |
|---|---|---|---|
| [#99](https://github.com/replicant1/NewTerminalGame/pull/99) | WI-16: the end-to-end behaviour suite | `main` | `b302b2d` |
| [#103](https://github.com/replicant1/NewTerminalGame/pull/103) | WI-16b: the assembled game uses what was built for it | `main` | `7518e64` |

Both merged by me. **WI-16 was the plan's one stacked item** — cut from
`r7/wi-14-live-assembly` at `46f9682`, the public surface commit lane A pushed before
writing any tests. WI-14 merged while WI-16 was being written, so the PR went to `main`
directly rather than being opened against the parent and retargeted. **The surface did not
move under me.**

**Files added:** `tests/test_end_to_end.py` (33), `tests/test_end_to_end_placement.py` (16,
2 `needs_window`), `tests/test_assembly_uses_everything.py` (20), two PR summaries, two
progress logs. **No production code in either item.**

## The journeys

A **win** and a **loss** on a corridor ring, differing only in which way the player sets
off — with a test asserting they really do end differently, because if they ever agreed one
of them would be proving nothing. **The END-3 board**, two corridor squares: the smallest
board on which the two step orderings disagree, and they agree on every other. One move
eats the last dot *and* walks into the ghost — `CAUGHT`, score 1, zero dots left, and the
status line says so. **`q` from Playing and from Decided**, both cases and both cases of the
key.

**The positions are built; the verdicts are not.** No test stamps an outcome and expects it
believed.

**END-4 on a position the system produced**, which closed a gap lane B named: END-4 was
pinned only on a hand-made position. The loss journey plays to a *real* `CAUGHT` and then
asserts the ghost's three glyphs are what shows at the square they met on.

## The sweep

Seven capabilities have the assembly as their only possible consumer. **I measured all
seven** rather than guessing which were safe, since guessing which were safe is how WI-15
was missed.

**Six are reachable and called** — `generate`, `next_ghost_move`, `Session`,
`status_cells`, `intent_for`, `placement_for`. **The seventh, WI-7's skeleton, is
deliberately unreachable**, per section 7: WI-14 supersedes its fixtures and owns the entry
point thereafter. A test records that so nobody wires it back in.

**Placement was the only real failure**, and WI-14b/14c closed it. The value is the
standing guard, not a second discovery.

**Why a source-level guard and not only a journey:** `Game.place()` is called from
`run_game` and nowhere else, and `run_game` shows a real window. Measured —
`build_game(...) + start()` leaves the window unplaced. So a headless journey **cannot** see
whether anybody calls it. Read with `ast`, like the layer rule, and it runs by default.

**Both detectors carry controls** — a call that is made is reported, a call that is not made
is not, the walk reaches all four layers — because a guard whose whole job is catching what
nothing else can see is the worst possible thing to have pass vacuously.

## Things I corrected in my own work

**A brittle assertion.** I first pinned the unplaced window at `(5, 38)`; it failed at
`x: 150`. That is the *first* toplevel's default and a second cascades, so the test would
have depended on how many windows the suite built first. Every assertion now compares
against what the placement computes, or watches the position **change** — *a getter
answering is not evidence a setter ran.*

**A correction to my own evidence, which applied to every report I filed this run.** I had
been quoting `lsappinfo visibleApplicationCount` as showing no window reached the screen.
Measured: it reads one higher **while a withdrawn Tk root that maps nothing is alive**, and
its baseline drifts with what the user is doing. It counts registered applications — S-1's
Dock tile — not windows. It shows no stray application was left, which is worth keeping;
what shows no window is the toolkit-level assertion, and that is what the suites assert.

## A risk reported rather than fixed

**`anchor_from` swallows every exception broadly and deliberately, so an anchor reader with
the wrong shape is indistinguishable from one that found nothing — it silently centres.** My
stub spelled `read()` as `anchor()` and I got five green-looking fallbacks instead of five
errors. Right for production, since a placement failure must never stop the game starting —
but a **mis-wired** reader degrades WIN-4 in total silence, which is a cost of option A that
nobody had named. It is now in human item 4's cost line.

## Suite state

```
.venv/bin/python -m pytest -q          →  961 passed, 0 failed, 0 skipped, 9 deselected
```

On `7518e64`, `main` with both items in it, at 02:29:57Z. **WI-16 adds 33 and WI-16b adds
36.** Crash reports **14, none new since 02:00:51Z**.

## Lane C over the whole run

**Seven landings: S-2, WI-5, WI-6, WI-12, WI-12b, WI-16, WI-16b.** `main` green after every
one. Three conflicts, all in `tests/conftest.py` or my own progress logs, all resolved by
keeping both sides and none escalated. One window left on the user's screen for two
minutes, caught and killed by pid; fourteen crash reports, eleven of them mine, none since
02:00:51Z; one `launchd` job registered for four seconds and removed.

**What lane C leaves unanswered and cannot answer:** WIN-4's route — S-2 proved the anchor
is readable with no permission at all, so the user is choosing between three routes rather
than granting or declining, and until they do **WIN-4 is not met**. The titlebar, the type
size, whether the box-drawing glyphs read as unbroken lines, and the Dock tile the suite
now raises are the other four, and none of them is a thing an agent may record as verified.
