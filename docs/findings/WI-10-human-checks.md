# Terminal Game — the six checks only a person can make

You are being asked to look at six things, because there is no way to test any
of them without a pair of eyes and a keyboard. Everything else about this game
is checked automatically; these six are what is left.

**It should take about ten minutes.** Section A does all six in one sitting.
Sections 1 to 6 do them one at a time, if you would rather, or if you want to
re-check just one.

You do not need to know anything about how the game was built. Nothing below
assumes you have read any other document.

---

## Before you start

**Where to be.** Open Terminal and change to the folder the game lives in —
the one containing `play`, `verify` and a `termgame` folder. Everything below
is typed there.

**What it will do to your screen.** Each run opens **one** new Terminal window,
the game's own, and closes that same window when you quit. It will not touch
any of your other windows, and it does not change any Terminal preference or
setting.

**How to stop at any time.** Press `q` in the game's window. That is the only
key that ends it. If anything goes wrong, jump to **"If something is left
behind"** at the end.

**One thing worth knowing before you look at anything.** This machine has three
displays, and there is a known fault that shows up now and then: the game
occasionally cannot read the display layout, and when that happens it opens on
your **main** screen instead of the one you launched it from. It says so when
it happens — a line beginning

```
could not read the screen layout
```

If you see the game on the wrong screen, **look for that line**; it is the
evidence, and it is worth reporting whether or not you see it.

---

## A. All six in one sitting

1. **Open three or four extra Terminal windows** and leave them where they are.
   You are going to check later that they are untouched, so give them a glance
   now.

2. **Take the window you are going to type in and move it somewhere awkward** —
   near the **bottom-right corner** of a screen, and if you have more than one
   screen, a screen that is **not** your main one. This matters: it is the
   position that shows up a mistake.

3. In that window, type:

   ```
   ./check-window-placement
   ```

4. A new window opens, titled **Terminal Game**. **Do not press `q` yet.**
   Look at it, and give yourself half a minute:

   - Where did it land? (check 1)
   - What does its title bar say? (check 3)
   - Is the text a comfortable size to read? (check 4)
   - Do the walls join up into corners and crossings, and can you tell the
     player from the ghost at a glance? (check 6)
   - Watch the pink ghost cross the maze. Does anything tear, blink or blank?
     (check 5)

5. **Now press `q`** in the game window. It should close. (check 2)

6. Look at your other Terminal windows. All still there, none moved, no dialog
   box anywhere. (check 2)

7. Read what `./check-window-placement` prints. It tells you where the game
   window went and where it measured from, and does the arithmetic for you.

That is all six. Write down what you saw — your own words are what is wanted,
not a pass or a fail.

---

## 1. Where the game window lands

> *This check exists because no program in this project can ever make it. The
> game is supposed to open just below and right of the window you typed in —
> and a program has no window it was typed in. It has no keyboard and no
> screen either. This one is entirely yours.*

### What to type

First, **move the window you are about to type in somewhere awkward**. Near the
bottom-right corner of a screen is the useful place, because that is exactly
where a launcher that got the arithmetic wrong would put the game half off the
edge. If you have more than one screen, use a screen that is **not** your main
one.

Then, in that window:

```
./check-window-placement
```

It explains itself, runs the game, and waits. When the game window appears,
look at it, then press `q` in it to quit. The script then prints its verdict.

### What you should see

- A new window, titled **Terminal Game**, appearing **just below and just to
  the right** of the window you typed in — about 30 pixels each way, roughly a
  title bar's worth. Close enough that they overlap, offset enough that you can
  see both.
- It is on **the same screen** as the window you typed in.
- **All four of its edges are on that screen.** Nothing hanging off the bottom
  or the right.
- The script finishes by printing the two positions and the offset between
  them, and says which of these you are looking at:

  | It prints | What it means |
  |---|---|
  | `LANDED_RIGHT` | The offset was exactly 30 across and 30 down. |
  | `LANDED_SHIFTED` | The offset was something else. Not automatically wrong — see below. |
  | `LAYOUT_UNREADABLE` | The game could not read your display layout. See below. |
  | `NO_REPORT` | The game never said where it put its window. Report this. |

**`LANDED_SHIFTED` is not necessarily a failure.** When the offset would have
pushed the game over an edge, the launcher deliberately pulls it back on
screen, which is exactly what should happen when you launch from near a corner.
What matters is what you *see*: a window fully on screen, on the screen you
launched from.

### What counts as a failure

Any one of these:

- The game window opened on a **different screen** from the window you typed
  in.
- Part of the game window is **off the edge** of the screen — you cannot see all
  four sides of it.
- It landed nowhere near the window you typed in — the far corner, the middle of
  a different display, the top-left of the main screen.
- It opened somewhere sensible but **exactly on top of** the window you typed
  in, with no offset at all.
- The script printed `NO_REPORT`.

### The one known fault, and what proves it

If the game opens on your **main** screen when you launched it from another
one, look through the output for a line beginning:

```
could not read the screen layout
```

That line is the cause. When the game cannot read how your displays are
arranged it assumes a single 1440 × 900 screen, and against that assumption the
window you launched from is nowhere at all, so the game falls back to the main
screen. It has been seen once before, it could not be reproduced on demand, and
nobody has explained it. **If you see it, say so** — a second sighting is worth
a great deal, and this line is the only trace it leaves.

### What to write down

The two positions the script printed, the offset it worked out, which of the
four words it ended with, and — in your own words — where the window actually
appeared relative to the one you typed in, and whether you could see all of it.

---

## 2. That `q` closes the game's window and nothing else

> *The way this one fails is destructive, which is why a person has to do it.*

### What to type

First open **three or four other Terminal windows** and put something
recognisable in them — run `ls`, open a file, anything. Look at where they are.

Then, in a different window:

```
./play
```

### What you should see

- One new window opens and the game appears in it.
- You press `q`. That window closes, and closes **straight away** — within about
  a quarter of a second.
- Every other Terminal window is exactly where it was, with exactly what was in
  it.
- **No dialog box appears at any point.** In particular, nothing asking *"Do you
  want to terminate running processes in this window?"*

### What counts as a failure

- Any of your other windows closes, moves, or changes.
- A confirmation dialog appears. (If one does, click **Cancel**, not Terminate,
  and write down exactly what it said.)
- The game's window does not close when you press `q`, and you have to close it
  yourself.
- `q` does nothing at all and you have to use Ctrl-C.
- The window closes but the game's process is still running — you can tell
  because your shell prompt does not come back in the window you typed `./play`
  in.

### What to write down

Whether the game's window closed, how quickly, whether anything else on your
screen changed, and whether any dialog appeared.

---

## 3. That the title bar reads exactly "Terminal Game"

### What to type

```
./play
```

Then look at the title bar of the new window. Press `q` when you have.

### What you should see

The window's title bar reads:

```
Terminal Game
```

and nothing else.

### What counts as a failure

Anything other than those two words. In particular:

- A folder name in front of it — `NewTerminalGame — Terminal Game`.
- The name twice — `Terminal Game — Terminal Game`.
- A program name after it — `Terminal Game — python3` or `— bash` or `— zsh`.
- Your username, a path, a percentage, or a command you did not type.
- Just `Terminal`, or the name of your shell.

**One thing that is *not* a failure:** for the first half-second the title may
briefly show something from your own shell's startup — on this machine it has
shown `rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519`. That is
your login profile running before the game starts, and it settles within about
a second. Judge the title **after** the game's picture has appeared. If it is
still wrong a second or two later, that is a real failure.

### What to write down

The title, copied exactly, including any dashes and anything either side of
them. If it settled from something else, say what it started as and roughly how
long it took.

---

## 4. That the text is big enough to read comfortably

> *This is a judgement, not a measurement. If it is wrong, it is a one-line
> change, so say so plainly.*

### What to type

```
./play
```

Sit at your normal distance from the screen. Press `q` when you have decided.

### What you should see

The game is drawn in **18 point Menlo**, in a window 40 characters wide and 30
lines tall. The whole maze should be readable without leaning in, and the dots
should be individually visible rather than a haze.

### What counts as a failure

- You have to lean towards the screen or squint to make out the maze.
- The dots are too small to count.
- The other way: it is so large that the window is unwieldy on your screen.
- The characters look stretched, squashed, or unevenly spaced — that would mean
  the font is not the one intended.

### What to write down

Comfortable, too small, or too big — and if it is wrong, what size you would
want instead.

---

## 5. That nothing flickers while the ghost moves

### What to type

```
./play
```

Then **do not touch the keyboard**. Just watch. The pink ghost moves on its
own, about seven squares a second, and it will keep moving whether or not you
do anything. Watch it for twenty or thirty seconds, including while it crosses
the middle of the maze and while it turns corners. Press `q` when you have seen
enough.

Then watch it again while you *are* moving, with the arrow keys.

### What you should see

The ghost slides from square to square and **nothing else on the screen
changes**. The maze stays put, the dots stay put, and the picture never blanks,
even for an instant.

### What counts as a failure

- The screen blanks, even briefly, as the ghost moves.
- The maze or the dots flicker, blink, or appear to redraw.
- The picture tears — part of it updates before the rest.
- A text cursor is visible anywhere, blinking or otherwise.
- Moving with the arrow keys makes it worse than standing still does.

### What to write down

What you saw. "Nothing flickered" is an answer. So is "there is a flicker at
the bottom of the screen once a second or so", and that would be the more
useful one.

---

## 6. That the picture looks right

### What to type

```
./play
```

Then compare what you see with the picture in `docs/FUNCTIONAL_REQUIREMENTS.md`
section 3 — open that file alongside, it has a full-size drawing of what the
game is meant to look like. Press `q` when you have compared them.

### What you should see

- **Walls** in blue, drawn as **double lines** that **join up** with their
  neighbours. Where two walls meet at a right angle you should see a corner
  (`╔ ╗ ╚ ╝`); where three meet, a tee (`╦ ╣ ╩ ╠`); where four meet, a crossing
  (`╬`). Horizontal runs should be continuous lines, with no gaps between one
  wall square and the next.
- **A wall square with no wall next to it** should be a single solid blue block
  (`■`) — not a stray line, not a corner pointing nowhere.
- **Dots** as small dim gold squares, one on every corridor square you have not
  been to yet.
- **The player**, a bright yellow three-character block: `▐█▌`.
- **The ghost**, a pink three-character block of a *different shape*: `▗█▖`.
- **The status line** along the very bottom, in cyan, reading:

  ```
   score 0    arrows, q quits
  ```

  with the number going up as you eat dots.

- The right-hand three columns of the window are blank. That is deliberate.

### What counts as a failure

- Wall corners that do not join — a horizontal line running into a vertical one
  with a visible gap or a mismatched character.
- A lone wall square drawn as anything other than a single block.
- Being unable to tell the player from the ghost at a glance. They must differ
  **both** in colour (yellow against pink) **and** in shape.
- Any colour plainly wrong: white walls, blue dots, a status line that is not
  cyan.
- Anything drawn with letters or punctuation where the drawing shows a block or
  a line.
- The maze not filling the window, or spilling past its right-hand edge.

### What to write down

Whether the walls join up; whether you could tell the player from the ghost
instantly; and any square of the picture that looked wrong, with roughly where
it was.

---

## If something is left behind

**A game window that will not close.** Click on it and press `q`. If that does
nothing, press Ctrl-C. If *that* does nothing, close the window yourself with
Cmd-W and, if you are asked whether to terminate running processes, click
**Terminate**. Then say so in what you write down — a window that had to be
closed by hand is exactly the kind of failure these checks are looking for.

**A dialog saying "Do you want to terminate running processes in this
window?"** Click **Cancel** and write down which window it was about. This
dialog is supposed never to appear; while it is on screen it blocks every
automated Terminal command on the machine, so it is worth knowing about.

**A message beginning `LEFT OPEN: Terminal window id ...`.** The game is telling
you it deliberately did not force a window closed, because forcing it would
have raised that dialog. Close the window yourself and report the message.

**Anything else.** Copy what was printed, exactly, and hand it back with the
rest.

---

## What the machine already checked, so you do not have to

So you know where the line is. Typing

```
./verify
```

runs, in about twenty-five seconds: every automated test in the project; a
scripted window open-and-close that proves the window is sized 40 × 30 in
Menlo 18, titled *Terminal Game*, closed by the id it was created with, and
that no other window on the screen moved; and three scripted games played
through the real game code, each compared character by character against a
recorded picture. If any of it fails it says which part and why.

None of that can see a screen or press a key, which is why the six above are
yours.

---

## For whoever collects the answers

You do not need this section; it is here so that the answers can be filed
against the requirements they belong to. The six checks above are, in order,
**H1 to H6** of the implementation plan §8 and the architecture §13:

| Above | Plan | Requirement |
|---|---|---|
| 1. Where the game window lands | H1 | WIN-4 |
| 2. That `q` closes the game's window and nothing else | H2 | WIN-5 |
| 3. That the title bar reads exactly "Terminal Game" | H3 | WIN-3 |
| 4. That the text is big enough to read comfortably | H4 | WIN-2 |
| 5. That nothing flickers while the ghost moves | H5 | SCRN-7 |
| 6. That the picture looks right | H6 | SCRN-3, SCRN-5 |
