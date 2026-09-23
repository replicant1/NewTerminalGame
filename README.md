# Terminal Game

A maze, a player, a ghost and some dots, in a window of its own on macOS.
The requirements are in `docs/FUNCTIONAL_REQUIREMENTS.md`, the architecture in
`docs/ARCHITECTURE.md` (candidate 2) and the plan in `docs/IMPLEMENTATION_PLAN.md`.

## Setting up

You need macOS and Homebrew's **CPython 3.14 with Tk 9**, at
`/opt/homebrew/bin/python3.14` (IMPLEMENTATION_PLAN.md section 1.2). Nothing
else will do: `/usr/bin/python3` is 3.9 with Apple's deprecated Tk 8.5, and the
suite refuses to run under it. From the repository root:

```sh
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The environment lives in `.venv/`, which is ignored. To rebuild it, delete it
and run the two commands again.

## Running the tests

| | Command, from the repository root | Opens windows? |
|---|---|---|
| **Default suite** | `.venv/bin/python -m pytest -q` | never |
| **Desktop tests** | `.venv/bin/python -m pytest -q -m desktop` | yes: real windows on your screen |

Three guards run with every suite, from `tools/pytest_guards.py` (loaded by
`conftest.py`):

- **The pinned interpreter.** Under any interpreter other than
  `/opt/homebrew/bin/python3.14`, or one without a working Tk 9, the suite stops
  before running anything and says what it found and what it wants.
- **Desktop tests are opt-in.** A test that opens a real window is marked
  `@pytest.mark.desktop`. It runs only when the `-m` expression names
  `desktop`, as the desktop command does, and is deselected otherwise.
- **The default suite opens no window.** A test without the `desktop` mark
  that tries to create a Tk window fails, naming itself, before the window
  exists. A `tkinter.Tcl()` interpreter, which has no window, is allowed.
  This cannot see a window made by a *subprocess* the test starts: a test that
  launches the game must carry the `desktop` mark.

Anything that opens a window follows the window hygiene in
`.claude/agents/developer.md`: capture your own window, reap it on success and
on failure, and never touch a window you did not open.

## The layers

The code in `terminal_game/` is four layers (IMPLEMENTATION_PLAN.md section 1.4),
one package each:

| Layer | Package | May import |
|---|---|---|
| Shell | `terminal_game.shell` | every layer below; `tkinter` and operating-system APIs |
| Presentation | `terminal_game.presentation` | application, domain |
| Application | `terminal_game.application` | domain; no clock |
| Domain | `terminal_game.domain` | the standard library only; no clock; no randomness it was not handed |

**How the tree declares its layers:** the `[tool.terminal_game.layers]` table
in `pyproject.toml` maps each layer to its package, and every module under that
package, at any depth, is in that layer. A new module goes in the package of its
layer; nothing else needs updating. Every module under `terminal_game/` must be
in a layer, except `terminal_game/__init__.py` and `terminal_game/__main__.py`,
which are the program's entry and are held to the shell's rules.

`tools/layer_check.py` reads the table and every module's source and reports
each import that breaks the rule, naming the module, the line and what it
imported. It also reports how many modules it examined in each layer, and fails
if a declared layer has none, so it cannot pass by examining nothing.
`tests/test_layer_check.py` runs it over the real tree in the default suite. To
run it on its own:

```sh
.venv/bin/python -m tools.layer_check
```

What counts as an operating-system or windowing API, a clock, or randomness the
domain was not handed is listed at the top of `tools/layer_check.py`.
