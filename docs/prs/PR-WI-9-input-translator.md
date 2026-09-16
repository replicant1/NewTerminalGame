# WI-9 — The input translator

**ANNOUNCING, per the first-lander rule: this branch lands the intent
vocabulary — `Intent`, `IntentKind`, `QUIT`, `move(direction)` — in
`terminal_game/presentation/input_translator.py`. WI-15's session controller
consumes it and should not declare a second one. Directions are *not*
declared here: they are `terminal_game.domain.maze.Direction`, which WI-5
landed and WI-7 already conforms to.**

**Developer:** DEV-B · **Branch:** `r6/wi-9-input-translator` · **Base:** `main` at `5e878b5`
**Iteration:** M1 · **Depends on:** WI-1 (landed)

Raw key events become intents. The four arrows become Move; `q` and `Q`
become Quit; every other key becomes nothing, and nothing is echoed anywhere.

## What is in it

| File | |
| --- | --- |
| `terminal_game/presentation/input_translator.py` | `translate`, `Intent`, `IntentKind`, `QUIT`, `move`, `ARROW_KEYS`, `QUIT_KEYS` |
| `tests/test_input_translator.py` | 25 tests |
| `terminal_game/presentation/__init__.py` | The package docstring now lists what is in the layer and names the two vocabularies other lanes should use rather than redeclare |

## On the ownership table, and a small contradiction in amendment 1

Amendment 1's ownership table says **"Directions and headings — DEV-B, in
whichever of WI-7 or WI-9 lands first"**. But the **first-lander rule**, in
the same section and stated as the general rule, says the first spelling to
land on `main` wins — and `Direction` landed on day one in **DEV-A's WI-5**,
as part of the maze's query surface. WI-7 conformed to it rather than
declaring a second one, and WI-9 does the same.

So the two rules in section 2 point at different owners for this one row. **I
have followed the first-lander rule**, because the alternative — a
presentation-layer `Direction` sitting beside the domain's — is exactly the
duplication amendment 1 exists to prevent, and because conforming cost
nothing. Flagging it so the table can be corrected rather than quietly
diverging from what the tree does.

**For WI-11 and WI-15:** use `terminal_game.domain.maze.Direction`. There is
one, it is in the domain, and both of DEV-B's M1 items already use it.

## The intent vocabulary

```python
class IntentKind(Enum):   MOVE, QUIT          # two, and GAME-3 says no more
class Intent(NamedTuple): kind, direction     # direction is None for a Quit
QUIT = Intent(IntentKind.QUIT, None)
def move(direction: Direction) -> Intent
def translate(keysym: str, char: str) -> Optional[Intent]
```

`Intent` is a value, so a test asserts what the player asked for by comparing
rather than by inspecting. `None` means the key was discarded.

## Why `translate` takes two strings and not a `KeyPress`

**Presentation may not name the Shell.** DEV-C's `KeyPress(keysym, char)`
lives in `terminal_game/shell/toolkit.py`, so importing it here would break
the layer rule that WI-10 is about to start guarding. `translate` takes the
two plain strings that value carries, and the Shell's key handler — which is
the caller, per the architecture's own diagram — unpacks it:

```python
intent = translate(key.keysym, key.char)
```

**`char` is required, not defaulted.** A default of `""` would quietly turn a
caller that forgot the argument into one whose quit key had stopped working.

## What this seam can and cannot see — worth DEV-C's eye

A key crosses the Shell seam as a keysym and the character it typed, **and no
modifier state**. That has one good consequence and one limitation:

- **A modified letter is correctly rejected.** Plain `q` arrives as
  `("q", "q")`; control-Q keeps the keysym but types a control character, so
  it does not quit. That is why `translate` insists on the character as well
  as the keysym for the quit keys — and there is a test for it.
- **A modified arrow cannot be told from a plain one.** An arrow types no
  character either way, so control-Up and Up are indistinguishable here, and
  control-Up therefore moves the player.

The plan's test list for WI-9 asks that "modified keys" map to nothing.
**Modified letters do; modified arrows cannot, at this seam.** Closing that
would mean adding the modifier state to the Shell's `KeyPress`, which is
WI-3's value and DEV-C's call, so I have raised it with them rather than
changing it. It is a small thing — control-Up moving the player is not a
requirement anybody will miss — but it should be a decision rather than an
accident.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
Ran 374 tests — 374 passed, 0 failed, 0 skipped
```

That is with DEV-A's WI-11 merged in. 25 of the 374 are new here. Nothing in this branch opens a window or imports a
toolkit.

## What the tests own

**CTRL-1:** each arrow maps to its own direction; the four map to four
*different* directions; and — the one way to get this wrong — up decreases
the row and left decreases the column, asserted on the axis rather than on
the name.

**CTRL-4:** `q` and `Q` both quit and give the very same intent; a quit
carries no direction; control-Q does not quit.

**CTRL-5, "no other key does anything":** a spread of **45** key presses as
the toolkit reports them — letters including WASD, digits, punctuation,
space, return, tab, escape, backspace, delete, home/end/page, F1/F5/F12, the
bare modifier keys, modified letters, four near-misses for an arrow keysym,
and the empty keysym — every one of them mapping to nothing. Plus *every*
printable ASCII character other than `q` and `Q`. The spread's own test
asserts it is a real spread and that it covers the cases that are easy to get
wrong, so it cannot shrink to nothing and keep passing.

**CTRL-5, "nothing is echoed":** translating every one of those keys with
stdout and stderr captured produces two empty strings. Backed by a check that
no output-capable module is imported and that no executable line contains
`print(`, `.write(`, `stdout`, `stderr` or `log`.

## Two of my own assertions were weaker than they looked

Found while reviewing, and fixed rather than left:

1. A test asserted `"print" not in vars(module)`. Builtins are not module
   globals, so that could never fail. Replaced with the stdout/stderr capture
   (which is the real guarantee), an imports check that can actually fail,
   and a source check.
2. A test looped over the ignored keys and only asserted *inside* an `if`, so
   it would have passed trivially had the list changed shape. Replaced with
   direct assertions about what the spread must contain.

## DEV-A's WI-11 has landed, and it fits

`origin/main` has been merged in, bringing the turn resolver. Two things
worth recording:

- **The `ghost_heading` gap I raised on PR #32 is closed.** `GameState` now
  carries `ghost_heading: Optional[Direction]` with a wither, and
  `resolve_tick` calls WI-7's `next_step`. Nothing of mine changed.
- **`resolve_move(state, direction)` takes a bare `Direction`**, which is
  exactly what an `Intent` carries. WI-15 will unwrap `intent.direction` and
  hand it straight over; no adapter, and no second intent type needed in the
  application layer. Announced on
  [PR #39](https://github.com/replicant1/NewTerminalGame/pull/39#issuecomment-5692246571).

## Deviations needing a ruling

**None in behaviour.** The one judgement call is following the first-lander
rule over the ownership table's row for directions, described above; I think
that needs a table correction rather than a code change, but it is the
technical lead's to say.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
