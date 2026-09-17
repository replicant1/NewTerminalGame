# WI-14c — let the anchor reader be injected

**Branch:** `r7/wi-14c-anchor-seam`, cut from the tip of `main` at `a4245a2`.

**Suite:** `.venv/bin/python -m pytest -q` — **925 passed, 0 failed, 0 skipped, 7 deselected**.

---

WI-14b wired the placement but hard-coded the shipped `NoAnchor` reader, so there was no
way to drive placement from a test. Lane C's **WI-16b** — the guard that asserts the
assembled game actually places its window — was left holding **9 red tests** on exactly
that missing keyword, and correctly refused to weaken them.

## The argument is not convenience

**Ground rule 1.6 forbids the default suite from querying the desktop.** So a placement
test cannot use the shipped reader. Without a seam, the only possible test of placement is
one marked `needs_window` — excluded by default, and therefore **unable to catch the very
defect WI-14b existed to fix**.

That is worth stating as a general thing, because it is the second time it has bitten:
**a capability with no way to test it by default is how the placement defect survived in
the first place.** `placement.py` was complete, tested and unreachable from any default
test of the assembly.

## The change

`anchor_reader=None` on **`build_game`** as well as `Game`, defaulting to
`placement.no_anchor()` and passed to `placement_for` in `Game.place()`. **Nothing about
what ships changes.**

It is on `build_game` because `build_game` is what the journeys use. Lane C offered to
build to whatever shape I chose; I took the one it asked for, because it is already coding
against it and any cleverness of mine would cost it a rewrite for no gain.

## The tests, and the control

- the game **asks** the reader it was given, and the window lands where
  `below_and_right_of` says for that anchor;
- **the control: two different anchors give two different positions.** A game that asked
  and then ignored the reply would pass the first test alone whenever the fallback happened
  to agree.

## Still not WIN-4

The shipped reader is unchanged and still follows nothing. This adds a seam for tests; it
does not add an anchor. The trace row stays **not met, wired to the fallback**.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
