# Scenario index

Every scenario document in this folder, what it is worth, an order to read them
in, and the ones still to be written.

## What a scenario is

The rest of `docs/` is organised by **subject**: the specification lists what the
program must do, the architecture document describes the layers, the plan says
who built what in which order, and the findings record what was measured. A
scenario is the same program described by what its parts **do together**.

One scenario is a mind-sized piece of behaviour. It is an interaction between two
and about five classes, achieving one outcome that is worth something on its own.
It is not necessarily the whole story from beginning to end — scenarios are meant
to join up, so several of them read in order describe a whole journey, and each
still stands alone.

Where a part of the program is a module of plain functions rather than a class —
and several of the most important ones are — the module is named as the
participant and said to be a module. That is not a compromise. Some of the best
reasoning in this program lives in modules with no classes in them at all.

## What the priorities mean

Every scenario document in this folder carries a priority on the line under its
headline. The priority is one of `HIGH`, `MEDIUM` or `LOW`.

A priority is not a score for how interesting the scenario is. It answers a
narrower question: **what stops working, and how often, if this piece of the
program is wrong.**

The answer depends on how the program is normally run rather than on how the code
reads. **This program is started one way and one way only:**

```
/usr/bin/python3 -m terminal_game
```

That command creates its own window — 40 characters wide and 30 rows deep, black
ground, fixed-width typeface, titled *Terminal Game* — and plays the game inside
it. There is no launcher and no second process. This is a change from the
program's previous shape: the architecture's candidate 2 was adopted, so the
application owns its window rather than dressing somebody else's, and nothing
here drives a terminal emulator through a scripting bridge.

One consequence is worth stating, because it moves several priorities. The window
and the game are the same process, so a fault anywhere in the shell layer takes
the game down with it. There is no surviving supervisor to report what happened.

| Priority | What earns it |
| --- | --- |
| `HIGH` | It happens on the path that **every painted picture** or **every tick** takes, or it is the only route by which the game can be seen, driven, or brought to an end |
| `MEDIUM` | It happens once for each game, or only when the player presses a key, or on every picture but only in a way that affects how the game *looks* rather than whether it runs |
| `LOW` | It happens only when something has already gone wrong, or only under a tool in `tools/` rather than in the game itself |

## The scenarios in this folder

| Scenario | Priority |
| --- | --- |
| [The window closes itself when the session ends, and the session learns that it did](the-window-closes-itself-when-the-session-ends-and-the-session-learns-that-it-did.md) | `HIGH` |

Fourteen more are listed under [Scenarios not yet written](#scenarios-not-yet-written).

## A reading order

Three laps. Each is a whole journey; each later lap explains something the
earlier one took for granted.

### Lap 1 — one picture, from a game state to lit pixels

The shortest path that produces something a player can see, and the one every
frame takes seven times a second.

### Lap 2 — where the arena comes from, and how a game ends

The maze, the opening position, and the ordered rules that decide a win from a
loss.

### Lap 3 — the window it all happens in, and the ways in and out

Opening it, placing it, refusing a font it cannot draw with, and closing it in a
way the session actually learns about.

## If you are here for one thing

- **"Why does the maze never have a dead end?"** — the carve-and-braid scenario.
- **"How does the ghost keep its beat?"** — the tick-timer scenario.
- **"Why is eating the last dot sometimes a loss?"** — the ordered-outcome scenario.
- **"Why does the window open at (120, 120) and not near my pointer?"** — the
  anchor scenario, and `docs/TRACEABILITY.md` §13.

## Scenarios not yet written

Fourteen of the fifteen. This index was written first, deliberately: it fixes the set and the
priorities before any of the documents exist, so that the set is something to
disagree with cheaply rather than after two hundred kilobytes have been written
against it.

| # | Scenario | Priority | Chiefly |
| --- | --- | --- | --- |
| 1 | A game state is composed into a 40 × 30 frame, with the ghost drawn last | `HIGH` | `frame_composer`, `Frame`, `picture` |
| 2 | A frame is painted onto the grid, touching only the cells that changed | `HIGH` | `CharacterGridSurface`, `Frame` |
| 3 | A wall square chooses its double-line glyph from its four neighbours | `MEDIUM` | `wall_glyphs`, `Maze` |
| 4 | The status row shows the score and the keys that still work | `MEDIUM` | `status_line` |
| 5 | A key press becomes an intent, and an unknown key becomes nothing | `HIGH` | `input_translator`, `Intent` |
| 6 | An arrow key moves the player one square and eats the dot it lands on | `HIGH` | `turn_resolver`, `GameState`, `DotField` |
| 7 | A clock tick moves the ghost, which is never told where the player is | `HIGH` | `ghost`, `turn_resolver` |
| 8 | Eating the last dot on the ghost's square is a loss and not a win | `MEDIUM` | `turn_resolver`, `Outcome` |
| 9 | The tick timer keeps the ghost's beat without drifting | `HIGH` | `TickTimer`, `cadence`, `Game` |
| 10 | A session goes Playing → Decided → Ended, and only `q` leaves it | `HIGH` | `Session`, `Phase` |
| 11 | A maze is carved into a spanning tree, then braided until no dead ends remain | `MEDIUM` | `maze_generator`, `maze_invariants` |
| 12 | A new game puts the player in the middle, the ghost far away, and a dot on every other square | `MEDIUM` | `opening_position`, `DotField` |
| 13 | A window is opened, dressed, and placed where the player was looking | `HIGH` | `WindowOwner`, `Anchor`, `Toolkit` |
| 14 | A font that is missing, substituted or not fixed-width is refused before a window opens | `MEDIUM` | `grid_surface`, `TkFontProbe` |
| ~~15~~ | ~~The window closes itself when the session ends, and the session learns that it did~~ | `HIGH` | **written** |

**Why fifteen again, and why not the same fifteen.** The previous set described
the program as it was before candidate 2 was adopted, and four of its scenarios
are about machinery that no longer exists: a launcher process, a terminal put
into raw mode and given back, a window resized under a game already drawing into
it, and a terminal too small being refused. Those are gone with the architecture
that needed them. What replaces them is the window this program owns itself — how
it is opened, placed, refused a font it cannot draw with, and closed in a way the
session actually learns about.

The domain scenarios survive almost unchanged in subject, because candidate 2
kept the Domain and Application layers exactly as candidate 1 had them. The code
behind them is new; the behaviour they describe is not.

**Number 15 is the one to write first if only one gets written.** A window
closing correctly while the session never learns it is over was found three times
in one run, in three different disguises — a close button, a swallowed crash, and
a scheduled deadline. The rule the run arrived at is worth a document of its own:
*assert the phase the session reached, not that the window closed.*
