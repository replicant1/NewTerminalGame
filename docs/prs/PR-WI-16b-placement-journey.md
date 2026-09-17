# WI-16b — the assembled game uses what was built for it

The guard for the class of defect WI-15 fell into: a capability **complete, tested, and
never called**. Two test files, no production code.

**The seven-capability sweep is done and it is in here**, so this is one landing rather
than two — the work was already written when the question of scope was asked.

## The answer to the sweep, first, because it is the useful part

The lead's graph analysis named **seven capabilities whose only possible consumer is the
assembly**. I measured all seven against the entry point rather than guessing which were
safe, since guessing which were safe is how WI-15 was missed.

| Capability | Reachable from `shell.game`? | Actually called? |
|---|---|---|
| WI-2 maze generation — `generate` | yes | yes |
| WI-9 ghost policy — `next_ghost_move` | yes | yes |
| WI-11 session controller — `Session` | yes | yes |
| WI-12 status line — `status_cells` | yes | yes |
| WI-13 input translation — `intent_for` | yes | yes |
| WI-15 placement — `placement_for` | yes | yes *(since WI-14b)* |
| WI-7 walking skeleton | **no** | **correctly so** |

**Six of seven are wired. The seventh is meant to be unreachable** — section 7 says *"WI-7
builds it with fixtures to prove the slice; WI-14 supersedes those fixtures and owns it
thereafter."* Two live entry points would be two things to keep in step and only one of
them would ever be played. A test records that so nobody "fixes" it by wiring it back in,
and another records that the skeleton and its own tests still exist.

**So placement was the only real failure, and WI-14b/14c closed it.** The value here is the
standing guard, not a second discovery.

## `tests/test_assembly_uses_everything.py` — 20 tests

Reads the source of everything reachable from the entry point with `ast`, the same
technique `tools/layer_rule.py` uses and for the reason that module already gives: *a
sentence remembers what was true once and nothing re-runs it.*

Reachability is necessary but **not** sufficient — `placement` was imported by `window.py`
for a type the entire time it was never used for a decision — so each capability also names
the call that has to happen.

`TestTheDetectorWorks` keeps the file from passing vacuously: the entry point is found, the
walk reaches all four layers and a sane number of modules, a call that **is** made is
reported, and a call that is **not** made is **not** reported.

## `tests/test_end_to_end_placement.py` — 16 tests, 2 of them `needs_window`

Three layers, because one is not enough:

1. **Behaviour, default suite** — `place()` moves the window to the coordinates
   `placement_for` computes, returns the point it used, does not disturb the 400 × 570, and
   is idempotent.
2. **The call site, default suite** — `run_game` really calls `place()`, and calls it
   *before* `show()`, because a window placed after being shown is a window the player sees
   jump. **This is the assertion that catches an absent call site**, and it runs by default.
3. **The whole chain, `needs_window`** — `run_game` on a real window returns and reaps
   itself; and separately, a placed window really is where placement said *while it is
   still up*.

**Why the static check rather than only driving it:** `Game.place()` is called from
`run_game` and nowhere else, and `run_game` shows a real window. Measured —
`build_game(...) + start()` leaves the window unplaced. So a headless journey through
`build_game` **cannot** see whether anybody calls `place`. The instance was fixed; the class
needed a different kind of test.

## The trap, and how every assertion avoids it

**A fresh Tk toplevel already has a position.** The first is `(5, 38)`; a second on the same
root cascades elsewhere. So "the window has a position", "its geometry parses", "it is not
at the origin" all pass with no placement code having run — and pinning the default would
make the test depend on how many windows the suite built first. **I wrote that brittle
version and it failed at `x: 150 != 5`.**

Every assertion now either compares against the coordinates `placement_for` computes, or
watches the position **change**. *A getter answering is not evidence a setter ran.*

## A risk worth reporting, found by falling into it

**`anchor_from` swallows every exception broadly and deliberately, so an anchor reader with
the wrong shape is indistinguishable from one that found nothing — it silently centres.**

My stub spelled `read()` as `anchor()`. Instead of five errors I got five green-looking
fallbacks, every one returning the centred point. That behaviour is *right* for production —
a placement failure must never stop the game starting, which is WI-15's bar — but it means
a **mis-wired** reader degrades WIN-4 in total silence. That is the same class of invisible
defect this whole item exists for, and it is worth knowing before the user picks a real
anchor route.

Not proposing a change: the broad catch is deliberate and defensible. Raising it because
whoever wires the real reader should know that getting its shape wrong will look exactly
like the fallback working correctly.

## What this does **not** claim

**WIN-4 is not met.** The shipped reader is `NoAnchor`, which follows nothing, so the window
is centred rather than appearing beside the player's last window. The route is still an open
question with the user — S-2's three options, human item 4. Nothing here should be read as
ticking that requirement; what is under test is that the game *asks and uses the answer* it
is given.

## Suite state

```
.venv/bin/python -m pytest -q          →  961 passed, 0 failed, 0 skipped, 9 deselected
```

Repository root, `.venv` from `/usr/bin/python3` 3.9.6, pytest 8.4.2, on `main` at
`874e0ca` plus this branch. **WI-16b adds 36** — 16 placement and 20 assembly guard. Crash
reports **14, none new** since 02:00:51Z.

Built against **WI-14c's `anchor_reader=` seam**, which lane A shaped to the request rather
than inventing its own. Without an injectable reader none of the anchor tests could live in
the default suite at all, because plan 1.6 forbids the default suite from querying the
desktop — and a guard that does not run by default is how the placement defect survived.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
