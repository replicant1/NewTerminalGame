# WI-13 — The status-line literals, measured

**Measured by:** DEV-A, WI-13, run 6
**Why it is here:** contradictions C-3 and C-4 were predicted in the
implementation plan from a reading of the specification. This records them as
numbers taken from the specification file itself, so that whoever rules on
assumption A7 is ruling on a measurement rather than on a description of one.

---

## What was run

`/usr/bin/python3`, over `docs/FUNCTIONAL_REQUIREMENTS.md`: the inline code
spans of the STAT-1 to STAT-3 paragraph extracted with a regular expression
rather than retyped, and row 29 of the specimen picture read from
`tests/specimen.py`, which was itself transcribed from the same file in WI-1.

## What came back

| Literal | Source | Length | Column of `q quits` |
| --- | --- | --- | --- |
| `score 0    arrows, q quits` | STAT-2 | **26** | 19 |
| `CAUGHT  score 37   q quits` | STAT-3 | **26** | 19 |
| `CLEARED  score 274  q quits` | STAT-3 | **27** | 20 |
| `' score 0    arrows, q quits'` | specimen picture, row 29 | **27** | 20 |

## C-3, as a number

The specimen picture's row 29 is **27** characters; STAT-2's literal is
**26**. The difference is exactly one **leading** space; the remainder is
identical character for character.

So the two disagree about which column the line starts at, and nothing else.
A7 takes STAT-2 as normative and the picture's leading space as illustrative,
so the text begins at column 0 of row 29.

## C-4, as a number

`q quits` cannot be at column 19 and at column 20 under one padding rule.
Nor can any rule that pads the score to a fixed width produce both, because
the two examples differ in *three* places at once:

| | word | spaces after the word | spaces after the score |
| --- | --- | --- | --- |
| loss | `CAUGHT` (6) | 2 | 3 |
| win | `CLEARED` (7) | 2 | 2 |

A rule aligning `score` would need one space after `CLEARED` where the
literal has two. A rule aligning `q quits` would need three spaces after 274
where the literal has two. The examples are internally inconsistent, and A7's
resolution — reproduce each example as its own template — is the only one
that reproduces both.

**The consequence is visible to a player**: because the templates are
literal, the line grows and shrinks with the number of digits in the score
rather than holding a column. `CAUGHT  score 7   q quits` is 25 characters;
`CAUGHT  score 264   q quits` is 27.

## One number that makes STAT-3's second example unreachable

A whole game is worth **259 to 271 points, mean 264.5** — measured over 200
mazes in `docs/findings/WI-6-start-squares.md`, one dot per corridor square
less the player's own.

**`CLEARED  score 274  q quits` is therefore illustrative and not
reachable.** The template reproduces it exactly, because A7 makes the
specification's literal normative, but no player will see 274 and no test
should assert that a game ended on it. WI-19's win path will end somewhere in
259–271.

## What a ruling would cost

Both contradictions are confined to two files:

- `terminal_game/presentation/status_line.py` — `PLAYING_TEMPLATE`,
  `CAUGHT_TEMPLATE`, `CLEARED_TEMPLATE`;
- `tests/test_status_line.py` — `STAT_2_LITERAL`, `STAT_3_LOSS_LITERAL`,
  `STAT_3_WIN_LITERAL`.

A ruling for the specimen picture over STAT-2 (C-3) is one leading space in
`PLAYING_TEMPLATE`. A ruling for a single alignment rule over the two
examples (C-4) replaces the two ending templates with one formatting
function, and changes at most one of the two STAT-3 literals — whichever the
user declines to keep.
