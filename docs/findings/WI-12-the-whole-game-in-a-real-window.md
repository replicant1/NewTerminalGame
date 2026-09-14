# WI-12 — the whole game, in a real window on the real desktop

macOS 25.6.0, Terminal.app, Python 3.9.6. **One window opened, one closed.**
Visible-window census `['7104']` before and `['7104']` after — the user's own
session, exactly where it started.

## What was run

`launcher.game.game_command(seed=4)`, opened and reaped through the same calls
`launcher.game.play` makes, with the tab's contents read in between — which is
the only way to see what a player would see while the game is still up.

```
/bin/sh -c 'i=0; while [ $i -lt 60 ]; do set -- $(stty size 2>/dev/null); \
  if [ ${1:-0} -ge 30 ] && [ ${2:-0} -ge 40 ]; then break; fi; \
  i=$((i+1)); sleep 0.1; done; cd <repo root> || exit 1; \
  exec <python> -m terminalgame.game_main --seed 4'
```

| | |
| --- | --- |
| window opened | +0.93 s, id **7891** |
| game process running | +0.95 s |
| position asked for | `Point(-754, -1352)` |
| position it landed at | `Point(-754, 30)` |
| window size | `357 x 558` points |
| `q` sent | +4.05 s |
| game gone | **+4.17 s** — 0.12 s later |
| window closed | reap `closed=True` |
| leaked windows | **none** |
| total | 4.50 s |

**`set position` is a request, not an instruction** — asked for y = −1352 and
the window landed at y = 30, which is WI-1's measurement reproducing exactly.
The launcher reads the position back rather than believing the move succeeded,
which is why the difference is visible here at all.

## What the player was looking at, four seconds in

Read off the live window with `contents of selected tab`, nothing reconstructed:

```
╔═══════════════════════════════════╗
║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║
║ ▪ ═════════════ ▪ ╔═══════╗ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ║
║ ▪ ■ ▪ ╔═══════════╣ ▪ ║ ▪ ║ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ║
║ ▪ ════╣ ▪ ║ ▪ ■ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║
╠════ ▪ ║ ▪ ╠═══════╝ ▪ ║ ▪ ╚════ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║
║ ▪ ║ ▪ ║ ▪ ║ ▪ ════╗ ▪ ╚═══════════╣
║ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║
║ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ╚════ ▪ ╔════ ▪ ║
║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║▐█▌▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║
║ ▪ ║ ▪ ║ ▪ ════╩═══╗ ▪ ════╣ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ║
║ ▪ ════╩═══════╗ ▪ ║ ▪ ║ ▪ ║ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ║
║ ▪ ■ ▪ ║ ▪ ■ ▪ ║ ▪ ║ ▪ ╚═══════╣ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║
╠════ ▪ ╠═══════╝ ▪ ╠═══════╗ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪▗█▖▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║
║ ▪ ■ ▪ ║ ▪ ════╗ ▪ ║ ▪ ║ ▪ ╚════ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ║
║ ▪ ════╩═══╗ ▪ ╠════ ▪ ╠════ ▪ ║ ▪ ║
║ ▪ ▪ ▪ ▪ ▪ ║ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ║
║ ▪ ■ ▪ ║ ▪ ║ ▪ ║ ▪ ════╝ ▪ ════╝ ▪ ║
║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ║ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ▪ ║
╚═══════╩═══════╩═══════════════════╝
 score 0    arrows, q quits
```

Everything the specification's own picture has, assembled by six work items
that were written and tested separately:

- **blue double-line walls that join up** — corners, tees, crossings and the
  lone `■` blocks, all choosing the glyph that meets their neighbours (WI-5a);
- **a dot on every corridor square** (WI-4, WI-7);
- **the player `▐█▌`** near the middle, three columns wide, where START-1 puts
  it;
- **the ghost `▗█▖`** a long way off, where START-2 puts it — and it has
  *moved*: it started at (1, 27) and is most of the way across the maze after
  roughly twenty ticks, with nothing pressed (GHOST-1, START-5);
- **the status row, not blank**, reading ` score 0    arrows, q quits` — with
  the leading space, which is the question WI-6 settled.

Colours are not in this capture because `contents of selected tab` returns text.
They remain a human check.

## The status row is the part worth dwelling on

`compose(state, status_line=None)` leaves row 29 blank and composes perfectly.
A wiring that forgot the status row would produce a frame that passes every
frame-builder test, every layering test and every domain test — and a game
that silently fails STAT-1. **The row above is the evidence that it was not
forgotten**, and the suite carries the same assertion in three places: on
`build_frame` directly, on every frame a played game presents, and here.

## `q` ended it in 0.12 seconds

Delivered with `do script "q" in selected tab of window id 7891`, which writes
to that one tab: nothing depends on which window has focus, and no keystroke is
injected into whatever the person at the machine is doing. The game exited, the
tab's process list went empty, and the launcher closed the window by the
identity it had captured at creation.

**If `q` had not worked**, the harness would have killed the child by pid —
never the window. A dead child lets the window fall idle and be closed cleanly;
closing a busy window raises the modal sheet that blocks every later automation
call, including the cleanup itself. It was not needed.

## What this does not show

- **The colours.** `contents of selected tab` is text. Blue walls, dim gold
  dots, a bright yellow player, a pink ghost and a cyan status line are all
  still human checks (SCRN-3 to SCRN-6).
- **How it feels to play.** Nobody pressed an arrow key in this run; `q` was
  delivered as terminal input rather than from a keyboard.
- **Flicker.** SCRN-7 asks for redrawing without it, and a capture cannot see
  it.
- **A win or a loss.** This run was quit part-way through. Both endings are
  played end to end in `tests/test_wired_game.py`, against the real frame
  builder, with the final frame asserted — but not in a window.
