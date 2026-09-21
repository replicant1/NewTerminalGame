# PR-PIXELS-tidy — four things the reviewer saw and did not ask for

Risk: LOW — four cosmetic items in test code. Nothing here changes what any test asserts
except one added case, and a defect would be visible and local.

This is the first LOW-risk pull request of the run, so by §1.9 it merges on Copilot's pass and
a green suite, without the code reviewer. That is the tiering working rather than a shortcut:
the change that needed a HIGH review got three rounds, and this one needs none of that.

## Why these are here and not in #115

The round 3 reviewer approved #115 and recorded these four as observations, marked explicitly
as *not comments and not conditions* — *"the developer should not resubmit for them"*. It was
right: a fourth round on a valid approval, for four cosmetic items, spends a review cycle on
nothing. So they land as their own change.

## The four

1. **`tests/test_pixels_reach_the_screen.py`** — the control's failure message still read
   *"box-drawing glyphs"* after the control moved to U+2588, a block element. **The reviewer
   asked to be overruled on this one**, having drawn the line at "text that could cause a
   wrong code change" versus "text that costs a moment's confusion" — and it was right to ask.
   It is the same stale-description class it *did* raise in round 2, where a docstring
   describing the superseded control could have led a maintainer to reverse the fix.

2. **`tests/test_pixels.py`** — `_bmp`'s `depth` parameter had no caller, and at `depth=24`
   would have built a BMP with no row padding, which a conformant 24bpp file has. The reviewer
   measured the consequence: on a padded 3×2 file `histogram` counts the padding as two
   spurious black pixels. A later test reaching for that parameter would have certified a depth
   the parser cannot read. It is now a module constant with that reasoning written beside it.

3. **An unused `import pytest`** — there is no lint config in this repository, so nothing
   catches these.

4. **`TestBlank` did not pin its own boundary**, where `TestNear` pins its tolerance at exactly
   24 and exactly 25. Now it does: 98 % dominant is blank, 97 % is not.

## Scrutiny

- `tests/test_pixels.py` — the `DEPTH` constant. Check the comment explains the *measurement*
  rather than merely asserting the restriction, so that whoever needs 24bpp knows what they
  have to fix first.

## Suite

`.venv/bin/python -m pytest -q` → **999 passed, 12 deselected**, up from 998 by the added
boundary case. `-m needs_window` → **10 passed, 2 failed**, unchanged: those two fail because
Tk paints nothing here, which is what they were written to report.
