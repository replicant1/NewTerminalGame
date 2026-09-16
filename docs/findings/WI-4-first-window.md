# WI-4 — The first window, and what it actually did

**Measured by:** DEV-C, WI-4, on this machine, with `tools/walking_skeleton.py`.
**Interpreter:** `/usr/bin/python3` — Python 3.9.6. **Toolkit:** Tk **8.5.9**.
**Windows opened for this item:** five, each a few seconds, each confirmed gone.

This is the end-to-end proof the whole of M0 exists to reach: the application's own
window, at the size WI-2's font metrics give, painting the specimen picture from the
requirements through the real surface, ticking at the ghost's cadence, taking keys, and
closing itself. **Candidate 2 was chosen over the architect's own recommendation, and
this is the first moment anybody can say whether that choice works. It does.**

Re-run it:

```
/usr/bin/python3 tools/walking_skeleton.py                     # 10s, or press q
/usr/bin/python3 tools/walking_skeleton.py --seconds 3 --json
```

It is not part of the suite; `unittest discover` does not collect it.

---

## 1. The window, measured

| Asked for | Measured back | |
| --- | --- | --- |
| title `Terminal Game` | `Terminal Game` | exact |
| 400 × 570 px, from Menlo 16pt at 10 × 19 a cell | window 400 × 570, canvas 400 × 570 | exact |
| position (160, 160) | (160, 160) | exact |
| background `black` | `black` | exact |
| not resizable | not resizable, both axes | exact |
| 143 ms tick | 144.0–144.3 ms observed over three runs | ~6.93/s |

**The WI-2 / WI-3 join holds with nothing between it.** The metrics own the size and the
window takes it: `pixel_size_for(measure_metrics())` is `PixelSize(400, 570)` and that
is what the window is, to the pixel. There is no rounding, no window-manager
adjustment, and no second source of truth.

**SCRN-2 is a fact here, not only a rule.** The painted canvas holds **696 items and
every one of them is of kind `text`** — no image, no bitmap, no rectangle, no line. The
architect's caution C5 said candidate 2 turns "there are no images" from something the
medium enforces into something a developer must remember. On this evidence the
discipline is holding, and `canvas_item_kinds` is a cheap thing for WI-10's guard to
assert against a real paint.

**30 rows painted**, the specimen picture read from `tests/specimen.py` rather than
transcribed a second time.

## 2. The thing this item found: the window must take the keyboard

**This is the defect WI-4 existed to catch, and it would not have been caught by any
test.**

WI-3's adapter called `canvas.focus_set()` and no more, on the reasoning that forcing
focus is rude. WI-3's tests passed, and WI-3's probe passed, because **neither of them
ever pressed a key.**

Measured across two diagnostic windows, driving synthetic key events into the real
window:

| What was tried | Delivered? |
| --- | --- |
| `root.event_generate("<KeyPress>", keysym=…, when="now")` | **no** |
| `canvas.event_generate("<KeyPress>", keysym=…, when="now")` | **no** |
| `root.event_generate("<Key-c>", when="now")` | **no** |
| the same, after `root.focus_force()` | **yes** |
| a queued event, after `root.focus_force()` | **yes** |

At the moment of the three failures, Tk's own bookkeeping looked entirely correct:
`focus_get()` returned the canvas, the canvas's bindtags were
`['.!canvas', 'Canvas', '.', 'all']`, and the `<Key>` binding was on `.`. The routing
was right the whole time. **Tk-internal focus is not enough: the toplevel needs the
operating system's keyboard focus before a key reaches the application at all.**

**What it would have cost.** A game window that opened without OS focus would take no
arrow keys and no `q`. CTRL-4 and END-6 make `q` the *only* way out of a finished game,
so the player would have been left with a window they could only close from the window
manager — which is also the one thing WIN-5 is trying to avoid.

**The fix**, in `TkToolkit.create_window`: `root.lift()` and `root.focus_force()` as the
window opens, before `canvas.focus_set()`. Taking the keyboard is the right manners
here rather than the wrong ones — the player has just launched a game and expects to
type into it. This is a change to WI-3's adapter made in WI-4's branch, and it is
flagged as a deviation rather than slipped in.

**Measured after the fix**, driving `Up, Left, Down, Right, z, q` into the real window:

| | |
| --- | --- |
| Keys delivered to the collaborator | `Up, Left, Down, Right, z, q` — all six, in order |
| `q` ended the session | yes, at **1.437 s** against an 8 s deadline |
| Window reaped | yes |
| Process exit | 0, by itself |

So the key path, the quit path and the self-closing window are all now measured against
real Tk, and not only against a recording double.

## 3. What the titlebar read — **and why that is still not an answer**

`root.title()` reads back exactly `Terminal Game`, against the architect's candidate-1
measurement of `rodneybailey — Terminal Game — sleep 2`. Under candidate 2 the process
owns the window and nothing composes anything around the title.

**Assumption A1 is still open.** Reading a string back from the toolkit that set it is
not a person seeing a titlebar, and macOS may add furniture of its own — a proxy icon, a
modified dot, a full-screen control — that the toolkit never hears about. **Nobody has
looked at any of these five windows.** The exact question for the user is in section 5.

## 4. Assumption A4 is open too, and this is the first item that can show it

The window is 400 × 570 because Menlo 16pt measures 10 × 19 a cell. Whether that is
*"large enough to read comfortably"* (WIN-2, assumption A4) has no objective test and
nobody has seen it. DEV-B raised it from WI-2; this is the first script that puts it on
a screen.

## 5. What a human needs to do, exactly

Run this, from the repository root:

```
/usr/bin/python3 tools/walking_skeleton.py
```

A black window, 400 × 570, appears down and to the right of the top-left corner. It
closes itself after ten seconds, or straight away if you press `q`. Three questions:

1. **Does the titlebar read exactly `Terminal Game`** — nothing before it, nothing after
   it, no path, no username, no filename? *(A1. First asked here, confirmed at WI-21.)*
2. **Is the type large enough to read comfortably?** *(A4.)*
3. **Do the blue double lines of the maze join up** into clean corners, tees and
   crossings, or are there gaps or overlaps where they meet? *(This is the residual
   glyph-alignment risk candidate 2 carries. WI-2 measured that every glyph has the same
   advance width; whether the strokes actually meet is something only an eye can settle,
   and WI-16 asks it properly.)*

Nothing else in this document needs a person. Everything in sections 1 and 2 was
measured.

## 6. What this does not tell you

- **Nothing about the game.** The skeleton paints one fixed picture. There is no maze
  generator here, no ghost, no rules and no score. WI-18 assembles the real thing.
- **Nothing about where the window *should* go.** It is at a fixed offset. WIN-4's
  anchor is WI-14's, under assumption A2, and still has a permission question in it.
- **Nothing about flicker over a long game.** WI-2 measured 5.6 ms for a full paint and
  0.68 ms for a one-square move against a 143 ms budget, which is the number that
  matters; this item repainted once.

## 7. Every window opened, and its fate

| # | What | Lifetime | Reaped |
| --- | --- | --- | --- |
| 1 | skeleton, `--seconds 2` | 2.05 s | yes |
| 2 | skeleton, `--seconds 8 --press …` (before the focus fix; no keys arrived) | 8.06 s | yes |
| 3 | key-dispatch diagnostic, first attempt | < 4 s | yes |
| 4 | key-dispatch diagnostic, second attempt | < 4 s | yes |
| 5 | skeleton, `--seconds 8 --press Up,Left,Down,Right,z,q` | 1.44 s | yes |

Each quit on its own scheduler, each was reaped in a `finally`, each ran under an
external kill deadline that was never reached, and `pgrep` was empty afterwards every
time. **None was left behind, and no modal sheet was ever raised** — the window belongs
to the process, so there is no second application left holding one.
