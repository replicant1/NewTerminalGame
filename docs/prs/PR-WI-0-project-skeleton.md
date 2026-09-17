# WI-0 — project skeleton and the layer rule

**Branch:** `r7/wi-0-project-skeleton`, cut from `main` at `4015c96`
**Lane:** B · **Iteration:** M0 · **Depends on:** nothing
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**56 passed, 0 failed, 0 skipped**

Five items become startable when this lands, and every developer after this
runs its suite command. So the two things to check first are that the command
works from a clean clone, and that the layer rule is a test rather than a
sentence.

---

## Setting up, from a clean clone

Four commands. Nothing is installed outside the repository.

```sh
git clone git@github.com:replicant1/NewTerminalGame.git
cd NewTerminalGame
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
```

**`/usr/bin/python3`, not `python3`.** On this machine `python3` may resolve to
the Homebrew 3.14, which has no `_tkinter` at all and therefore cannot open a
window. `/usr/bin/python3` is CPython 3.9.6 with Tk 8.5. Section 1.2 fixes it,
and it is not a preference.

If the environment is built any other way, `tests/test_runtime.py` fails on the
first run and names the problem — which is the point: *"WI-0 pins the
interpreter so a developer finds this out from a failing suite and not from a
user."*

Two harmless things you will see: the bundled `pip` is 21.2.4 and prints a
notice that a newer version exists (cosmetic, and deliberately not upgraded, so
that every developer's environment is built the same way); and `.venv/` is
git-ignored, which it was not before this branch.

---

## What is in it

### The runtime, pinned and reproducible

| File | What it does |
|---|---|
| `requirements.txt` | Pins `pytest==8.4.2`, and says why `tkinter` cannot be listed there — it is a standard-library binding that comes from the interpreter the venv was created from, and from nowhere else. |
| `pytest.ini` | Makes the single suite command work with nothing installed: `pythonpath = .` so `import terminal_game` and `import tools.layer_rule` resolve, `testpaths = tests`, `--strict-markers`, and the `needs_window` marker **excluded by default**. |
| `.gitignore` | Gains `.venv/`, `/venv/` and `.pytest_cache/`. |
| `README.md` | The four commands above, the layer rule in a paragraph, and what 3.9 forbids. |

`pytest.ini` carries `addopts = --strict-markers -m "not needs_window"`. That
is section 1.6's requirement that **the default suite must never put a window
on the user's screen**, implemented once, here, so that S-1 and WI-5 have a
marker to reach for rather than each inventing one. A command-line `-m`
overrides it, so `-m needs_window` is how a human-verification run asks for the
excluded tests deliberately.

### A package to put things in

```
terminal_game/
    domain/          the rules of the game; pure
    application/     session controller, turn resolver
    presentation/    everything the player sees, as data
    shell/           the window, the event loop, the tick timer, the entry point
tools/               developer tooling; not part of the game
tests/               the suite
```

Each layer's `__init__.py` carries its own clause of the rule as a docstring,
so a developer opening `terminal_game/domain/` reads what the domain may not do
before writing anything in it.

### The layer rule, as something that runs

`tools/layer_rule.py` reads every module under `terminal_game` with `ast` and
reports each import the rule forbids.

Three decisions in it are worth a sentence each.

**It reads source rather than importing it.** Importing a presentation module
runs its body, and under candidate 2 that is precisely the code that could put
a window on the user's screen. A rule that had to import the thing it judges
would be a rule that could not be run in the default suite.

**It lives outside the package it scans.** A checker inside `terminal_game`
would have to judge itself and therefore be exempted, and an exemption is the
first hole anyone uses. `tests/test_layer_rule.py` also pins that nothing in
`terminal_game` imports `tools`.

**It catches the ordinary evasions.** Imports written inside a function or a
`try`, relative imports resolved to absolute names, `from X import Y` read as
both `X` and `X.Y`, and `importlib.import_module("tkinter")` or
`__import__("tkinter")` with a literal name. **Its one known limit: an import
whose module name is computed at runtime is invisible to it.** That is written
in the module docstring and in the README rather than left to be found.

What it enforces, with a distinct handle per clause so a failure says which:

| Handle | Clause |
|---|---|
| `layer-order` | `shell -> presentation -> application -> domain`; a layer may import itself and anything below it |
| `domain-purity` | Domain names no toolkit, clock, filesystem, environment, process, or module-level random source |
| `application-toolkit` | Application names no windowing toolkit |
| `application-clock` | Application reads no clock; a tick arrives as a call |
| `presentation-toolkit` | Only the one painting module names the toolkit |
| `unplaced-module` | Code directly under `terminal_game/` is in no layer, so the rule cannot judge it |

One written import line reports as one violation, even though `from X import Y`
is two names to the scanner — otherwise every cross-layer import would look
like two mistakes, and the count in a failure is the first thing anyone reads.

### The painting exception, named in one place

`tools.layer_rule.PAINTING_MODULE` is `"terminal_game.presentation.surface"` —
the one module inside Presentation allowed to name the toolkit, which is WI-5's
character grid surface.

**WI-5: if you name your surface module something else, change that constant
and nothing else.** It is a single line and it is the only place the exception
is written down. The suite pins that the exception stays *one* module and stays
inside `presentation`, so it cannot be widened quietly, but it does not care
what the module is called and does not require it to exist yet.

---

## The tests, and why they are shaped this way

**56 tests in three files.**

`tests/test_runtime.py` (3) — the interpreter is 3.9; the suite is running
inside a virtual environment rather than against a system-wide pytest; and
`_tkinter` is importable and reports a Tk 8.x binding. That last one is the
measurement that distinguishes a venv built from `/usr/bin/python3` from one
built from the Homebrew python. Reading `_tkinter.TK_VERSION` constructs no
`Tk()`, so it puts nothing on the screen.

`tests/test_layer_rule.py` (32) — one test runs the rule over the real tree.
That is the assertion the project leans on, and at WI-0 it would pass just as
happily against a checker that judged nothing at all, because the real tree is
four empty packages. So the rest build small packages in `tmp_path` that break
the rule on purpose and assert the checker names the violation: domain reaching
up, domain naming a clock or a random source or the filesystem, application
naming the toolkit, presentation naming the toolkit outside the painting
module, a module in no layer, a dynamic import, an import hidden in a function.

**Those are fixtures written to be wrong. No working code is altered to produce
them and nothing outside `tmp_path` is touched** — the prohibition on breaking
correct code to watch a test go red is about mutating the real tree, and this
branch never does.

Alongside them, four tests assert the checker *accepts* what it should: a clean
tree, a layer importing itself and everything below it, the domain using pure
standard-library modules, and the shell naming anything. A checker that
rejected everything would pass all the rejection tests.

`tests/test_import_scanner.py` (21) — the same worry one level down. Given
source that imports something, does the scanner see it? A scanner that returned
an empty list for every file would make the layer test pass for ever, and pass
loudest on the day somebody imports `tkinter` into the domain.

---

## Deviations, all additive, all needing a ruling

1. **`README.md` at the repository root.** Section 1.7 names four document
   shapes and a README is none of them. I judged a clean clone needs setup
   instructions in the repository and not only in a PR body nobody reads twice.
   Say if it should go.
2. **`tools/` as a package for developer tooling.** Section 1.8 leaves layout
   to the developers, so this may not need a ruling at all — but it adds a
   fifth top-level directory and WI-18's coverage audit may want to live in it.
3. **The `needs_window` marker and its default exclusion**, created here rather
   than by S-1 or WI-5. Section 1.6 requires the exclusion; nothing said who
   builds the mechanism, and two people inventing two markers is worse.
4. **`unplaced-module`** — the rule now requires every module under
   `terminal_game` to sit in one of the four layer packages, with
   `terminal_game/__init__.py` exempt. The plan does not ask for this. Without
   it the rule is dodged by putting the module one level up, so I think it is
   the rule rather than an addition to it; it is a real constraint on layout
   and it should be a ruling rather than my judgement.
5. **The reading of "Application imports Domain only"** (section 1.3). Read
   literally that forbids `enum` and `typing` too. I implemented it as: *of the
   four layers*, Domain and itself only — plus the explicit bans on the toolkit
   and the clock. Domain's impurity ban is the strict one, as written.

## Contradiction found

**`.gitignore`'s comment contradicted section 1.2.** The stanza above
`__pycache__/` read *"There is no build step, no virtualenv and no packaging
here (ARCHITECTURE.md §2)"*. Section 2 of the architecture is candidate 1;
candidate 2 was adopted and section 1.2 of the plan fixes the runtime as a
project virtual environment with the suite command `.venv/bin/python -m pytest
-q`. The measurement is the file itself before this branch: no ignore entry for
a virtual environment directory existed, so the first developer to build one
would have had `.venv/` — some thousands of files — offered up by `git status`.
Fixed here: the comment now says what is still true, and `.venv/` is ignored.

## What needs a human

Nothing blocking. The five deviations above want a ruling from the technical
lead, and deviations 1 and 4 are the two I would most like settled before WI-1
and WI-3 branch from this, because they constrain where other people put files.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
