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
| [A game state is composed into a 40 × 30 frame, with the ghost drawn last](a-game-state-is-composed-into-a-40-by-30-frame-with-the-ghost-drawn-last.md) | `HIGH` |
| [A frame is painted onto the grid, touching only the cells that changed](a-frame-is-painted-onto-the-grid-touching-only-the-cells-that-changed.md) | `HIGH` |
| [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` |
| [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` |
| [A key press becomes an intent, and an unknown key becomes nothing](a-key-press-becomes-an-intent-and-an-unknown-key-becomes-nothing.md) | `HIGH` |
| [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` |
| [A clock tick moves the ghost, which is never told where the player is](a-clock-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` |
| [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` |
| [The tick timer keeps the ghost's beat, and stops cleanly when a tick ends the game](the-tick-timer-keeps-the-ghosts-beat-and-stops-cleanly-when-a-tick-ends-the-game.md) | `HIGH` |
| [A session goes Playing → Decided → Ended, and only `q` leaves it](a-session-goes-playing-to-decided-to-ended-and-only-q-leaves-it.md) | `HIGH` |
| [A maze is carved into a spanning tree, and then braided until no dead ends remain](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` |
| [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` |
| [A window is opened, dressed, and placed where the player was looking](a-window-is-opened-dressed-and-placed-where-the-player-was-looking.md) | `HIGH` |
| [A font that is missing, substituted or not fixed-width is refused before a window opens](a-font-that-is-missing-substituted-or-not-fixed-width-is-refused-before-a-window-opens.md) | `MEDIUM` |
| [The window closes itself when the session ends, and the session learns that it did](the-window-closes-itself-when-the-session-ends-and-the-session-learns-that-it-did.md) | `HIGH` |

All fifteen are written.

## A reading order

Three laps, 56 minutes in all. Each is a whole journey; each later lap explains something the earlier one took for granted.

### Lap 1 — one picture, from the thing that caused it to lit pixels

**21 minutes.** The six documents that describe the path every picture takes. Nothing here is optional and nothing here is unusual: this is the game running normally.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [The tick timer keeps the ghost's beat, and stops cleanly when a tick ends the game](the-tick-timer-keeps-the-ghosts-beat-and-stops-cleanly-when-a-tick-ends-the-game.md) | `HIGH` | 3 min |
| 2 | [A key press becomes an intent, and an unknown key becomes nothing](a-key-press-becomes-an-intent-and-an-unknown-key-becomes-nothing.md) | `HIGH` | 3 min |
| 3 | [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` | 3 min |
| 4 | [A clock tick moves the ghost, which is never told where the player is](a-clock-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` | 4 min |
| 5 | [A game state is composed into a 40 × 30 frame, with the ghost drawn last](a-game-state-is-composed-into-a-40-by-30-frame-with-the-ghost-drawn-last.md) | `HIGH` | 4 min |
| 6 | [A frame is painted onto the grid, touching only the cells that changed](a-frame-is-painted-onto-the-grid-touching-only-the-cells-that-changed.md) | `HIGH` | 4 min |

Read them in this order rather than any other. The first is the beat everything else hangs off; the middle four are the two things that can change a game — a key and a tick — and the last two are one story in two halves, building a picture and then putting it on the glass.

At the end of this lap you can follow any picture in the game from the thing that caused it to the pixels it becomes. You will also have met the rule the whole design turns on: **the part that knows a key was pressed never learns what it means, and the part that knows what it means never learns there is a window.**

### Lap 2 — how that picture is drawn, and where the arena comes from

**19 minutes.** Lap 1 took two things for granted: that the maze exists, and that its squares know how to be drawn. This lap is both, and it ends on the rule that decides a game.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` | 4 min |
| 2 | [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` | 3 min |
| 3 | [A maze is carved into a spanning tree, and then braided until no dead ends remain](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` | 4 min |
| 4 | [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` | 4 min |
| 5 | [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` | 4 min |

The first two finish the picture — the glyph a wall chooses, and the row beneath the maze. The next two build the arena. The last is the one to read slowly: it turns on the order of two lines, and on a decision made in the document before it without which the requirement would be unreachable.

At the end of this lap you know why a maze never has a dead end, why the ghost starts on a dot, and why eating the last one is sometimes a loss.

### Lap 3 — the window it all happens in, and the ways out of it

**16 minutes.** The program owns its own window, which is the largest change from the architecture this one replaced. These four are that window's whole life.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [A window is opened, dressed, and placed where the player was looking](a-window-is-opened-dressed-and-placed-where-the-player-was-looking.md) | `HIGH` | 4 min |
| 2 | [A font that is missing, substituted or not fixed-width is refused before a window opens](a-font-that-is-missing-substituted-or-not-fixed-width-is-refused-before-a-window-opens.md) | `MEDIUM` | 3 min |
| 3 | [A session goes Playing → Decided → Ended, and only `q` leaves it](a-session-goes-playing-to-decided-to-ended-and-only-q-leaves-it.md) | `HIGH` | 4 min |
| 4 | [The window closes itself when the session ends, and the session learns that it did](the-window-closes-itself-when-the-session-ends-and-the-session-learns-that-it-did.md) | `HIGH` | 5 min |

The order is chronological: the window is placed, the font it will draw with is checked, the game inside it runs its three phases, and it closes.

The last is the one to read if you only read one thing in this folder. A window closing correctly while the session never learns it is over was found three times in one run, in three disguises, and the rule it produced — *assert the phase the session reached, not that the window closed* — is the most transferable thing this program has to say.
## If you are here for one thing

- **"Why does the maze never have a dead end?"** — [the carve-and-braid scenario](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md).
- **"How does the ghost keep its beat?"** — [the tick-timer scenario](the-tick-timer-keeps-the-ghosts-beat-and-stops-cleanly-when-a-tick-ends-the-game.md).
- **"Why is eating the last dot sometimes a loss?"** — [the ordered-outcome scenario](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md).
- **"Why does the window open at (120, 120) and not near my pointer?"** —
  [the anchor scenario](a-window-is-opened-dressed-and-placed-where-the-player-was-looking.md),
  and `docs/TRACEABILITY.md` §13.

## Why fifteen again, and why not the same fifteen

The previous set described
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

**If only one is read, read the last of them.** A window
closing correctly while the session never learns it is over was found three times
in one run, in three different disguises — a close button, a swallowed crash, and
a scheduled deadline. The rule the run arrived at is worth a document of its own:
*assert the phase the session reached, not that the window closed.*
