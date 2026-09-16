# WI-21 — the five questions for a human

**Written by:** DEV-A, WI-21, run 6.
**Interpreter:** `/usr/bin/python3` — Python 3.9.6. **Toolkit:** Tk **8.5.9**.
**Windows opened:** nine, each under 3.1 seconds, **each confirmed gone.**
**Screen gate:** held exclusively, granted and released through the conductor.

---

## 0. Read this first: every question below is OPEN

**Nothing in this document is an answer.** Five questions have been open for a
whole run, and five developers in a row have declined to close any of them from
a measurement. Each was right, and this document is the sixth refusal.

The job of this work item was to make the five questions **cheap and
unambiguous to answer**, not to answer them. So each one below carries an exact
command, exactly what to look at, and what it would cost to change if the
answer is no.

**For the sweep:** no row anywhere may claim **test coverage** for anything in
this document. Where the suite cannot reach something, the honest category is
*covered by observation, not by test*, citing this file. And nothing here is
even that: the observations in §6 are about the **instruments**, not about the
questions. **The five questions have no evidence of any kind yet.**

---

## 1. The rule that shaped this item, and the split it forces

**Section 4 rule 5: no agent may run `/usr/bin/python3 -m terminal_game`.**

The finished game is unbounded by design. `q` is the only way out of a finished
game (CTRL-4, END-6), so it waits for a person — which makes it exactly the
thing an agent must not start, because launched by an agent nobody is there to
press it and it holds a window open on somebody's desktop indefinitely. **It is
the user's to run.**

So there are two instruments, and **every answer below says which one it would
come from**. This distinction is not pedantry; conflating the two is the one
dishonest move available to this work item.

| | What it is | What it can honestly answer |
| --- | --- | --- |
| **the harness** — `tools/the_questions.py` | `build_game` with every argument at its default, at the real anchor, painted by the real surface, under two deadlines | the titlebar, where the window landed, whether the type is comfortable |
| **the joinery view** — `tools/the_look.py --view joinery` | WI-16's lattice — the only thing on this project that has ever put a crossing glyph on a screen | whether the wall strokes meet |
| **the real game** — `/usr/bin/python3 -m terminal_game` | the shipped exit path, unbounded, **yours to start and nobody else's** | a whole game played to an ending, a real `q` out of a *finished* game, a close button pressed by a hand, the process exiting |

**The harness creates the window identically** — same `build_game`, same
anchor, same font, same surface — which is why it answers the first three
faithfully. **It is not the shipped exit path.** Its sitting ends on a
scheduled `session.quit`, not on a key you pressed, and it has an unconditional
backstop under that which the game does not have and should not have.

---

## 2. Before you look — otherwise this reads as a bug

**The window will open at the fixed fallback position `(120, 120)` on your
primary display. It will not appear near your pointer.**

That is expected, and the reason is **geometry, not permission**. Measured in
`docs/findings/WI-14-anchor-query.md` and confirmed on four windows in
`docs/findings/WI-18-the-game-on-screen.md`, and on six more here: the toolkit
reports the pointer in **whole-desktop** coordinates — it read `(-175, -448)`, a
second display up and to the left — while `winfo_screenwidth/height` and the
virtual root describe only the **primary**, at 1512 x 982. `maxsize()` knows the
desktop is 5120 x 2422 but **gives no origin**. There is therefore no rectangle
to bound the pointer into, and an anchor that cannot be bounded is correctly
treated as *nothing seen* (contradiction **C-7**).

**Granting Accessibility would not change this.** Please do not grant one for
this. If you dislike where the window lands, the fix is a better fallback
position — `FALLBACK_POSITION` in `terminal_game/shell/anchor.py` — and it is
one constant.

Confirmed on every one of this item's six own windows:
`"anchor_saw_something": false, "anchor_failure": null` — **the query ran, saw
nothing, did not fail, and did not prompt** — and the window landed at
`(120, 120)` each time.

---

## 3. Question 1 — A1: does the titlebar read exactly *Terminal Game*?

**OPEN.**

```
/usr/bin/python3 tools/the_questions.py
```

**Asked of:** the bounded harness. Also visible on the real game, and on every
window in §6.

**Look for:** the strip along the top of the window. Exactly `Terminal Game`,
with nothing before it and nothing after it — no file name, no `python3`, no
trailing marker.

**Why five developers have refused to close this.** Tk has read that string
back to us **on every window this project has ever opened** — twenty-one in
WI-16 and WI-17, four in WI-18, nine here. It read back `Terminal Game` every
single time. **That is still not an answer**, because reading a string back
from the toolkit that set it is not a person seeing a titlebar: the reported
name and the rendered titlebar are different things, and under candidate 1 they
were measured to *differ*. The harness reports the read-back under the field
name `title_read_back_which_is_not_an_answer_to_A1`, so that nobody can quote
it as one by accident.

**If the answer is no:** `WINDOW_TITLE` in
`terminal_game/shell/window_owner.py` is the one constant, and nothing composes
anything around it.

---

## 4. Question 2 — A10 / SCRN-3: do the strokes actually meet?

**OPEN.**

```
/usr/bin/python3 tools/the_look.py --view joinery --seconds 20
```

**Asked of:** WI-16's joinery view — **and not a game screen.** This matters
more than it looks.

**Look for:** a lattice filling the whole window.

```
╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╗
║   ║   ║   ║   ║   ║   ║   ║   ║   ║
╠═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╬═══╣
```

A hairline of black where two cells meet, or a stroke that steps sideways
instead of running straight, is a no. If it reads as solid continuous rules, it
is a yes.

**Why here rather than on the game.** The specimen picture in the requirements
**contains no crossing glyph at all**, and WI-8's census over 200 generated
mazes found `╬` in only **55 of 200** seeds (61 occurrences). So a game screen
may never show you the junction most likely to be wrong. The joinery view puts
every junction WI-8 can produce on one screen, crossing included, and it is the
only thing on this project that has ever rendered one.

**Why the measurement does not settle it, stated for the fifth time because it
is the most tempting shortcut on the project.** WI-2 measured that all 113
glyphs the picture uses share **one advance width** in Menlo, at 14, 16, 18 and
20 point alike, with a control showing that glyphs Menlo *lacks* fall back to
visibly different advances — so the uniformity is the font's own coverage and
not a fallback artefact. **That is a good measurement and it settles the
spacing.** It proves the glyphs land in the right *places*. Whether the strokes
**touch** is a property of the glyph outlines, and the only instrument that can
read it is an eye.

**If the answer is no:** the glyph table in
`terminal_game/presentation/wall_glyphs.py`, or `FONT_FAMILY` in
`terminal_game/shell/grid_surface.py`.

---

## 5. Question 3 — A4: is the type comfortable?

**OPEN.**

```
/usr/bin/python3 tools/the_questions.py --sizes 14,16,18,20 --seconds 15
```

**Asked of:** the bounded harness. Four windows in turn, the **same game** at
four sizes, so the answer is a comparison rather than a guess.

**Look for:** can you read the bottom row without leaning in, and tell the
player's shape from the ghost's at a glance?

**The ladder, measured here on the assembled game** — and it reproduces WI-16's
table on the static view exactly:

| Point size | Cell | Window | Canvas items |
| --- | --- | --- | --- |
| 14 | 8 x 16 | 320 x 480 | 706 |
| **16 (current)** | **10 x 19** | **400 x 570** | 706 |
| 18 | 11 x 21 | 440 x 630 | 706 |
| 20 | 12 x 24 | 480 x 720 | 706 |

**If the answer is no:** `FONT_POINT_SIZE` in
`terminal_game/shell/grid_surface.py` is one constant either way, and the
window size follows from it automatically. The table says what each costs.

---

## 6. Question 4 — A2 revised / WIN-4: did it land somewhere you could see it?

**OPEN.**

```
/usr/bin/python3 tools/the_questions.py
```

**Asked of:** the bounded harness, which asks the **real** anchor query exactly
as the shipped command does.

**Look for:** where the window appeared, and nothing more ambitious than that.
**Read §2 first.** The question to answer is the modest one — *could you see
it?* — and if the answer is no, the fix is a better fallback, not a permission.

**Why the question is the modest one.** WIN-4 asks for the window to land *"a
little below and to the right of whatever window the player was last looking
at, so it always lands somewhere visible"*. Both available readings deviate
from that: a literal anchor needs a permission nobody has, and a fixed corner
is not below-and-right of anything. **A2 revised** takes the pointer instead,
because it serves the requirement's own stated purpose where a fixed corner
cannot — and then C-7 means that on *this* machine, as configured, it falls
back anyway.

---

## 7. Question 5 — five rulings, decided rather than seen

**ALL FIVE OPEN.** These need no screen. Each was decided here for a stated
reason, each is recorded rather than hidden, and each names **the one place a
reversal lands**.

```
/usr/bin/python3 tools/the_questions.py --checklist
```

### A3 / C-2 — WIN-5 against END-5 and END-6

*Does the window close the instant the outcome is decided, or when the player
presses `q` after seeing the final picture?*

WIN-5 says the window closes *"as soon as the game ends"*; END-5 says *"the last
picture stays on screen"*; END-6 says `q` is *"the only way to leave a finished
game"*. **All three cannot hold on the literal reading of WIN-5** — this is a
contradiction in the specification, not an ambiguity.

**As built:** the second reading. Outcome decided → final picture stands →
player presses `q` → the window closes itself.
**Lands in:** `terminal_game/application/session.py`, and nowhere else.
**Reversing it costs:** one work item's worth of change; the WIN-5, END-5 and
END-6 sweep rows follow it.

### A8 / C-5 — the dot on the losing turn

*When the ghost catches the player on a square that still has a dot, is the dot
still eaten and still scored?*

The specification never says. Both readings satisfy END-3, and it changes the
last number the player ever sees.

**As built:** yes — caught **and** the dot counts. Not a coin flip: END-3's own
wording, *"eating the last dot on the square the ghost is standing on is a loss,
not a win"*, only parses if the eating happens.
**Lands in:** `terminal_game/domain/turn_resolver.py`, already landed.
**Reversing it costs:** a follow-up branch on WI-11, **never** a session change —
scattering the step order is exactly what caution C6 exists to prevent.

### A9 / C-6 — a winning score the game cannot reach

*STAT-3's winning example scores 274. Do you want it changed?*

**A full game is worth 259 to 271 points, mean 264.5** — the score is the
corridor count less one, and the generator never reaches 275 corridors. So
`CLEARED  score 274` **cannot occur**.

**As built:** kept as an exemplar of the *format*, which is all it was ever
needed for. No test and no sweep row asserts 274 as an achieved score.
**Lands in:** WI-13's formatting tests and the sweep rows.
**Reversing it costs:** nothing waits on it. You may simply want to know your
example is impossible.

### A7 / C-3 and C-4 — the status line's exact wording

*The literals disagree with the specimen picture by one leading space, and the
two ending examples cannot both come from any single padding rule. Are the
literals what you want?*

Measured: STAT-2 is 26 characters with no leading space where the picture's row
29 has 27 with one; and the two STAT-3 examples differ in three places at once,
so **no padding rule of any kind fits** — per-ending templates stop being the
simplest reading and become the only one.

**As built:** the literals are normative and reproduced exactly, as one template
per ending; the picture's leading space is illustrative.
**Lands in:** `terminal_game/presentation/status_line.py`, and nowhere else.
**Reversing it costs:** three template constants in one module. Every other item
obtains row 29 from that module rather than typing it, so a reversal propagates.

### The ghost's start-corner tie-break

*START-2 names the furthest corridor square from the player, singular, but on a
real maze four corners tie. Should the tie be drawn at random?*

**Measured over 200 mazes:** the ghost starts at `(1, 1)` in **115** and
`(1, 27)` in the other **85**, and **never on the right**. Two distinct opening
positions over two hundred distinct mazes. Nothing in the requirements is
broken by it — the ghost genuinely is a furthest corridor square every time —
but a player would notice over a few games.

**As built:** broken deterministically, because WI-6's work item was handed no
random source where WI-5's and WI-7's both were, and inventing one would be
inventing a requirement.
**Lands in:** `ghost_start_square` in
`terminal_game/domain/opening_position.py` — one extra parameter and one draw
over the tied squares.
**Reversing it costs:** two hand-built tests change. The 200-seed property tests
assert *"no corridor square is further"* and pass either way, which is as it
should be.

---

## 8. The game itself — yours to run, and the only thing that answers the rest

```
/usr/bin/python3 -m terminal_game
```

Add `--seed N` to replay one particular maze.

**No agent on this project may start that command**, for the reason in §1. It is
also the only thing that can answer any of the following, and **the harness has
not answered and cannot answer them**:

- **A whole game played to an ending.** *Nobody has ever played one.* Every
  on-screen run this project has made ended `UNDECIDED` — WI-18 with two dots
  eaten out of 259–271, and every one of this item's own six windows with zero.
  A game reaching either ending exists only headless, in WI-19's suite. **If you
  play one through, you will be the first person to see it.** Expect `CAUGHT`
  long before `CLEARED`: clearing means eating 259 to 271 dots.
- **A real `q` ending a *finished* game.** The harness lets you press `q`, but
  its own deadline would have ended the sitting anyway; only the unbounded game
  proves `q` is what got you out. This is END-6, and it is the requirement the
  whole "no agent may run it" rule turns on.
- **The close button, pressed by a hand.** WI-17 and WI-18 evaluated the same
  `WM_DELETE_WINDOW` command a window manager sends, which is the real path —
  but nobody has clicked it.
- **The process exiting cleanly**, and the terminal you started it from coming
  back with nothing printed to it (CTRL-5).

---

## 9. What the harness did on a real screen

**This section is about the instrument, not about the questions.** Nothing in it
is evidence for any of the five.

Nine windows, all reaped. Afterwards `pgrep` found no tool process under any of
the six names this project has used, and System Events counted **0** processes
whose name contains "Python".

| # | What was run | Held | Reaped | What it said |
| --- | --- | --- | --- | --- |
| 1 | `the_questions.py --seconds 2` | 2.09 s | yes | (120, 120), 400 x 570, 706 items all `text`, 13 frames |
| 2 | `the_questions.py --seconds 3` | 3.08 s | yes | phase **`ended`** with nothing pressed, 21 frames |
| 3–6 | `the_questions.py --sizes 14,16,18,20 --seconds 3` | ~3.05 s each | yes ×4 | the ladder in §5, all at (120, 120) |
| 7 | `the_look.py --view joinery --seconds 3` | 3 s | yes | **714** items, all `text` |
| 8 | `the_look.py --view game --seconds 3` | 3 s | yes | **698** items, all `text` |
| 9 | `window_manners.py --exercise keys` | 1.49 s | yes | player moved, `z` ignored, `q` ended it, output empty |

Short-first, as every lane on this run has done: one 2-second window to prove
the mechanics and the reap before anything longer.

**One thing changed between windows 1 and 2, and it is worth recording.** Window
1 ended with the session's phase still `playing`, because the sitting's single
deadline was `owner.end_session` — which takes the window out from under the
session rather than asking it to stop. That is the same shape of defect WI-17
measured on the close button. The sitting now schedules **two** deadlines before
the event loop is entered: `session.quit` at N seconds, which is what
`--seconds` does on the production entry point and which leaves the phase
`ended`; and `owner.end_session` 1.5 s under it, which asks nobody's permission
and fires if the session is ever wedged. **A faithful route and an unconditional
route are not the same route.** Window 2 onwards reached `ended`.

**Windows 7, 8 and 9 were not for this item.** WI-22 changed two on-screen tools
and had no desktop slot, and said so plainly. Both of its call sites were run
here, being the last screen turn of the run: `the_look.py --view game` painted
**698** items and `--view joinery` **714**, which are exactly the figures WI-16
recorded before the change, and `window_manners.py --exercise keys` behaved
identically to WI-17's record. Its judgement that `frame_for` is
character-for-character the expression it replaced **holds on a real screen as
well as in the suite.**

**On the modal sheet**, stated the way amendment 6 requires: *"no modal sheet
was raised"* is a negative about the user's environment and is not established
by running the thing that might raise one. The structural argument is WI-3's and
unchanged — the window belongs to this process, so there is no second
application left holding one. What was **observed** is the weaker, sufficient
fact: nine processes exited on their own and none was there afterwards.

**On the harness prompting for anything**, stated the same way: the privileged
anchor route is **structurally absent** from the code, which covers every run on
every machine, and that absence is WI-14's finding rather than this one's. What
this item adds is the same shape one level up: `tools/the_questions.py` **imports
no `subprocess`, no `multiprocessing`, no `pty`, and not
`terminal_game.__main__`, and calls nothing that launches a process** — so it has
no way to start the unbounded game at all. There is a test walking the module's
syntax tree that says so. *Absent, not guarded.*

---

## 10. What this document does not tell you

- **Any of the five answers.** That is the point of it.
- **Anything a person has seen.** Every window above was looked at by a
  scheduler, not an eye.
- **Whether the five colours can be told apart** (SCRN-5's colour half). WI-16's
  `colours` view is the instrument; the outline half is already settled in
  WI-12's tests.
- **Anything about a modified arrow.** **A11** — `KeyPress` carries no modifier
  state, so control-Up is indistinguishable from Up and moves the player. Ruled
  a known gap in amendment 9 and not touched here.
- **Flicker at the ghost's cadence over a long game.** Six sittings of three
  seconds is not a game. The repaint cost is in
  `docs/findings/WI-2-cell-metrics.md` (0.68 ms median against a 143 ms budget),
  and the rest belongs to the game you run yourself.
