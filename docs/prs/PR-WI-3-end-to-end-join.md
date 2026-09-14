# WI-3 — the end-to-end join

**Branch** `wi-3-end-to-end-join`, cut from `main` at `5269b67`.
**Lane** A (DEV-A). **Local mode** — this file stands in for the pull request.
**Depends on** WI-1 and WI-2, both already on `main`.

The launcher opens a window running the real game process; the game runs in it;
the game exits on `q`; the launcher confirms nothing is running any more and
closes the window by the identity it captured. Nothing is left on the desktop.

Run it with `python3 -m launcher.game`.

## What is new

| File | What it is |
| --- | --- |
| `launcher/game.py` | The join. The shell command that runs the real game, as text, and the entry point that plays a whole session. |
| `launcher/script.py` | One new builder, `window_processes` — asks what is running in the captured window. |
| `launcher/desktop.py` | `Desktop.processes(window_id)` — the typed side of it. |
| `launcher/lifecycle.py` | `has_live_processes`, and a `still_running` argument on `wait_until_idle` and `reap`. Additive: the default is exactly the old behaviour. |
| `tests/test_game_command.py` | 19 tests on the command text. |
| `tests/test_end_to_end_join.py` | 24 tests on the join. |
| `tests/test_launcher_script.py` | One line: registering the new builder with WI-1's existing rules. |

Findings: `WI-3-busy-is-false-after-a-grid-resize.md`,
`WI-3-configure-startup-race.md`, `WI-3-the-join-measured-end-to-end.md`.

## The headline: the launcher was killing the game, and reporting success

The first real run against the real desktop was a **false green**. `python3 -m
launcher.game` printed `window 7684 closed` and exited 0 — and a whole session
took **1.00 s with `--hold 5` and 0.98 s with `--hold 12`**. The hold made no
difference because the game never ran. The launcher's success signal reports on
the window, not on what was in it.

Ground truth came from `pgrep`, which knows nothing about Terminal:

| | game alive (pgrep) | tab's `busy` says |
| --- | --- | --- |
| window **with** its grid set | +0.9 s → +8.4 s | **false from +0.9 s onwards** |
| window **without** its grid set | +0.7 s → +7.0 s | true +0.1 s → +7.0 s |

Bisecting `configure` by group: font, colours and every `title displays …`
switch are harmless. **It is `set number of columns` / `set number of rows`
alone** — and WIN-2 requires exactly that, so it is true of *every* window this
system opens. Sizing the window before running the game in it does not help
either; the tab is spoiled by having been resized at all.

So **caution C2's guard is inert on every window the launcher creates.** No
modal sheet was ever raised and none was expected — Terminal does not prompt for
a window it believes is idle. The damage runs the opposite way from what C2
anticipated: not a blocked automation call, but a game killed under the player.

`processes of selected tab` keeps telling the truth — `login|-zsh|ssh-add`
during start-up, `login|Python` while playing, **empty** once the game has gone.
Empty is unambiguous and needs no matching of process names, because the
launcher `exec`s the command so no shell is left underneath it. Being non-empty
during start-up also closes the start-up gap for free.

## What proves it works now

| asked for | session took |
| --- | --- |
| `--hold 5` | 6.13 s |
| `--hold 12` | 12.92 s |

A 7-second difference in the hold shows up as a 6.79-second difference in the
session — which a killed game cannot do. The ~1 s fixed overhead is window
creation, configure, measure, move and the final close; the 0.21 s residual is
0.1 s polling granularity and scheduling noise, systematic of nothing.

The frame really reaches the glass — read back from a live window with `contents
of selected tab`, the whole 40 x 30 picture: walls, title, dots, the player
glyph, the ghost glyph, the status line.

And the `q` path, which a hold expiry does not demonstrate, measured separately:
a game given a **30-second** hold, sent `q` at +2.76 s, **gone at +2.90 s** —
0.14 s later, 27 seconds early — then the window closed by its captured id. The
`q` was delivered with `do script "q" in selected tab of window id N`, which
writes to that one tab and so needs no focus stealing and injects no keystroke
into whatever the person at the machine is looking at.

## The command the window runs

```
/bin/sh -c 'i=0; while [ $i -lt 60 ]; do set -- $(stty size 2>/dev/null); \
  if [ ${1:-0} -ge 30 ] && [ ${2:-0} -ge 40 ]; then break; fi; \
  i=$((i+1)); sleep 0.1; done; cd <repo root> || exit 1; \
  exec <python> -m terminalgame.game_main --hold 5'
```

Four decisions in there, none of them free:

- **The game is named as a string and never imported.** Plan §3 — the launcher
  process shares no code with the game. There is a test that reads
  `launcher/game.py` and asserts it imports nothing from `terminalgame`.
- **It changes to the repository root**, because the window runs a fresh login
  shell in the player's home, where `python3 -m terminalgame.game_main` finds
  nothing. `|| exit 1` so a root that cannot be entered stops rather than
  starting the game somewhere arbitrary.
- **`exec` at every hop.** `script.open_window_running` already prefixes `exec`
  so the login shell is replaced rather than left alive underneath; the inner
  `exec` does the same for `/bin/sh`. That is what makes the process list go
  *empty* — rather than falling back to a shell — when the game ends.
- **A bounded size gate.** `configure` sets the window to 40 x 30 only *after*
  `do script` has already started the command, and an untouched profile opens at
  80 x 24 — three rows short of what the game requires, and the game checks its
  size once, at curses start-up, and fails loudly. Measured, `configure` lands
  0.496 s before the game can first look, so the race is currently won — but by
  login-shell start-up latency, which is an accident of this machine. The gate
  waits for the size the launcher asked for, is bounded at 60 × 0.1 s, and
  **always falls through**, so a genuinely too-small screen still reaches the
  game's own loud failure rather than being suppressed.

`stty size` reports **rows first**, which is the easy thing to get backwards;
there is a test that passes distinct values for rows and columns to check which
comparison each lands in.

## `--hold` is passed explicitly, at 5 seconds

The game's own default is 3 s and the launcher could inherit it. It does not:
how long a window sits on the player's desktop is a decision this join should
make out loud. Five seconds because someone watching needs long enough to read
the frame and press `q` — the path WIN-5 and END-6 are about — while an
unattended run still ends promptly. Scaffolding either way: WI-11 replaces the
skeleton with the real loop, which ends when the player ends it and not on a
timer.

## Deviations and things needing a ruling

**1. `WindowLauncher.run` still has the defect. This is the ruling I need.**

What I changed: `wait_until_idle` and `reap` now take a `still_running`
argument. What I left alone: **it defaults to `self.desktop.is_busy`, which is
exactly the old behaviour**, so WI-1's contract and all 107 of its tests are
untouched and `run` behaves today precisely as it did before. `launcher/game.py`
passes `WindowLauncher.has_live_processes` instead, so only the join is fixed.

The ruling is between two options, and it is not mine to take:

- **(a) Leave `run` as it is.** `python3 -m launcher <command>` keeps a known
  defect — it will close any window whose command is still running, because
  every window it opens is grid-configured. Nothing on `main` depends on `run`
  today except WI-1's own tests and entry point.
- **(b) Make `busy` no longer the default**, i.e. switch `run`, and with it
  `Desktop.is_busy`, over to the process list. That is the correct end state in
  my view, but it rewrites a contract WI-1 measured and pinned, and it changes
  the AppleScript text that `tests/test_launcher_script.py` asserts on. It is a
  plan-level decision, and §11.2 already points WI-13 at "a revisit of the
  C2/C3 resolution against a real failing launch", which is exactly this.

I did not take (b) unilaterally because it is another work item's pinned
contract. My recommendation is (b), routed through WI-13.

**2. The failure path inside `WindowLauncher.open` still asks `busy`.** When
setup fails after the window exists, `open` calls `self.reap(window_id,
self.failure_timeout)` with no `still_running`, so it uses the unreliable flag.
I left it alone for the same reason as above. In practice it is the benign
direction — on a failed launch, closing is what you want, and Terminal raises no
sheet for a window it thinks is idle — but it is part of the same ruling.

**3. I added a builder to `launcher/script.py` and a line to
`tests/test_launcher_script.py`.** WI-1's
`test_every_public_builder_in_the_module_is_covered_by_these_rules` caught the
new `window_processes` builder and required it to be registered. That guard did
exactly its job; the new builder passes the by-id and boundedness rules with the
rest. Flagging it because it is a touch on another work item's test file.

**4. `launcher/game.py` does not reuse `launcher/__main__.py`.** It did at
first, but `__main__.main` calls `launcher.run(command)`, which is the defective
path. The join composes `open` → `reap(still_running=…)` itself. The exit codes
and the reporting are WI-1's, restated rather than delegated.

## Assumptions, not rulings

- **A1** (WIN-5 against END-5/END-6) is what this join implements: the game ends
  on `q` and the launcher then closes the window by itself. That is the plan's
  assumption and it is **not** recorded here as settled. Flipping it moves one
  signal inside the loop and does not disturb the join.
- **A2** — the Automation/Accessibility permission was available throughout;
  every measurement above depended on it. I cannot grant or verify it.
- **A3** — the system terminal, per window, saved preferences untouched. Nothing
  here installs a profile or changes a global setting. **WIN-3 is not verified
  and is not recorded as verified.**

The two cautions pull the way §11.3 says: where C2 and C3 disagree, C2 wins. A
window still running something is left open and its id named, and the join has
tests for both halves of that.

## Suite

`python3 -m unittest discover` from the repository root: **238 tests, 0 failed,
0 skipped.** Baseline on `main` at `5269b67` was 191, so this adds 43 — 19 on
the command text, 24 on the join. No existing test was changed except the one
registration line described above.

Mutation checks: **not applicable — mutation checking is prohibited on this
project** (plan §4.4).

## Windows

**29 opened, 29 closed** across every measurement and every real run. The census
metric is `every window whose visible is true`; `id of every window` is not
usable, because Terminal keeps a window object addressable after a close and it
was measured reporting one the launcher had already closed. Final visible census
`7104` — the user's own session, exactly where it started.

## What needs a human

1. **The `q` I sent arrived as terminal input, not from a keyboard.** It proves
   the read-key path, the quit condition and the launcher's response. It does
   not prove a real keypress reaches the same code. Run `python3 -m
   launcher.game --hold 30`, press `q`, and check the window closes by itself
   within a second or so.
2. **WIN-2's appearance** — whether Menlo 14 on black is "large enough to read
   comfortably", and whether the frame looks right. Only a person at the screen
   can say.
3. **WIN-3's title bar** still reads `rodneybailey — Terminal Game — <command>`.
   Two components cannot be cleared without changing the player's saved profile,
   which A3 forbids. Unchanged by WI-3 and still on WI-14b's list.
4. **The Automation/Accessibility permission** was already granted on this
   machine. Its first-run behaviour on a machine where it has not been granted
   is untested here.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
