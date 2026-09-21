# Terminal Game

A single-process windowed character grid — the game paints a 40 × 30 field of
characters in a fixed-width typeface on a black ground, in a window it creates,
titles, sizes and closes itself.

* What it must do: `docs/FUNCTIONAL_REQUIREMENTS.md` (49 requirement codes)
* How it is shaped: `docs/ARCHITECTURE.md` — **candidate 2** is the one adopted
* How it is being built: `docs/IMPLEMENTATION_PLAN.md`

## Setting up, from a clean clone

Four commands, and nothing else. They take about half a minute.

```sh
brew install python-tk@3.14
git clone git@github.com:replicant1/NewTerminalGame.git
cd NewTerminalGame
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

**Use `/opt/homebrew/bin/python3.14`, and install `python-tk@3.14` before you
do.** The interpreter is not chosen for the language it offers; it is chosen
for the Tk bound to it, and the plain Homebrew python has no `_tkinter` at all
until that formula is installed. `docs/IMPLEMENTATION_PLAN.md` section 1.2, as
amended by AMEND-6, fixes it, and `tests/test_runtime.py` fails immediately and
says so if the environment was built any other way.

**Not `/usr/bin/python3`.** It is CPython 3.9.6 bound to Apple's Tk 8.5.9, and
on current macOS that Tk *maps windows without painting them*: the game opens a
window and draws nothing into it. All 1017 headless tests pass on it, and so do
ten of the twelve window tests — the two in
`tests/test_pixels_reach_the_screen.py` that photograph the screen are the only
ones that can tell, and they are the reason the interpreter moved. AMEND-6 has
the measurements.

Two things you will see and can ignore:

* `.venv/` is git-ignored, along with `.pytest_cache/`. Never commit either.
* The window tests below put real windows on your screen for a moment and
  close them again.

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

**The interpreter is 3.14 and the source is 3.9.** Those came apart in AMEND-6:
the interpreter moved for the Tk bound to it, and the code stayed where it was
because every module is written to 3.9 and there is no reason here to spend the
churn.

So: no `match`; no `X | Y` unions and no built-in generics evaluated at runtime
— put `from __future__ import annotations` at the top of every module and keep
annotations as strings; no `functools.cache`, no `itertools.pairwise`, and
nothing else from 3.10 or later.

**What enforces it, and what does not.** `tests/test_runtime.py` parses every
module in `terminal_game/`, `tests/` and `tools/` with `ast.parse(...,
feature_version=(3, 9))`, so 3.10+ *syntax* — `match`, `except*`, PEP 695 —
fails the suite on the interpreter that would otherwise accept it. The same
file asserts that every module carries `from __future__ import annotations`,
which is what makes an `X | Y` or a `list[int]` **in an annotation** harmless:
it is never evaluated.

Three things are guarded by neither, because they parse at every version and
are not library calls either: `X | Y` **evaluated at runtime**
(`isinstance(x, int | str)`), a built-in generic **evaluated at runtime**
(`dict[str, int]()`), and 3.10+ library APIs like `functools.cache`. 3.9's
*interpreter* caught those and the parser cannot, and the interpreter is what
AMEND-6 traded away. **Review owns all three**, and the list above is what
review is reading against.
