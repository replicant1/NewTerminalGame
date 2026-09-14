# WI-3 — Terminal's `busy` flag stops telling the truth once the window has a grid

> **Superseded in one particular, and only one — pointer added by the technical lead, not by editing
> the measurement below.** WI-13 could not reproduce "the grid alone does it" and measured a 2 x 2:
> it takes **both** the grid *and* a real curses program in the tab. `sleep` with the grid told no
> lies in 8 samples; the real game with the grid lied in 8 of 9. See
> `docs/findings/WI-13-what-actually-breaks-busy.md`. **Nothing built on this finding changes** —
> every window this launcher opens has a grid and runs the real game, so the flag lies on all of
> them — but the cause stated below is incomplete, and a cause stated wrongly is how somebody later
> concludes the problem does not apply to their case.

Measured on the development machine while joining the launcher to the real game
process. macOS 25.6.0, Terminal.app, Python 3.9.6.

**The short form:** setting `number of columns` and `number of rows` on a tab —
which is exactly what WIN-2 requires, and what the launcher does to every window
it creates — makes that tab's `busy` property report **false for the entire life
of the process running in it**. Caution C2's guard ("never close a window with
something running in it") is therefore inert on every window this system opens,
and a launcher that trusts `busy` closes the window on the player mid-game.

`processes of selected tab` keeps telling the truth and is what the join uses
instead.

## What was measured

Ground truth for "is the game alive" is `pgrep -f terminalgame.game_main`, which
knows nothing about Terminal. The game was launched with `--hold 8`, so it draws
its frame and exits by itself after eight seconds.

| | game alive (pgrep) | `busy` says |
| --- | --- | --- |
| window **with** the grid set (window 7698) | +0.9 s → +8.4 s | **false from +0.9 s onwards** |
| window **without** the grid set (window 7699) | +0.7 s → +7.0 s | true +0.1 s → +7.0 s, then false |

Without the grid, `busy` tracks the process exactly. With it, `busy` goes false
at the moment the game starts and stays false for the whole eight seconds the
game is demonstrably running.

## Which setting does it

`configure_window` sets fonts, colours, the grid and the title. Each group was
applied on its own to a window running the same eight-second game, and `busy`
sampled only at moments when `pgrep` confirmed the game was alive:

| configure applied | `busy` while the game was provably alive |
| --- | --- |
| nothing (window 7700) | `Y Y Y Y Y Y Y Y Y` |
| font only (7701) | `Y Y Y Y Y Y Y Y Y` |
| colours only (7702) | `Y Y Y Y Y Y Y Y Y` |
| **grid only (7703)** | **`. . . . . . . . .`** |
| title only (7704) | `Y Y Y Y Y Y Y Y Y` |

It is the grid alone — `set number of columns` / `set number of rows`. Fonts,
colours and every `title displays …` switch are harmless.

**Ordering does not help.** Creating a blank window, setting its grid while it
was empty, and only then running the game in it (`do script … in selected tab of
window id N`) gives `busy` = false just the same. The tab is spoiled by having
been resized at all, not by being resized underneath a running process.

## What does work: the process list

`processes of selected tab of window id N`, sampled across a whole session on a
grid-configured window (window 7709, `--hold 6`):

| time | game alive | `busy` | `processes` |
| --- | --- | --- | --- |
| +0.3 s | no — shell still starting | true | `login｜-zsh｜ssh-add` |
| +1.5 s → +3.9 s | **yes** | **false** | `login｜Python` |
| +5.1 s onwards | no — game over | false | *(empty)* |

Three properties make this the right signal, and all three were measured rather
than assumed:

1. It is **accurate while the game runs**, which `busy` is not.
2. It goes **empty** when the command ends. That is a consequence of the
   launcher `exec`ing the command so the login shell is replaced rather than
   left underneath it — there is no shell to fall back to. So "empty" means
   "nothing is running in there", with no matching of process names.
3. It is **non-empty during start-up** (`login｜-zsh｜ssh-add`), so a window whose
   shell has not yet become the game is never mistaken for one whose game has
   ended. This matters: a window exists before its command does, and the gap was
   measured at most of a second.

A window that has gone away answers with an empty list, because nothing is
running in a window that no longer exists.

## Why it mattered here

Before the signal was changed, `python3 -m launcher.game` took **1.00 s whether
the game was asked to hold its frame for 5 seconds or for 12** — the launcher
found the window "not busy" immediately and closed it, killing the game during
the login shell's start-up. It reported `window 7684 closed` and exit status 0
while the player had seen nothing at all.

Afterwards, with the process list as the signal: `--hold 5` takes 6.13 s and
`--hold 12` takes 12.92 s. The 7-second difference in the hold shows up as a
6.79-second difference in the session, which is the evidence that the game
really runs for as long as it was told to.

## What this does not settle

`WindowLauncher.run` and `Desktop.is_busy` still use the `busy` flag, and every
window `run` opens is grid-configured, so `run` has this defect. WI-3 did not
change it, because WI-1 pinned that contract with tests and the fix is a
decision above this work item. The new signal is additive: `wait_until_idle` and
`reap` take a `still_running` argument, defaulting to the old behaviour, and the
join passes `WindowLauncher.has_live_processes`. **This needs a ruling** — see
the WI-3 PR summary.

No modal sheet was ever raised during any of this, and none was expected:
Terminal does not prompt for a window it believes is not busy. The damage from
the false reading is not a blocked automation call, it is a game killed under
the player. That is the opposite way round from what caution C2 anticipated, and
it is worth knowing.
