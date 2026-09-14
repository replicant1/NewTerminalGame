# WI-6 — the status line

**Branch** `wi-6-status-line`.
**Stacked on `wi-10-rules-outcome` at `1d37240`** — four deep:
`wi-7-game-state` → `wi-8-player-move` → `wi-10-rules-outcome` → this. WI-6
depends only on WI-7, but `wi-10-rules-outcome` already contains WI-7 and WI-8,
so stacking there was cheaper than a fresh integration. **Read its diff against
`wi-10-rules-outcome`.**
**Lane** A (DEV-A). **Local mode.**
**Suite** `python3 -m unittest discover` — **400 passed, 0 failed, 0 skipped**.
**Windows opened: none.** Pure presentation.

Requirements: **STAT-1, STAT-2, STAT-3, SCRN-6**.

## What is new

| File | What it is |
| --- | --- |
| `terminalgame/presentation/status_line.py` | `status_text`, `status_row`, `score_field`, `STATUS_COLOUR`, `StatusLineWillNotFit`. |
| `terminalgame/presentation/__init__.py` | **DEV-B's file, byte for byte.** See below. |
| `tests/test_status_line.py` | 29 tests. |

```python
from terminalgame.presentation.status_line import status_row, STATUS_COLOUR

row = status_row(state, width)     # exactly `width` characters
```

`status_row(state, width=REQUIRED_WIDTH)` is what WI-5b wants: text already
padded to the row, plus `STATUS_COLOUR` to draw it in. **WI-5b should pass the
width it is composing at** rather than lean on the default, which exists for
callers with no frame.

## One rule, and it reproduces all three quoted lines exactly

The specification gives three examples and never states a rule:

```
during play    ' score 0    arrows, q quits'
on a loss      'CAUGHT  score 37   q quits'
on a win       'CLEARED  score 274  q quits'
```

They are one shape. **The score is `score <n>` left-justified in nine columns,
with two spaces between it and whatever follows.** During play the line is
indented one space; on an ending, the ending's name takes the front. Nine
columns because `score ` is six and a 19 x 29 maze holds fewer than three
hundred dots, so three digits covers every score this game can reach.

That single rule produces all three lines character for character, which is the
reason to think it is the rule they were written from — rather than three
unrelated strings that happen to look similar.

## The leading-space question — decided, and an assumption

Read from the source rather than from the summary of it. The picture's status
row is **line 71** of `FUNCTIONAL_REQUIREMENTS.md`, inside the code block, and
is **27 characters beginning with a space**. STAT-2 quotes the same line inline,
in backticks, as the same 26 characters **without** it.

**This keeps the space.** Three reasons:

1. **The picture is a verbatim code block and preserves whitespace exactly.**
   An inline backtick quote is prose, and a leading space inside one is
   invisible to a reader and trivially lost in transcription. Where two pieces
   of evidence disagree, the one that *can* carry the detail is the better
   witness.
2. **The maze's left wall stands at column 0**, so one space lifts the status
   line off it rather than butting it against the corner.
3. **WI-2's skeleton, already on `main`, writes it with the space.** Choosing
   the space agrees with the tree; choosing against it would mean changing
   working code to match the weaker of two readings.

**This is an assumption, not a ruling — the user has not been asked.** It is one
constant to change: `PLAY_INDENT`.

**The ending lines are not indented.** STAT-3 is the only evidence for those two
and shows no leading space, and unlike STAT-2 there is no picture to contradict
it. So each line follows its own evidence. That asymmetry is deliberate and is
the sort of thing the user may want to look at — it is on the human-check list
below rather than smoothed over.

## STAT-3's alignment — checked, and incidental

`q quits` begins at **column 19** on a loss and **column 20** on a win. Checked
rather than assumed, and there is a test asserting the two quoted lines really
do disagree, so the judgement below rests on a measurement.

**It is incidental, and the decisive reason is not the arithmetic.** A game ends
one way. **No player ever sees both lines**, so alignment between them is
unobservable. The difference falls out entirely of `CAUGHT` being six letters
and `CLEARED` seven — the score field is the same nine columns in both and so
are the gaps around it, which a test pins by asserting the column difference
equals the difference in the two words' lengths.

Forcing them to agree would mean departing from a line the specification quotes
in order to fix something nobody can see. So: reproduce both quotes exactly, and
record that the misalignment was noticed and judged rather than missed.

## How the tests avoid proving nothing

**The three literal strings are transcribed from the specification**, not
assembled by the test from the same parts as the code. A status line asserted
equal to a string the test built would agree with the implementation however
wrong both were. These are an external oracle.

Two green results would otherwise be meaningless, and each has a test that
answers differently:

- **if the score were never updated** — several tests use two different scores
  and assert the lines differ; one **plays a real game** through
  `advance_player`, asserts the line tracks `state.score` at every step, and
  then asserts the score both rose above zero and took more than one value, so
  a walk that never ate a dot would fail rather than pass vacuously;
- **if the ending were never distinguished** — the loss and win lines are
  asserted to differ, and each is asserted **not** to contain the other's word.

The same shape guards the keys: the ending lines must not offer `arrows`
(END-5), and a separate test asserts the play line **does** — without which the
first would pass against a line that never mentions the arrow keys at all.

## Cross-lane: what I read rather than agreed

**DEV-B is live on `wi-5b-frame-composition`** (worktree
`agent-a8ddd11bcf04cac47`, head `bc21558`) — the frame composer, which is the
thing that will *place* my status row. Both their branches already carried
`terminalgame/presentation/__init__.py`.

**I took their blob verbatim.** `git cat-file blob 6b5672e2…` straight into
place, then hashed my file and confirmed it is the same `6b5672e2…` — identical
on `wi-5a-wall-glyphs` and `wi-5b-frame-composition` too. Two identical blobs
merge clean where two different ones conflict. This is the "one of you writes
it, the other reads that exact blob" rule, and it is why I read rather than
agreed.

**I also ran DEV-B's own `tests/test_layering.py` from
`wi-5b-frame-composition` against this tree**, because their WI-5a added a
`PresentationLayerTest` that will scan my module once the branches meet. All
four of their Presentation guards pass on `status_line.py`:

| Their guard | Result |
| --- | --- |
| Presentation imports only the Domain and the screen port | pass |
| Presentation never reaches for the terminal adapter | pass |
| Presentation reads no key, writes no terminal, never sleeps | pass |
| The Domain does not import the Presentation layer | pass |

The one test that failed is `test_the_presentation_layer_is_where_it_is_said_to
_be`, which asserts `wall_glyphs.py` exists — it is on their branch, not mine.
After the merge both files are present and it passes. That is an artefact of
running their file against my tree in isolation, not a defect in either.

**Their `test_layering.py` is a strict superset of mine** — it already contains
my WI-7 `uses_global_random` work and my `game_state.py` line, because they
merged `wi-7-game-state`. **I have not touched that file in WI-6**, so no
conflict is expected there.

**One thing their guard leaves open, which my module now also rests on.** Their
`PRESENTATION_MAY_IMPORT` permits `terminalgame.screen.port`, and their comment
records it as needing a ruling: plan §3 says "Presentation depends on Domain,
and on nothing else" while in the same breath asking Presentation to produce
"characters and colours", which it cannot name without the port. `status_line.py`
imports `Colour` and `REQUIRED_WIDTH` from the port, so **if that ruling goes the
other way, this module changes with `wall_glyphs.py`.** I have followed the
convention already in the tree rather than opening a second front.

## A deliberate omission, recorded so nobody "fixes" it

**`tests/test_layering.py` is untouched, and `status_line.py` is deliberately
not added to their `PresentationLayerTest`'s named-module list.**
`files_under("presentation")` sweeps it automatically, so every guard above
already applies to it. Naming one module is enough for that list's purpose —
catching the layer being moved or renamed — and naming a second would be an
adjacent-line edit to the one file the other lane is editing.

**This absence is a decision, not an oversight. Do not add it.**

## Deviations, for a ruling

1. **`StatusLineWillNotFit`** is raised when the row is too narrow. §11.8, and
   the reason is sharper than usual: truncating drops the *end* of the line,
   and the end is the part that says which keys work. A status row that has
   quietly lost `q quits` is worse than a loud failure, because END-6 makes
   that the only way out of a finished game.
2. **`status_row` pads to the full width** rather than returning a ragged
   string. STAT-1 says the row shows the score and the keys "and nothing else",
   and a short string would leave the tail of the previous frame's line on
   screen — which matters most on a loss, whose line is *shorter* than the play
   line. There is a test for exactly that case.

## Assumptions

- **The leading space** — as above. Assumption, not a ruling.
- **The ending lines' lack of one** — the same question seen from the other
  side, resolved by following each requirement's own evidence.
- Q1, Q2 and Q3 are untouched by this item.

## Contradictions found

**None new.** The one this item was sent to settle — the picture against STAT-2
— is §6 of the plan's own list, and it is now decided and pinned rather than
outstanding.

One observation: **STAT-2 says "with the score kept up to date", which is not
something this module can fail at.** The line is computed from the state every
time it is asked for; there is no cached score to go stale. "Kept up to date"
becomes a property of the loop calling this often enough, which is WI-11's, and
the test that plays a real game is the closest this item can come to it.

## What needs a human

1. **The leading space**, and the asymmetry that follows from it: the play line
   is indented one column and the two ending lines are not. Both follow the
   specification's own evidence for each, but a person looking at the screen may
   simply prefer them to agree. One constant, `PLAY_INDENT`, and one decision
   about whether the ending lines should carry it too.
2. **Whether Presentation may import the screen port** — DEV-B's open question,
   which this module now also depends on.
3. **Nothing else.** No window was opened; both remaining questions are
   preferences rather than measurements.

## Commits

| | |
| --- | --- |
| `26232d6` | WI-6: the status line |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
