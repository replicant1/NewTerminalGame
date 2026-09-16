# WI-5a — One root package, not two

**Developer:** DEV-A · **Branch:** `r6/wi-5a-package-name` · **Base:** `main`
**Follows:** WI-5 (PR #24) and WI-1 (DEV-B) · **Iteration:** M0

---

## Why this exists

WI-1 and WI-5 were built at the same time in two worktrees, from a tree with
no application in it. The plan leaves package and module names to the
developers (section 1, *what is not fixed, and is yours*), so each of us
picked one. They did not match:

| Landed by | Root package | Tests |
| --- | --- | --- |
| **WI-1**, DEV-B | `terminal_game/` | flat, in `tests/` |
| **WI-5**, DEV-A | `terminalgame/` | nested, in `tests/domain/` |

Both merged cleanly and the whole suite is green either way — no test refers
to the other's package, so nothing broke. But the tree now has **two root
packages**, and DEV-C starting WI-3 and WI-8 would have had to choose between
them with nothing to say which was intended.

## What this does

Moves WI-5 onto WI-1's convention, in a single pass of renames. **Nothing of
DEV-B's is touched, and no behaviour changes anywhere.**

- `terminalgame/domain/` → `terminal_game/domain/`
- `terminalgame/__init__.py` → removed; `terminal_game/__init__.py` (DEV-B's,
  which already carries the layer dependency rule and already names `domain`
  as a sub-package) is the only root
- `terminal_game/domain/__init__.py` gains a docstring in the same style,
  saying what the layer may not do and what is in it so far
- `tests/domain/test_*.py` → `tests/test_*.py`, and `tests/domain/` removed
- the three test modules' imports follow
- WI-5's PR summary and completion record are corrected to the new paths

## Why DEV-B's spelling and not mine

Three reasons, in order of weight:

1. **WI-1 landed first.** `terminal_game/` was already on `main` when WI-5
   merged, so it is the incumbent and moving to it disturbs nobody.
2. **Its package docstring already carries the layer dependency rule** and
   already names `domain`, `application` and `shell` as the sub-packages to
   come. That is a better thing for WI-10's architecture guard to find than an
   empty file.
3. **`terminal_game` is the conventional Python spelling** of a two-word name.

This was settled by conforming rather than by arbitration: renaming my own
files costs nothing and changes none of DEV-B's, so there was nothing for
anyone to rule on. It is recorded here so the decision is on the record rather
than only in a diff.

## Suite

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
```

```
Ran 113 tests in 3.1s

OK
```

**113 passed, 0 failed, 0 skipped** — the same 113 as before the move (68 from
WI-5, 45 from WI-1), because this changes where code lives and nothing else.

## For DEV-C, and for whoever picks up M1

There is now exactly one convention in the tree:

```
terminal_game/
    __init__.py          the layer dependency rule
    domain/              WI-5: maze, maze_invariants, maze_generator
    presentation/        WI-1: frame
    application/         to come
    shell/               to come — the only place the toolkit may be named
tests/
    test_*.py            flat, discovered by the pinned command
    specimen.py          shared fixture, deliberately not named test_*
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
