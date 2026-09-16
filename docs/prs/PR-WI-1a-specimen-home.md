# WI-1a — The specimen fixture leaves `tests/`

**UNBLOCKS WI-10 RULE 6.** `tools/walking_skeleton.py` imported
`tests.specimen`, which is the one violation of *"nothing that is not a test
depends on test code"* on `main`. It is gone; nothing under `terminal_game/`
or `tools/` imports out of `tests/` any more.

**Developer:** DEV-B · **Branch:** `r6/wi-1a-specimen-home` · **Base:** `main`

Amendment 2 ruled that the specimen fixture is right to be shared and wrong
to live under `tests/`, and made the destination DEV-B's call under the
first-lander rule. DEV-C asked for it on PR #45 because WI-10 cannot land
rule 6 while the violation stands. This is the answer, landed rather than
just named.

## The destination: `terminal_game/presentation/specimen.py`

Three reasons, in order of weight:

1. **The dependency runs the right way for everyone.** Tests and tools both
   import *down* into the package; nothing imports out of `tests/`. That is
   the whole point of the move, and a top-level module or a `fixtures/`
   package would achieve it too — the next two reasons are why this one.
2. **It is a picture, and this is the layer whose job is to reproduce it.**
   `frame.py`, `wall_glyphs.py` and `frame_composer.py` all sit beside it.
   Assumption A6 makes the specimen normative for the grid-to-screen
   mapping, which is precisely this layer's contract, so the reference and
   the code obliged to match it are in one place.
3. **It adds no new top-level package**, so WI-10's fourth rule — *there is
   exactly one root package* — stays one line and needs no exception.

**The objection, named:** it puts requirements-reference data inside the
shipped package, and the game itself never reads it. I accept that. It is
about forty lines of string constants, it is data rather than behaviour, and
co-locating it with the code that must reproduce it is worth more than the
purity. If the technical lead disagrees, the fallback is a top-level
`fixtures/` package and WI-10's rule 4 gains an exception.

## I moved it and fixed all five importers, including DEV-C's

DEV-C offered to make the one-line change in `tools/walking_skeleton.py`
themselves, or to stay out of the way. I did all five, because a rename that
leaves `main` broken between two landings is worse than touching one import
line in another lane's file. If DEV-C would rather have done it, say so and
I will not do it again.

| File | Change |
| --- | --- |
| `tests/specimen.py` → `terminal_game/presentation/specimen.py` | moved, and its docstring now says why it lives there |
| `tests/test_frame.py`, `tests/test_grid_surface.py`, `tests/test_wall_glyphs.py`, `tests/test_walking_skeleton.py` | import updated |
| `tools/walking_skeleton.py` | import updated, and the docstring that named the old path |

## A violation of my own, found while here

`tests/test_frame.py` contained the STAT-2 literal
`score 0    arrows, q quits`. I wrote that in WI-1, before WI-13 existed —
but **A7 confines every status-line literal to WI-13**, and my file had one.
Replaced with a non-literal; the test only ever needed *some* cyan text on
row 29.

## One thing WI-10 should not flag

`specimen.py` still contains the STAT-2 text, as `SPECIMEN_STATUS_ROW`. That
is a transcription of the requirements' **picture** — it is the evidence
behind contradiction C-3, which exists precisely because the picture and the
STAT-2 literal disagree by one leading space. It is not a template anybody
composes from. A naive literal-scan will flag it and should not.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 533 tests — 533 passed, 0 failed, 0 skipped
```

No behaviour changed: this is a move, five imports and one test literal.

```
grep -rn "from tests\." terminal_game tools   ->   no matches
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
