# WI-17 — an agent can read the screen, and nothing on it is being drawn

Measured on 2026-09-21, after the user looked at the running game and said there was no maze
in it.

Two findings. The first overturns a premise this project built a rule on. The second is the
reason the game shows a blank window, and it is not in the application.

## 1. "No agent on this machine can capture the pixels" is false

`docs/IMPLEMENTATION_PLAN.md` gives that as the reason human item 9 goes to the user:

> **Human item 9** … is yours to put in front of the user, **because no agent on this machine
> can capture the pixels to judge it.**

It was never tested. `screencapture` ships with macOS, Screen Recording is already granted to
this terminal, and a capture of a named region returns real window content — chrome, title
text and all. Four captures were taken before anyone noticed the premise was wrong.

**What is true** is the sentence in WI-17's own Part 4, which is more careful: *"I did not look
at the screen."* That was a statement about what had been done, not about what could be.

## 2. Tk 8.5.9 maps windows here and paints nothing in them

The game's window is white and empty. So is this, which owes nothing to the project:

```python
top = tkinter.Toplevel(root)
canvas = tkinter.Canvas(top, width=400, height=570, background="#000000")
canvas.pack()
canvas.create_rectangle(50, 50, 350, 520, fill="#2121de", outline="")
```

Photographed at the canvas's own `winfo_rootx/rooty`: **17,195 of 17,200 sampled pixels are
pure white**. Not the black ground, not the blue rectangle. The window is mapped, sized
400×570, and reports `background='#000000'`.

```
python 3.9.6 · tk patchlevel 8.5.9 · windowingsystem aqua · three displays, Retina
```

**So the blank game is not an application defect.** `requirements.txt` pins `/usr/bin/python3`
as *"the only interpreter on this machine with a working `_tkinter`"* — and "working" was only
ever established as *importable*, never as *able to draw*.

## 3. Why 996 passing tests could not see it

Because every one of them reads what Tk was **told**, not what reached the screen. Tk records
`text='╔'`, `fill='#2121de'` on a canvas item it never draws, and `itemcget` returns the
record. A window showing nothing satisfies every assertion in the suite.

The test that runs the real entry point says so itself:

> *What this can honestly observe, and no more: `run_game` maps a window, returns rather than
> hanging, and leaves nothing open.*

An investigating agent fell into the same trap on the way to this finding: it read back 698
glyphs through `itemcget` and reported the game was painting correctly. It was reading
bookkeeping. **Only the framebuffer knows, and only a capture reads the framebuffer.**

## 4. The recipe that works

- **Take the geometry from Tk** — `winfo_rootx`, `winfo_rooty`, `winfo_width`,
  `winfo_height`. **Never from AppleScript**, whose `position` amendment 1 already measured as
  wrong by a display height on a secondary display. Every capture taken from an AppleScript
  position during this investigation photographed the wrong rectangle, twice catching
  unrelated windows belonging to the user.
- **`screencapture -x -t bmp -R x,y,w,h`** — on every Mac, and a 32-bpp BMP is a header and a
  block of BGRA that `struct` reads. No Pillow, no numpy, `requirements.txt` unchanged.
- **Capture from inside a running event loop**, in an `after` callback, after a settle delay.
  A window mapped in the same turn of the loop has not been composited and photographs the
  desktop behind it.
- **Never call `update()` to force a paint.** It does not return on a mapped window — measured
  for WI-5/WI-6, and it hung this investigation for two minutes.
- **Compare with tolerance.** A Retina capture passes through a colour profile and every glyph
  carries an antialiased fringe, so ink arrives as a spread rather than one value.

## 5. What it does not settle

Human item 9 — whether Menlo's box-drawing ink spans the full cell so a wall run reads
unbroken rather than dashed — is a perceptual judgement at the sub-pixel level and remains the
user's. The plan was right about that one specifically and wrong to generalise from it to
"pixels cannot be read at all".
