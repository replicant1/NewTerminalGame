# WI-5a — One root package, not two

**Developer:** DEV-A · **Branch:** `r6/wi-5a-package-name` · **Base:** `main`
**Follows:** WI-5 (PR #24) and WI-1 (DEV-B) · **Iteration:** M0

---

## Why this exists

WI-1, WI-3 and WI-5 were built at the same time in three worktrees, from a
tree with no application in it. The plan leaves package and module names to
the developers (section 1, *what is not fixed, and is yours*), so each lane
picked one. On the root package they did not match:

| Landed by | Root package | Tests |
| --- | --- | --- |
| **WI-1**, DEV-B | `terminal_game/` | flat, `tests/test_frame.py` |
| **WI-3**, DEV-C | `terminal_game/` | nested, `tests/shell/` |
| **WI-5**, DEV-A | `terminalgame/` | nested, `tests/domain/` |

All three merged cleanly and the suite is green either way — no lane refers to
another's package, so nothing broke. But `main` carried **two root packages**,
and the next developer to open the tree would have had to choose between them
with nothing to say which was meant.

## What this does

Moves WI-5's package onto the one the other two lanes already use. **Nothing
of DEV-B's or DEV-C's is touched, and no behaviour changes anywhere.**

- `terminalgame/domain/` → `terminal_game/domain/`
- `terminalgame/__init__.py` → removed; `terminal_game/__init__.py`, which
  already carries the layer dependency rule and already names `domain` as a
  sub-package to come, is the only root
- `terminal_game/domain/__init__.py` gains a docstring in the same style,
  saying what the layer may not do and what is in it so far
- `tests/domain/__init__.py` likewise
- WI-5's PR summary and completion record are corrected to the new paths

## Two decisions, settled by conforming rather than by arbitration

**The root package is `terminal_game/`.** Two of the three lanes had already
landed it; `terminal_game` is the conventional Python spelling of a two-word
name; and DEV-B's root docstring already states the layer dependency rule,
which is a better thing for WI-10's architecture guard to find than an empty
file. I am the one out of step, so I am the one who moves. There was nothing
here for anyone to rule on.

**Tests stay nested by layer, in `tests/domain/`.** This branch first
flattened them to match WI-1's single `tests/test_frame.py`, and then put
them back: WI-3 landed `tests/shell/`, so nested by layer is what two of the
three lanes do, and it mirrors `terminal_game/` directory for directory. Both
shapes are found by the pinned discovery command, so this is a readability
choice and not a correctness one. The flatten-and-unflatten is in this
branch's history rather than hidden, because the second half of the evidence
(WI-3) arrived after the first decision.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 167 tests in 3.3s

OK
```

**167 passed, 0 failed, 0 skipped**, with `origin/main` merged in so that
WI-1, WI-3 and WI-5 are all present: 68 from WI-5, 45 from WI-1, 54 from
WI-3. The same count as before the move, because this changes where code
lives and nothing else.

## What the tree looks like afterwards

One convention, for whoever opens it next:

```
terminal_game/
    __init__.py          the layer dependency rule
    domain/              WI-5: maze, maze_invariants, maze_generator
    presentation/        WI-1: frame
    shell/               WI-3: window owner, tick timer, toolkit seam
    application/         to come
tests/
    __init__.py          how to run the suite, and that it opens no window
    domain/              mirrors terminal_game/domain
    presentation/        to come — WI-1's test_frame.py is still flat
    shell/               mirrors terminal_game/shell
    specimen.py          shared fixture, deliberately not named test_*
tools/                   scripts a person runs deliberately; never discovered
```

`tests/test_frame.py` is left exactly where DEV-B put it. Moving another
developer's test file is theirs to decide, not mine, and it costs nothing to
leave it: the pinned command finds it either way.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
