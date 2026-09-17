# The window is opened withdrawn, dressed, placed, and only then shown

**Priority: `HIGH`** — it is the only route by which the game becomes visible, and a fault here takes the whole process down with it. [What the priorities mean](SCENARIO_INDEX.md#what-the-priorities-mean).

[`GameWindow`](../../terminal_game/shell/window.py#L81) owns the window and
nothing else. WIN-1, WIN-2 and WIN-3[^codes] are here; WIN-4 is
[`placement`](../../terminal_game/shell/placement.py)'s and is deliberately
absent from the window class.

**Three of the four window requirements stopped being caveats under this
architecture.** The title is whatever this process says it is, with nothing
composing around it; the size is a pixel rectangle this process asks for; the
window closes because the process that owns it closes it. The architect's
assumptions A1 and A5 and his caution C2 all fell away with the terminal they
were about.

## Built withdrawn, so it is never half-formed on screen

The window is created **withdrawn**. The title, the size, the ground and the
first frame can all be set before anybody sees it, and
[`show`](../../terminal_game/shell/window.py#L218) is what puts it there.
Nothing after that changes its size or its title.

The order in [`run_game`](../../terminal_game/shell/game.py#L388) is exact, and
each step is somebody's requirement:

```python
game = build_game(...)   # a window, withdrawn; a session; a maze
game.start()             # paint the first frame, bind keys, start the timer
game.place()             # WIN-4 — decide where it goes
game.window.show()       # deiconify
game.window.run()        # mainloop, until the window is destroyed
```

**`start` before `show` is START-5**: *"the game is under way the moment the
window opens: the ghost is already moving, and nothing has to be pressed to
begin."* The frame is painted and the timer is running before the window is
ever mapped, so there is no first moment in which the game is visible but not
yet going.

## The placement call that was missing

`game.place()` is wiring and decides nothing — it asks
[`placement_for`](../../terminal_game/shell/placement.py#L175) and carries the
answer to `move_to`.

It exists because the assembly work item **built both halves and called
neither**. Placement was complete and tested, the window could be moved, and
the running program placed its window nowhere — so a fresh toplevel landed at
Tk's own default of `(5, 38)`. Measured, and fixed as its own small item.

That is the shape worth carrying away: *an item can be complete, tested, and
never called.* Both pieces had tests; nothing tested that anybody joined them.

## WIN-4 is not met, and the code says so rather than pretending

WIN-4 asks for the window to appear *"a little below and to the right of
whatever window the player was last looking at"*. That has two halves and only
one is settled.

**Settled, and all of it in this module:** given an anchor, where the window
goes; what to do when there is no anchor; and how to say a position to the
toolkit without getting it wrong. None of that needs the desktop, so all of it
is tested against supplied numbers.

**Not settled:** *how the anchor is read*. Three routes were measured and the
choice between them is a question outstanding with the user. So reading is a
seam — [`AnchorReader`](../../terminal_game/shell/placement.py#L92) — and what
ships is [`NoAnchor`](../../terminal_game/shell/placement.py#L109), the reader
that reads nothing and therefore cannot prompt or crash.

With it the window is **centred on the main display**, which is a sane default
and is not WIN-4. The docstrings say so in as many words. Whichever route is
chosen becomes a small, tested substitution rather than a rewrite.

## Two measurements this module exists to encode

**The coordinate space has negative origins.** Three displays were measured: the
main one at `(0, 0) 1512 × 982`, and two others at `(-3509, -1440)` and
`(-949, -1440)`. Arithmetic that assumes a screen starts at zero is wrong on
that desk.

And **a clamp would be worse than none.** Tk's `winfo_screenwidth` and
`winfo_screenheight` report the *main display only*, so clamping a position to
"the screen" would push a perfectly good anchor on a second display back onto
the first. **Nothing here clamps**, and that is a decision rather than an
omission.

**Tk's geometry string does not spell a negative origin the obvious way:**

| written as | produces | which Tk reads as |
| --- | --- | --- |
| `"+{}+{}".format(-877, -1348)` | `+-877+-1348` | x = −877, y = −1348 — correct |
| `"{:+d}{:+d}".format(-877, -1348)` | `-877-1348` | 877 from the **right**, 1348 from the **bottom** |

The tidier-looking one is wrong, silently, on a different display. That is why
[`geometry_string`](../../terminal_game/shell/placement.py#L192) exists as a
function with a test rather than as a format call at the point of use.

| Participant | What it represents, and its part in this scenario |
| --- | --- |
| [`GameWindow`](../../terminal_game/shell/window.py#L81) | The one window. In this scenario it is **WIN-1, WIN-2 and WIN-3**, and it holds no opinion about where it goes |
| [`GridSurface`](../../terminal_game/presentation/surface.py#L115) | The canvas. In this scenario it is **what goes in the window**, built before the window is shown |
| [`placement`](../../terminal_game/shell/placement.py) | A module and four small types. In this scenario it is **where the window goes**, and the honest admission that WIN-4 is unmet |
| [`Rect`](../../terminal_game/shell/placement.py#L61) | A rectangle in the global display space. In this scenario it is **why nothing clamps**: origins are negative on a real desk |
| [`Point`](../../terminal_game/shell/placement.py#L82) | A position. In this scenario it is **what the geometry string must spell correctly**, signs included |
| [`AnchorReader`](../../terminal_game/shell/placement.py#L92) | A one-method seam. In this scenario it is **the unsettled half**, kept substitutable |
| [`NoAnchor`](../../terminal_game/shell/placement.py#L109) | The reader that reads nothing. In this scenario it is **what ships**, and why the window is centred |
| [`Game`](../../terminal_game/shell/game.py#L90) | The assembly. In this scenario it is **the caller that joins them**, which is the call that was once missing |

```mermaid
sequenceDiagram
  autonumber
  participant E as entry point
  participant G as Game
  participant W as GameWindow
  participant S as GridSurface
  participant P as placement<br/>a module
  participant A as AnchorReader

  E->>G: build_game()
  G->>W: a toplevel, WITHDRAWN
  W->>S: build the canvas, measure the font
  S-->>W: 400 × 570
  W->>W: title "Terminal Game", black ground, not resizable
  E->>G: start()
  G->>W: present the first frame; bind <Key>; start the timer
  note right of G: START-5 — under way before it is seen.
  E->>G: place()
  G->>P: placement_for(reader, display, window size)
  P->>A: read()
  alt an anchor was readable
    A-->>P: a Rect
    P-->>G: below and right of it, by (40, 40)
  else NoAnchor, which is what ships
    A-->>P: None
    P-->>G: centred on the main display
    note right of P: WIN-4 is NOT met here,<br/>and the code says so.
  end
  G->>W: move_to(point) — via geometry_string, which gets the signs right
  E->>W: show() — deiconify
  E->>W: run() — mainloop
```

## Related scenarios

- **The font is measured at start-up, and the window's size is derived from what
  was found** — where 400 × 570 comes from.
- **The window closes itself when the session ends, and the process runs out of
  work** — the other end of this window's life.
- **A field is painted onto the canvas, touching only the cells that changed** —
  what fills it.

### Footnotes

[^codes]: Requirement codes are the specification's own, in
    [`docs/FUNCTIONAL_REQUIREMENTS.md`](../FUNCTIONAL_REQUIREMENTS.md).
