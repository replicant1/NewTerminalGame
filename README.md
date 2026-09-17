# Terminal Game

A single-process windowed character grid — the game paints a 40 × 30 field of
characters in a fixed-width typeface on a black ground, in a window it creates,
titles, sizes and closes itself.

* What it must do: `docs/FUNCTIONAL_REQUIREMENTS.md` (49 requirement codes)
* How it is shaped: `docs/ARCHITECTURE.md` — **candidate 2** is the one adopted
* How it is being built: `docs/IMPLEMENTATION_PLAN.md`

## Setting up, from a clean clone

Three commands, and nothing else. They take about half a minute.

```sh
git clone git@github.com:replicant1/NewTerminalGame.git
cd NewTerminalGame
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

**Use `/usr/bin/python3` and not whatever `python3` resolves to.** On this
machine `python3` may be the Homebrew 3.14, which has no `_tkinter` at all and
therefore cannot open a window; `/usr/bin/python3` is CPython 3.9.6 with Tk 8.5.
That choice is `docs/IMPLEMENTATION_PLAN.md` section 1.2 and it is fixed, not a
preference. `tests/test_runtime.py` fails immediately and says so if the
environment was built any other way, so you find out here rather than in WI-5.

Two things you will see and can ignore:

* `pip` in the bundled venv is 21.2.4 and prints a notice that a newer version
  is available. It is cosmetic. Nobody upgrades it, so that every developer's
  environment is built the same way.
* `.venv/` is git-ignored, along with `.pytest_cache/`. Never commit either.

## Playing the game

```sh
.venv/bin/python -m terminal_game.shell.game
```

A 400 × 570 window appears, centred on your main display, with a maze in it.
The ghost is already moving; nothing has to be pressed to begin. **Arrow keys
move, `q` quits.**

**There is no time limit and no watchdog**, deliberately — GAME-3 forbids
one — so the window waits as long as you like. If a key ever fails to close
it, the window's close button is wired independently and always works.

Before you play it for the first time, **`docs/findings/WI-17-human-verification.md`**
is worth two minutes: it lists the five things only a person can check, says
what a failure looks like for each, and is honest about what the test suite
does and does not tell you.

## Running the suite

```sh
.venv/bin/python -m pytest -q
```

From the repository root, exactly that. It is the single command the whole
project is judged by, and every developer quotes its counts rather than the
word "pass".

Tests that would put a real window on the user's screen are marked
`needs_window` and are **excluded by default** — `pytest.ini` does that, and
`docs/IMPLEMENTATION_PLAN.md` section 1.6 is why. To run one deliberately,
override the marker expression on the command line:

```sh
.venv/bin/python -m pytest -q -m needs_window
```

Anything you run that way is subject to the window hygiene of section 1.5
without exception: capture the window id at the moment you create it, let the
child process exit, confirm it, and only then close.

## How the code is arranged

```
terminal_game/
    domain/          the rules of the game; pure
    application/     session controller, turn resolver
    presentation/    everything the player sees, as data
    shell/           the window, the event loop, the tick timer, the entry point
tools/               developer tooling; not part of the game
tests/               the suite
```

The arrow reads "may import":

    shell -> presentation -> application -> domain

and on top of the ordering: **domain** names nothing impure — no toolkit, no
clock, no filesystem, no environment, no process, and no module-level random
source, because randomness arrives as an argument; **application** names no
toolkit and no clock, because a tick arrives as a call; **presentation** names
the toolkit from exactly one module, the one that actually paints, and produces
data everywhere else; **shell** may name anything.

That is not a convention anyone has to remember. `tools/layer_rule.py` reads
the imports of every module under `terminal_game` with `ast` and
`tests/test_layer_rule.py` runs it over the real tree on every suite run. It
reads source rather than importing it, so it can judge a module that would open
a window if it were imported.

It catches imports written anywhere in a file, including inside a function or a
`try`, relative imports, and `importlib.import_module("tkinter")` or
`__import__("tkinter")` with a literal name. **It cannot see an import whose
module name is computed at runtime** — that is a known limit, written down here
rather than left to be discovered.

**Code goes in one of the four layer packages.** A module directly under
`terminal_game/` is one the rule cannot judge, so the suite reports it.

## Writing to the 3.9 language level

The interpreter is 3.9, so: no `match`; no `X | Y` unions and no built-in
generics evaluated at runtime — put `from __future__ import annotations` at the
top of every module and keep annotations as strings; no `functools.cache`, no
`itertools.pairwise`, and nothing else from 3.10 or later.
