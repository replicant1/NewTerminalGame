# Code review 1 — the Python in this repository

Reviewed 2026-09-15 against `main` at `3937cde`. Scope: all 4,818 lines of
production Python across `terminalgame/`, `launcher/` and `acceptance/`, read in
full, plus a structural pass over the 9,513 lines of tests. Every finding below
was reproduced against the code rather than inferred from reading it; the repro
is given with each one.

The suite was green throughout: 730 tests, 0 failures.

## Status

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | The acceptance pack leaks a window when `configure` fails | high | **Fixed** — [PR #18](https://github.com/replicant1/NewTerminalGame/pull/18) |
| 2 | `target_position`'s stated guarantee is not a guarantee | medium | Open |
| 3 | `game.play` duplicates `WindowLauncher.run`, with a stale docstring | medium | **Fixed** — [PR #20](https://github.com/replicant1/NewTerminalGame/pull/20) |
| 4 | Two docstrings describe work items that have since landed | low | **Fixed** — [PR #20](https://github.com/replicant1/NewTerminalGame/pull/20) |
| 5 | The launcher polls the desktop with a subprocess ten times a second | medium | Open |
| 6 | The pack's copy of `_bounded` dropped a guard | low | Open |
| 7 | Smaller things | low | Open |

Findings are recorded as they stood at the time of review. Where one has since
been fixed the original account is left intact — it is the reason the change was
made — and what was done is stated under the heading.

## Summary

This is good code. The hexagonal layering is real rather than aspirational and
`tests/test_layering.py` enforces it with 32 tests that include meta-tests
checking the scan itself can still detect a violation. The domain is immutable,
pure, and seeded through a single injected random source. Requirement codes are
traced from the specification into the docstrings and back out into test names.
The two hard-won operational lessons of the run — that `busy` lies for a window
with a grid, and that a window must never be closed with a live process in it —
are both written down where the next reader will hit them.

Seven findings follow. One was a defect that leaked a terminal window onto the
user's desktop; it has since been fixed, along with the duplication and the two
stale docstrings. What remains open is a documented guarantee the code does not
provide, one efficiency problem, and cleanup. None of them is in the game's
domain logic, which I could not fault.

---

## 1. The acceptance pack leaks a window when `configure` fails

**`acceptance/pack.py:177-183`** — severity: high — **FIXED**

> **Fixed** in [PR #18](https://github.com/replicant1/NewTerminalGame/pull/18),
> commit `ac85181`. What follows describes the defect as it stood at review;
> what was done about it is at the end of the section.

`WindowUnderTest.__enter__` creates the window, then configures it, then returns
`self`:

```python
def __enter__(self):
    self.opened_at = self.clock()
    self.window_id = self.desktop.open_window_running(self.command)   # window now exists
    self._note("window %d created" % self.window_id)
    self.desktop.configure(self.window_id)                            # can raise
    self._note("configured")
    return self
```

Python calls `__exit__` only if `__enter__` returns normally. So if `configure`
raises — a refused Automation permission, a timeout, a window the desktop will
not address — the window has been created and nothing will ever reap it. The
class docstring at `acceptance/pack.py:156-163` says the opposite: *"captures
the id at the moment of creation and closes it in a `finally`, so a failure
anywhere inside cannot leave one behind."*

Reproduced with a runner that answers `open_window_running` and then fails
`configure_window`:

```
raised: the desktop refused to configure it
calls made: ['open_window_running', 'configure_window']
was the window closed?  False
window.abandoned = None
```

`abandoned` staying `None` is the second half of the problem. The
`*** WINDOW n WAS LEFT OPEN ***` banner in `acceptance/__main__.py:67-74` is
driven by that attribute, so the user is not told either — `pack.run` just
propagates the error and the window sits there.

`launcher/lifecycle.py:165-182` gets this exactly right for the same two calls,
and the pack should copy it:

```python
window_id = self.desktop.open_window_running(command)
try:
    self.desktop.configure(window_id)
    ...
except BaseException as cause:
    raise LaunchFailed(cause, window_id, self.reap(window_id, self.failure_timeout)) from cause
```

**Fix:** wrap everything after `open_window_running` in `__enter__` in
`try/except BaseException`, call `self.reap()` and set `self.abandoned` before
re-raising.

### What was done

Two changes, and the second is why the first can be relied on:

- **`__enter__` reaps for itself.** Everything after the window exists is
  wrapped; on any failure it reaps, then re-raises.
- **`reap` catches `BaseException` rather than only `AutomationError`**, as
  `WindowLauncher.reap` already does. A reap runs on the failure path, so an
  exception of its own would bury the failure it was called to clean up after.
  `AutomationError` is the expected way in; the point is that nothing else
  escapes either. Without this, the reap `__enter__` now depends on could
  replace the real diagnosis with a worse one.

Three regression tests in `TheWindowIsReapedByConstruction`, **each confirmed
failing against the code as reviewed** — verified by reverting the fix and
re-running, not by assertion:

| Test | Asserts |
|---|---|
| `test_a_failure_while_configuring_still_closes_the_window` | `close_window` is called, naming the captured id |
| `test_and_the_configure_failure_is_the_one_that_comes_out` | the `AutomationError` still reaches the caller even when the reap itself falls over, and the abandoned window is recorded |
| `test_a_configure_failure_over_a_live_game_names_the_window_it_left` | a window with a live game is left open and **named** — caution C2 still beats C3 on this path |

```
fix reverted:  FAILED (failures=3)
fix applied:   OK
whole suite:   Ran 733 tests — OK   (730 before, +3)
```

One test-helper change came with it: `happy_path()` was lifted out of `build()`
in `tests/test_acceptance_pack.py`. The new tests construct their own runner,
and `RecordingRunner` *consumes* list replies, so passing the module-level
`HAPPY_PATH` drains it and every later test sees an empty queue. `build`'s
docstring warned about exactly this and the first attempt walked into it anyway,
turning four unrelated tests red. The warning is now a function.

---

## 2. `target_position`'s stated guarantee is not a guarantee

**`launcher/geometry.py:99-125`** — severity: medium

The docstring says of rule 2:

> 2. Do not let that carry the new window's top-left corner outside the
>    reference window's own frame. […] **This is the only part of the placement
>    that is a *guarantee* rather than a best effort, and it is what WIN-4's
>    "so it always lands visible" rests on.**

Rule 3 runs afterwards and can move the corner straight back out of that frame:

```python
x = min(x, reference.left + max(reference.width - 1, 0))   # rule 2
x = min(x, screen.right - size.width)                      # rule 3 — can undo it
```

This is not hypothetical, and the suite's own data hits it. From
`tests/test_launcher_geometry.py:47`:

```
screen    = Rect(0, 0, 1440, 900)
reference = Rect(1300, 800, 1440, 900)
size      = 357 x 558
landed at Point(x=1083, y=342)   inside reference frame? False
```

1083 is 217 points to the *left* of the reference window. The test asserts the
coordinates and that the point is on screen — it never asserts the frame
containment that the docstring calls the guarantee. The one test that does
assert it, `test_the_offset_never_leaves_the_reference_windows_own_frame` at
line 71, uses a 5120 x 2422 screen where rule 3 is inert, so it cannot catch
the override.

The behaviour is defensible: the window lands on screen, which is what a player
cares about. What is wrong is the claim. The real guarantee is rule 3's clamp to
the screen rectangle, and `visible_screen_bounds` is documented at
`launcher/script.py:129-139` as *"the union of them all, so it is an outer
bound rather than a guarantee of visibility — measured […] a rectangle much of
which is over no display at all"*. So the two modules point at each other: the
script says the guarantee comes from the reference window, the geometry's
behaviour says it comes from the screen, and neither is unconditionally true.

**Fix:** either state the real precedence in the docstring (rule 3 wins, and
frame containment is best-effort), or apply rule 2 last so it holds. Do not
leave the claim standing as written. Whichever way it goes, add a test at the
bottom-right case that asserts the property the docstring picks.

---

## 3. `game.play` duplicates `WindowLauncher.run`, and its docstring explains a difference that no longer exists

**`launcher/game.py:151-172`** — severity: medium — **FIXED**

> **Fixed** in [PR #20](https://github.com/replicant1/NewTerminalGame/pull/20). What follows describes the duplication as it
> stood at review; what was done is at the end of the section.

The two are now behaviourally identical:

```python
# WindowLauncher.run
window = self.open(command)
return self.reap(window.window_id, self.session_timeout)

# game.play
window = launcher.open(command)
return launcher.reap(window.window_id, launcher.session_timeout,
                     still_running=launcher.has_live_processes)
```

`reap` passes `still_running` through to `wait_until_idle`, which defaults it to
`self.has_live_processes` (`launcher/lifecycle.py:217-218`). Passing it
explicitly changes nothing.

`play`'s docstring still says:

> This is `WindowLauncher.run` with one difference, and the difference is the
> whole of WI-3's risk. `run` decides the game has finished by asking the tab
> whether it is `busy` […] So `run` closes the window while the player is still
> playing.

That was true before WI-13. It is not true now: `window_is_busy` was deleted
outright (`launcher/script.py:272-278`) and `run`'s own docstring at
`launcher/lifecycle.py:139-150` correctly describes waiting on the process list.
So the file warns a reader away from a function that is now the right one, on
grounds that were removed two work items ago.

This matters more than an ordinary stale comment, because the `busy` defect is
the one the project most needs future readers to understand, and a wrong account
of it in the seam module is where they will meet it first.

**Fix:** delete `play` and call `launcher.run(command)` from `game.main`, moving
anything worth keeping from the docstring onto `run`. If `play` is kept as a
named seam, rewrite the docstring to say it is `run` under a local name.

### What was done

`play` is deleted. `game.main` calls `launcher.run(command)`, which is what
`launcher/__main__.py` already did — so both entry points now take one route
into the launcher instead of two.

One paragraph of `play`'s docstring was worth keeping and is not stated
anywhere else, so it moved onto `run`: that an empty process list is
unambiguous because `open_window_running` `exec`s the command and leaves no
login shell alive underneath it, and that this covers the start-up gap for free
— a window whose login shell has not finished starting lists that shell, so it
is never mistaken for one whose game has ended. A short note on `run` records
that the copy existed and why, so the next reader meets the history rather than
rediscovering it.

The 20 call sites in `tests/test_end_to_end_join.py` now call
`launcher.run(game_command())`. Every assertion is unchanged, and the coverage
improves: the class that pins the `busy` defect
(`TheGameIsNotInterruptedWhileItIsBeingPlayed`) now exercises the production
path rather than a copy of it.

Nothing was lost by deleting the function: `WindowLauncher.run` is directly
tested at ten call sites in `tests/test_launcher_lifecycle.py`.

---

## 4. Two docstrings describe work items that have since landed

Severity: low — **FIXED** in [PR #20](https://github.com/replicant1/NewTerminalGame/pull/20) — but both sat in module headers
where they are read first.

- **`terminalgame/presentation/frame_builder.py:56-62`** — *"Row 29 is a seam,
  not this module's row […] **WI-6 has not landed yet**, so `compose` leaves row
  29 blank unless a caller hands it a status line."* WI-6 landed;
  `terminalgame/presentation/status_line.py` exists and `game_main.build_frame`
  passes its output in. The mechanism described is still correct — the row is
  still optional — but "has not landed yet" is false.

- **`acceptance/pack.py:360-366`** — *"on `main` the game process is still M0's
  walking skeleton and the real one arrives with WI-12, so an exercise that
  pinned today's frame would pass now and fail the moment the game it is meant
  to check turns up."* WI-12 landed (`de576a2`). The reasoning for not pinning a
  fixed picture may still hold, but it now needs a different reason, and as
  written it tells a reader the pack is checking a skeleton.

**Fix:** both are one-sentence edits. Worth doing together with finding 3, since
all three are the same class of rot.

### What was done

Both rewritten, and in each case the design point the stale sentence was
carrying is kept rather than deleted with it:

- **`frame_builder.py`** now records that WI-6 landed and that nothing here had
  to change when it did, which was the point of cutting the seam that way. The
  trap is spelled out where a caller will meet it: a frame with a blank row 29
  is well-formed and passes every test in the module, so forgetting the status
  line fails STAT-1 *silently* — which is why `build_frame` is a named function
  with a test of its own.
- **`pack.py`** now gives a reason for not pinning a fixed picture that outlasts
  the skeleton: the pack runs `game_command()` with **no seed**, so MAZE-4 gives
  it a different maze every run and there is no fixed frame to pin. Seeding it
  would buy one at the price of no longer exercising the real command as a
  player gets it. Shape is what SCRN-1 states and what holds for every maze.

---

## 5. The launcher polls the desktop with a subprocess ten times a second, for the life of the game

**`launcher/lifecycle.py:42, 209-229`** — severity: medium (efficiency)

`POLL_INTERVAL = 0.1`, and `wait_until_idle` calls `has_live_processes` →
`Desktop.processes` → `OsascriptRunner.run` → `subprocess.run(['/usr/bin/osascript', '-'])`
each time round. Every poll is a process spawn plus an Apple event to Terminal.

Measured on this machine, a *trivial* `osascript` round trip with no Apple event
at all costs 36 ms. The real call is an Apple event to Terminal asking for
`processes of selected tab`, so it is strictly slower. That gives a loop period
of at least 136 ms, of which at least a quarter is spent in `osascript`:

```
a 10-minute game  = ~6,000 osascript spawns, ~215 s of subprocess time
SESSION_TIMEOUT   = 4 hours = 144,000 spawns worst case
```

A game lasts as long as the player wants it to — that is the explicit design of
`UNTIL_THE_PLAYER_QUITS` — so this runs for the whole session, not for a
start-up window. It burns roughly a third of a core alongside the game it is
watching, and it sends Terminal an Apple event every seventh of a second while
the player is trying to play in it.

Nothing needs a tenth of a second here. The question being asked is "has the
player quit yet", and a person notices nothing if the window closes half a
second after they press `q`.

**Fix:** give `wait_until_idle` a backoff — poll fast for the first second or
two while the process list is still filling, then settle to 0.5 s or 1 s. The
pack's own `POLL` (`acceptance/pack.py:51`) has the same value and the same
justification available, but its waits are bounded at 15 s so it matters far
less there.

---

## 6. The pack's copy of `_bounded` dropped the guard the launcher's has

**`acceptance/pack.py:71-78`** vs **`launcher/script.py:88-92`** — severity: low

```python
# launcher/script.py
return "with timeout of %d seconds\n%s\nend timeout" % (max(1, int(math.ceil(timeout))), source)

# acceptance/pack.py
return "with timeout of %d seconds\n%s\nend timeout" % (int(timeout), body)
```

The launcher rounds *up* and floors at 1. The pack truncates. Any timeout below
1.0 second becomes `with timeout of 0 seconds`, and any fractional timeout is
silently shortened. Nothing calls it that way today — every caller takes the
`CALL_TIMEOUT = 10.0` default — so this is latent rather than live.

The pack's docstring explains the duplication: *"The pack writes its own rather
than importing the launcher's private helper: it depends on the launcher's
public vocabulary and none of its internals."* That is a reasonable boundary to
hold. The copy just has to be a faithful one.

**Fix:** `max(1, int(math.ceil(timeout)))`, matching the original.

---

## 7. Smaller things

| Where | What |
|---|---|
| `terminalgame/domain/maze.py:23` | `Iterable, Iterator, List, Sequence, Tuple` imported; none used. The module carries no annotations. |
| `acceptance/pack.py:42` | `Point` imported from `launcher.geometry`; unused (`Size` is used). |
| `terminalgame/screen/curses_adapter.py:147-148` | `if 0 <= code < 256: return Key.printable(chr(code))` labels every byte as printable, including control codes — ESC arrives as `Key.printable('\x1b')` with `is_printable` true. Harmless today (only `q`/`Q` are consulted, and `direction_of` returns `None` for anything unmapped), but the predicate does not mean what it says, and the same branch turns each byte of a multi-byte UTF-8 key into its own Latin-1 `Key`. |
| `terminalgame/domain/rules.py:112-118` | `advance_ghost`'s docstring: *"It also returns the same state when the ghost was told to stay where it is […] Every other step in the Domain returns the state it was given when nothing happened; this makes that convention hold without exception."* It returns `settle(state)`, which returns a **new** object when the outcome has changed — e.g. a stationary ghost that the player has just walked into returns a fresh `CAUGHT` state. That is the correct behaviour; the "without exception" is what is wrong, and the loop's redraw argument at `application/loop.py:47-51` cites this convention by name. |
| `terminalgame/presentation/frame_builder.py:131-145` | `compose` builds a fixed 40 x 30 `Frame` and never checks the maze fits it. A maze wider than 19 or deeper than 29 fails with a raw `IndexError` from `Frame.put`, where every other "this argument makes the requirement impossible" case in the codebase raises a named error naming the requirement (plan §11.8 — `NotAWallSquare`, `StatusLineWillNotFit`, `NoCorridorToStartOn`, `MazeTooSmall`). |
| `acceptance/__main__.py:29-37` | `--list` is declared and never read; the branch tests `not arguments.run`. Benign, since `--list` is the default, but `--run --list` runs. |
| `launcher/lifecycle.py:179` | `except BaseException as cause` converts a `KeyboardInterrupt` during launch into a `LaunchFailed`, which `game.main` turns into exit code 1. Reaping the window first is right; swallowing the interrupt's identity is a side effect worth a comment at least. |

---

## The tests

9,513 lines against 4,818, a ratio of about 2:1. The shape is healthy: 648
`assertEqual` against 105 `assertTrue`, so the suite mostly asserts values
rather than truthiness.

Two things stand out as better than usual:

- **`tests/test_layering.py` tests its own scanner.**
  `test_the_scan_can_see_the_imports_it_is_looking_for`,
  `test_the_dependency_scan_can_tell_the_domain_from_the_rest`,
  `test_the_random_scan_can_tell_a_shared_generator_from_an_owned_one`,
  `test_the_standard_library_check_can_tell_the_difference` and
  `test_the_import_scan_sees_what_it_is_looking_for` all exist to prove the
  architecture tests would fail if the architecture broke. That is the failure
  mode most architecture tests have, and it is closed here.

- **`acceptance/checks.py` has no "passed" field.** Not set to `False` —
  absent. A human check cannot be recorded as verified because there is nowhere
  to write it. That is a structural answer to a governance problem.

One gap, which was finding 1's other half: there was no test that
`WindowUnderTest` reaps a window when `configure` fails.
`tests/test_acceptance_pack.py` stubbed `configure_window` to `"ok"` and never
exercised the failure path, which is why the leak was there — the launcher's
equivalent path *is* tested, in
`tests/test_launcher_lifecycle.py:255`. **Closed** by the three tests listed
under finding 1.

---

## What I could not fault

The domain. `maze.py`, `player.py`, `rules.py`, `game_state.py`,
`ghost_policy.py` and `maze_generator.py` were read line by line and I found
nothing wrong with any of them. Particular things worth keeping:

- **END-3's ordering** is isolated in one named function (`rules.outcome_of`)
  with the reversal case — last dot eaten on the ghost's square — written into
  the docstring as the single state that distinguishes right from wrong.
- **GHOST-4 is enforced by the signature.** `choose_heading` and `ghost_move`
  do not take the player's position, so "the ghost takes no notice of the
  player" is checkable in one line rather than being a promise.
- **MAZE-2 and MAZE-3 fall out of the odd lattice** rather than being measured
  over a sample of mazes. The 2x2 argument in `maze_generator.py:13-22` is
  correct: one of the four squares in any 2x2 block has both coordinates even,
  and no pass ever opens one.
- **`nearest_to_centre` doubles the coordinates** to keep an even-width grid's
  half-square centre in exact integers, and ties break in reading order stated
  in the key rather than inherited from iteration order.
- **`next_deadline`** is correct catch-up arithmetic: after the adjustment the
  deadline exceeds `now` by `tick - r` where `r = (now - deadline) mod tick`, so
  it never fires a burst and never falls behind.
- **`joins_up_with` vs `maze.is_wall`** are two questions one word apart, with
  the difference written down and an instruction not to unify them. That comment
  will save somebody an afternoon.

## Suggested order

- ~~Finding 1 — it puts a window on the user's desktop that nothing closes.~~
  **Done**, [PR #18](https://github.com/replicant1/NewTerminalGame/pull/18).
- ~~Findings 3 and 4 — one pass over the duplication and the stale docstrings.~~
  **Done**, [PR #20](https://github.com/replicant1/NewTerminalGame/pull/20).

What is left, in the order I would take it:

1. Finding 2 — decide which rule is the guarantee, then make doc, code and test
   agree. It is the last finding where the code and its own documentation
   disagree about something load-bearing.
2. Finding 5 — a backoff in `wait_until_idle`.
3. Findings 6 and 7 as cleanup.
