# Scenario index

Every scenario document in this folder, what it is worth, and an order to read
them in.

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
reasoning in this program lives in modules with no classes in them at all: the
wall-glyph table, the key translation and the turn resolver are three of them.

## What the priorities mean

Every scenario document in this folder carries a priority on the line under its
headline. The priority is one of `HIGH`, `MEDIUM` or `LOW`.

A priority is not a score for how interesting the scenario is. It answers a
narrower question: **what stops working, and how often, if this piece of the
program is wrong.**

The answer depends on how the program is normally run rather than on how the code
reads. **This program is started one way and one way only:**

```sh
.venv/bin/python -m terminal_game.shell.game
```

That command creates its own window — 40 characters wide and 30 rows deep, black
ground, fixed-width typeface, titled *Terminal Game* — and plays the game inside
it. There is no launcher and no second process: the architecture's candidate 2
was adopted, so the application owns its window rather than dressing somebody
else's, and nothing here drives a terminal emulator through a scripting bridge.

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
| [A key press becomes an intent, and an unknown key becomes nothing](a-key-press-becomes-an-intent-and-an-unknown-key-becomes-nothing.md) | `HIGH` |
| [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` |
| [A tick moves the ghost, which is never told where the player is](a-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` |
| [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` |
| [A session goes Playing → Decided → Ended, and only `q` leaves it](a-session-goes-playing-to-decided-to-ended-and-only-q-leaves-it.md) | `HIGH` |
| [The tick timer keeps the ghost's beat, and stops when the game is decided](the-tick-timer-keeps-the-ghosts-beat-and-stops-when-the-game-is-decided.md) | `HIGH` |
| [A game state is composed into a 40 × 30 field, three cells to an actor](a-game-state-is-composed-into-a-40-by-30-field-three-cells-to-an-actor.md) | `HIGH` |
| [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` |
| [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` |
| [A field is painted onto the canvas, touching only the cells that changed](a-field-is-painted-onto-the-canvas-touching-only-the-cells-that-changed.md) | `HIGH` |
| [A maze is carved on a lattice of odd cells, then braided until no dead ends remain](a-maze-is-carved-on-a-lattice-of-odd-cells-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` |
| [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` |
| [The font is measured at start-up, and the window's size is derived from what was found](the-font-is-measured-at-start-up-and-the-windows-size-is-derived-from-what-was-found.md) | `MEDIUM` |
| [The window is opened withdrawn, dressed, placed, and only then shown](the-window-is-opened-withdrawn-dressed-placed-and-only-then-shown.md) | `HIGH` |
| [The window closes itself when the session ends, and the process runs out of work](the-window-closes-itself-when-the-session-ends-and-the-process-runs-out-of-work.md) | `HIGH` |
| [Every import in the tree is checked against the layer rule](every-import-in-the-tree-is-checked-against-the-layer-rule.md) | `LOW` |

All sixteen are written.

## A reading order

Four laps, 65 minutes in all. Each is a whole journey; each later lap explains
something the earlier one took for granted.

### Lap 1 — one picture, from the thing that caused it to lit pixels

**23 minutes.** The six documents that describe the path every picture takes. Nothing here is optional and nothing here is unusual: this is the game running normally.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [The tick timer keeps the ghost's beat, and stops when the game is decided](the-tick-timer-keeps-the-ghosts-beat-and-stops-when-the-game-is-decided.md) | `HIGH` | 3 min |
| 2 | [A key press becomes an intent, and an unknown key becomes nothing](a-key-press-becomes-an-intent-and-an-unknown-key-becomes-nothing.md) | `HIGH` | 3 min |
| 3 | [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` | 4 min |
| 4 | [A tick moves the ghost, which is never told where the player is](a-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` | 4 min |
| 5 | [A game state is composed into a 40 × 30 field, three cells to an actor](a-game-state-is-composed-into-a-40-by-30-field-three-cells-to-an-actor.md) | `HIGH` | 4 min |
| 6 | [A field is painted onto the canvas, touching only the cells that changed](a-field-is-painted-onto-the-canvas-touching-only-the-cells-that-changed.md) | `HIGH` | 5 min |

Read them in this order rather than any other. The first is the beat everything else hangs off; the middle three are the two things that can change a game — a key and a tick — and the last two are one story in two halves, building a picture and then putting it on the glass.

At the end of this lap you can follow any picture in the game from the thing that caused it to the pixels it becomes. You will also have met the rule the whole design turns on: **the part that knows a key was pressed never learns what it means, and the part that knows what it means never learns there is a window.**

### Lap 2 — how that picture is drawn, and where the arena comes from

**20 minutes.** Lap 1 took two things for granted: that the maze exists, and that its squares know how to be drawn. This lap is both, and it ends on the rule that decides a game.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` | 4 min |
| 2 | [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` | 3 min |
| 3 | [A maze is carved on a lattice of odd cells, then braided until no dead ends remain](a-maze-is-carved-on-a-lattice-of-odd-cells-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` | 5 min |
| 4 | [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` | 4 min |
| 5 | [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` | 4 min |

The first two finish the picture — the glyph a wall chooses, and the row beneath the maze. The next two build the arena. The last is the one to read slowly: it is the requirement the plan called the project's single fragility, and the way it was removed rather than guarded against is the best argument in this folder for choosing a shape over writing a rule.

At the end of this lap you know why a maze never has a dead end, why the ghost starts on a dot, and why eating the last one is sometimes a loss.

### Lap 3 — the window it all happens in, and the ways out of it

**18 minutes.** The program owns its own window, which is the largest change from the architecture this one replaced. These four are that window's whole life.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [The font is measured at start-up, and the window's size is derived from what was found](the-font-is-measured-at-start-up-and-the-windows-size-is-derived-from-what-was-found.md) | `MEDIUM` | 4 min |
| 2 | [The window is opened withdrawn, dressed, placed, and only then shown](the-window-is-opened-withdrawn-dressed-placed-and-only-then-shown.md) | `HIGH` | 4 min |
| 3 | [A session goes Playing → Decided → Ended, and only `q` leaves it](a-session-goes-playing-to-decided-to-ended-and-only-q-leaves-it.md) | `HIGH` | 5 min |
| 4 | [The window closes itself when the session ends, and the process runs out of work](the-window-closes-itself-when-the-session-ends-and-the-process-runs-out-of-work.md) | `HIGH` | 5 min |

The order is chronological: the font that decides how big the window is, the window being placed and shown, the game inside it running its three phases, and it closing.

The last is the one to read if you only read one thing in this folder. A window closing correctly while the session never learns it is over was found three times in one run, in three disguises, and the rule it produced — *assert the phase the session reached, not that the window closed* — is the most transferable thing this program has to say.

### Lap 4 — the rule the other three rest on

**4 minutes.** Not part of the running program at all, which is why it is last and why it is the only `LOW` in the folder. It is also the reason the first three laps could be written the way they were.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [Every import in the tree is checked against the layer rule](every-import-in-the-tree-is-checked-against-the-layer-rule.md) | `LOW` | 4 min |

Every claim in the earlier laps of the form *"this part names no toolkit"* or *"randomness arrives as an argument"* is true because something re-runs it on every suite run. This is that something, and it is worth reading after the other three rather than before — the rules mean more once you have seen what they buy.

## If you are here for one thing

- **"Why does the maze never have a dead end?"** — [the carve-and-braid scenario](a-maze-is-carved-on-a-lattice-of-odd-cells-then-braided-until-no-dead-ends-remain.md).
- **"How does the ghost keep its beat?"** — [the tick-timer scenario](the-tick-timer-keeps-the-ghosts-beat-and-stops-when-the-game-is-decided.md).
- **"Why is eating the last dot sometimes a loss?"** — [the ordered-outcome scenario](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md).
- **"Why does the window open in the middle of my screen and not beside what I was using?"** — [the window-opening scenario](the-window-is-opened-withdrawn-dressed-placed-and-only-then-shown.md). WIN-4 is not met; the reader that would meet it is a seam awaiting a ruling.
- **"Why is the font Menlo at 16?"** — [the font scenario](the-font-is-measured-at-start-up-and-the-windows-size-is-derived-from-what-was-found.md). Both halves of that were measured.

## Why sixteen

Fifteen would have been the same count as the previous set, and the sixteenth is
[the layer rule](every-import-in-the-tree-is-checked-against-the-layer-rule.md).

It earns a document because it is 463 lines of this repository, because the
`LOW` band was defined for exactly this kind of thing and had never been used,
and because almost every other scenario in the folder makes a claim — *the
Domain names no toolkit*, *a tick arrives as a call*, *only one module may paint*
— that is only true because that tool re-runs it. A folder that described the
program's behaviour and left out the thing that keeps the behaviour honest would
be describing an intention.

The set is otherwise chosen the same way as before: one mind-sized piece of
behaviour each, joined so that reading a lap in order is a whole journey, and
sized so that no document needs a second sitting.

**Two scenarios describe a requirement that is not met**, and they say so rather
than describing what the code was supposed to do. WIN-4 — the window appearing
beside whatever the player was last looking at — is unmet, because how to read
the anchor is a question outstanding with the user; what ships centres the
window on the main display instead. That is in the window-opening scenario, and
it is in the code's own docstrings too.
