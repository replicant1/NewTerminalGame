# Scenario index

Every scenario document in this folder, what it is worth, an order to read them
in, and the ones still to be written.

## What a scenario is

The rest of `docs/` is organised by **subject**: the specification lists what the
program must do, the architecture document describes the layers, and the findings
record what was measured. A scenario is the same program described by what its
parts **do together**.

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
reads. This program is normally started with `python3 -m launcher.game`. That
command opens a new terminal window of its own, 40 characters wide and 30 rows
deep, on a black background in a fixed-width typeface, titled *Terminal Game*,
and plays the game inside it. There is a second way in — running
`python3 -m terminalgame.game_main` directly, in a terminal the player has sized
themselves — which is useful for anyone working on the program and is not the
ordinary way a game is played. Work that only happens on that second path matters
less.

| Priority | What earns it |
|---|---|
| `HIGH` | It happens on the path that **every drawn picture** takes, or it is the only route by which the game can be seen, driven or given back at all. If it is wrong there is either no picture, or no way to affect one |
| `MEDIUM` | It happens once for each game, or only when the player presses a key, or every picture but only in a way that affects how the game *looks* rather than whether it works. The game survives without it and is worse for the lack |
| `LOW` | It happens only when something has already gone wrong, or only on a way of starting the program that is not the ordinary one |

## The scenarios in this folder

They are listed in the order the program does them: the window before the maze,
the maze before the first picture, and the endings last.

| Scenario | Priority |
|---|---|
| [The launcher asks where the player was looking, and then opens the game's window](the-launcher-asks-where-the-player-was-looking-and-then-opens-the-games-window.md) | `HIGH` |
| [The game waits for its window to reach 40 by 30 before it starts drawing](the-game-waits-for-its-window-to-reach-40-by-30-before-it-starts-drawing.md) | `LOW` |
| [The terminal is put into raw mode and given back on every way out](the-terminal-is-put-into-raw-mode-and-given-back-on-every-way-out.md) | `HIGH` |
| [A terminal too small to hold the picture is refused before a game starts](a-terminal-too-small-to-hold-the-picture-is-refused-before-a-game-starts.md) | `LOW` |
| [A maze is carved into a spanning tree and then braided until no dead ends remain](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` |
| [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` |
| [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` |
| [A game state is composed into a 40 by 30 frame with the ghost drawn last](a-game-state-is-composed-into-a-40-by-30-frame-with-the-ghost-drawn-last.md) | `HIGH` |
| [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` |
| [A whole frame is written to the terminal and made visible in one pass](a-whole-frame-is-written-to-the-terminal-and-made-visible-in-one-pass.md) | `HIGH` |
| [The key read's timeout is recomputed every pass so the ghost keeps its beat](the-key-reads-timeout-is-recomputed-every-pass-so-the-ghost-keeps-its-beat.md) | `HIGH` |
| [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` |
| [A clock tick moves the ghost, which is never told where the player is](a-clock-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` |
| [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` |
| [The launcher closes the window it created, once nothing is running in it](the-launcher-closes-the-window-it-created-once-nothing-is-running-in-it.md) | `HIGH` |

That is eight at `HIGH`, five at `MEDIUM` and two at `LOW`. The line between
the first two is drawn at *the ordinary way in* rather than at *per picture*, and
that choice is most of what makes the ranking say anything. Drawn at "does this
run for every picture", the wall characters would outrank the only route by which
a window ever opens, which is the wrong way round for a program whose whole first
act is making itself somewhere to live.

## A reading order

The list above is the order the program does things, which is not the order that
makes them easiest to learn. What follows is three laps of the same circuit. Each
lap is complete on its own: stop after any one of them and you will have a whole
picture of the program, just a smaller one than if you go round again.

The times are reading times, at the pace of somebody reading carefully rather
than skimming.

### Lap 1 — one picture, from cause to characters on a screen

**56 minutes.** The five documents that describe the path every drawn picture
takes. Nothing here is optional and nothing here is unusual. This is the game
running normally.

| | Document | Priority | Time |
|---:|---|---|---:|
| 1 | [The key read's timeout is recomputed every pass so the ghost keeps its beat](the-key-reads-timeout-is-recomputed-every-pass-so-the-ghost-keeps-its-beat.md) | `HIGH` | 13 min |
| 2 | [An arrow key moves the player one square and eats the dot it lands on](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) | `HIGH` | 12 min |
| 3 | [A clock tick moves the ghost, which is never told where the player is](a-clock-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) | `HIGH` | 11 min |
| 4 | [A game state is composed into a 40 by 30 frame with the ghost drawn last](a-game-state-is-composed-into-a-40-by-30-frame-with-the-ghost-drawn-last.md) | `HIGH` | 11 min |
| 5 | [A whole frame is written to the terminal and made visible in one pass](a-whole-frame-is-written-to-the-terminal-and-made-visible-in-one-pass.md) | `HIGH` | 9 min |

Read them in this order rather than any other. The first one is the beat
everything else hangs off, and the last two are one story told in two halves —
building a picture, and then putting it on the glass.

At the end of this lap you can follow any picture in the game from the thing that
caused it to the characters that reach the terminal. You will also have met the
rule the whole design turns on, which is that **the part that knows a key was
pressed never learns what it means, and the part that knows what it means never
learns that a key exists.**

### Lap 2 — where the arena comes from, and how a game ends

**48 minutes.** What is drawn, where it came from, and the two questions that
decide every ending.

| | Document | Priority | Time |
|---:|---|---|---:|
| 6 | [A maze is carved into a spanning tree and then braided until no dead ends remain](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md) | `MEDIUM` | 12 min |
| 7 | [A new game puts the player in the middle, the ghost far away, and a dot on every other square](a-new-game-puts-the-player-in-the-middle-the-ghost-far-away-and-a-dot-on-every-other-square.md) | `MEDIUM` | 11 min |
| 8 | [A wall square chooses its double-line glyph from its four neighbours](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) | `MEDIUM` | 9 min |
| 9 | [The status row shows the score and the keys that still work](the-status-row-shows-the-score-and-the-keys-that-still-work.md) | `MEDIUM` | 8 min |
| 10 | [Eating the last dot on the ghost's square is a loss and not a win](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) | `MEDIUM` | 8 min |

The first and third are a pair, and the pairing is the point: one makes a shape
out of open and closed squares knowing nothing about how it will look, and the
other turns that shape into lines knowing nothing about how it was made. The
second and the last are also a pair, separated by a whole game: a decision taken
while laying the dots is the only reason the last document describes something
that can actually happen.

This lap assumes lap 1.

### Lap 3 — the window it all happens in, and the ways in and out

**44 minutes.** Everything on either side of a game: how a window is made for it,
how the terminal inside that window is borrowed and given back, what happens when
it will not do, and how the window is taken away again.

| | Document | Priority | Time |
|---:|---|---|---:|
| 11 | [The launcher asks where the player was looking, and then opens the game's window](the-launcher-asks-where-the-player-was-looking-and-then-opens-the-games-window.md) | `HIGH` | 14 min |
| 12 | [The launcher closes the window it created, once nothing is running in it](the-launcher-closes-the-window-it-created-once-nothing-is-running-in-it.md) | `HIGH` | 11 min |
| 13 | [The terminal is put into raw mode and given back on every way out](the-terminal-is-put-into-raw-mode-and-given-back-on-every-way-out.md) | `HIGH` | 10 min |
| 14 | [The game waits for its window to reach 40 by 30 before it starts drawing](the-game-waits-for-its-window-to-reach-40-by-30-before-it-starts-drawing.md) | `LOW` | 5 min |
| 15 | [A terminal too small to hold the picture is refused before a game starts](a-terminal-too-small-to-hold-the-picture-is-refused-before-a-game-starts.md) | `LOW` | 4 min |

Read the first two together or not at all. They are one window's whole life, and
the second is the one that explains why the first captures a number and never
lets go of it. The last two are also a pair: one is a race, and the other is what
happens when the race is lost.

## If you are here for one thing

| The question | The document |
|---|---|
| How does a key press become a character moving? | [An arrow key moves the player](an-arrow-key-moves-the-player-one-square-and-eats-the-dot-it-lands-on.md) |
| How does the ghost keep moving with only one thread and no locks? | [The key read's timeout is recomputed every pass](the-key-reads-timeout-is-recomputed-every-pass-so-the-ghost-keeps-its-beat.md) |
| How do you promise the ghost is not cheating? | [A clock tick moves the ghost](a-clock-tick-moves-the-ghost-which-is-never-told-where-the-player-is.md) — it cannot see the player |
| Where does the maze come from, and why has it no dead ends? | [A maze is carved and then braided](a-maze-is-carved-into-a-spanning-tree-and-then-braided-until-no-dead-ends-remain.md) |
| Why are the corners of the walls drawn correctly? | [A wall square chooses its glyph](a-wall-square-chooses-its-double-line-glyph-from-its-four-neighbours.md) |
| Why does the game not flicker? | [A whole frame is written in one pass](a-whole-frame-is-written-to-the-terminal-and-made-visible-in-one-pass.md) |
| What exactly does the bottom row say, and why? | [The status row shows the score and the keys](the-status-row-shows-the-score-and-the-keys-that-still-work.md) |
| I ate every dot and still lost. Is that a bug? | [Eating the last dot on the ghost's square](eating-the-last-dot-on-the-ghosts-square-is-a-loss-and-not-a-win.md) — no, it is a requirement |
| Why does a window open by itself, and why does it close by itself? | [The launcher opens the window](the-launcher-asks-where-the-player-was-looking-and-then-opens-the-games-window.md) and [the launcher closes it](the-launcher-closes-the-window-it-created-once-nothing-is-running-in-it.md) |
| Why does it refuse to start in my terminal? | [A terminal too small](a-terminal-too-small-to-hold-the-picture-is-refused-before-a-game-starts.md) |
| Why is my shell not broken after the game crashed? | [The terminal is given back on every way out](the-terminal-is-put-into-raw-mode-and-given-back-on-every-way-out.md) |

## Scenarios not yet written

Each of these is a real collaboration in the program that no document covers yet.
They are listed in bold rather than linked, because a link to a document that does
not exist would be a broken link. The cast is already worked out for each.

- **A press towards a wall changes nothing and no picture is drawn** — `MEDIUM`.
  The cast of the arrow-key scenario with the wall question answered the other
  way. Worth its own document because "nothing at all" is checked by identity
  rather than by listing what did not change, and because that convention is what
  lets the loop skip a redraw without asking anything about walls.
  Cast: `loop`, `player`, `GameState`, `Maze`.

- **A finished game keeps the ending it got and stops redrawing** — `MEDIUM`.
  Requirement END-5, and the interesting part is how little code enforces it: the
  Domain refuses to move a finished game, so the loop needs no check of its own,
  and the last picture stays up because nothing changes rather than because
  anything decides to leave it. Also why a finished game is never re-judged.
  Cast: `loop`, `rules`, `player`, `GameState`.

- **A desktop that will not say where the player was looking gets a default
  position** — `LOW`. The window-opening cast with the very first question
  refused, because the player declined the permission. It degrades to a
  documented default position rather than refusing to start, which is architecture
  assumption A2.
  Cast: `WindowLauncher`, `Desktop`, `geometry`, `AutomationError`.

- **Setting up fails after the window already exists, and the launcher takes it
  back** — `LOW`. Caution C3. The window is dealt with before the error is,
  because the alternative is an orphaned window left on the player's desktop. The
  report says what became of it, and names it by number when the launcher could
  not take it back.
  Cast: `WindowLauncher`, `LaunchFailed`, `ReapResult`, `Desktop`.

- **One seed reproduces a whole game, not just its maze** — `LOW`. A single
  random source is threaded through the maze, both starting positions and every
  choice the ghost makes. With two sources a seed would reproduce the maze but not
  the game played on it, and reproducing a whole game is what the acceptance
  checks need.
  Cast: `game_main`, `game_state`, `maze_generator`, `ghost_policy`.

- **A key that is neither an arrow nor `q` is discarded** — `LOW`. Requirements
  CTRL-5 and END-6. Where a terminal's key codes become named keys, and where
  everything else becomes nothing at all. Small, but it is the one place the
  escape sequences an arrow key really sends stop travelling into the game.
  Cast: `CursesScreen`, `Key`, `loop`.
