# Lane B, iteration M0 — completion record

Lane B's M0 is **WI-0** and **WI-1**. **Both have landed, and both are
recorded here** — one completion document per lane per iteration, as section
1.7 asks.

---

## WI-0 — project skeleton and the layer rule

| | |
|---|---|
| Branch | `r7/wi-0-project-skeleton`, cut from `main` at `4015c96` |
| Head of branch | `70455cc` |
| Pull request | [#73](https://github.com/replicant1/NewTerminalGame/pull/73) — opened as a draft, marked ready, merged by developer B |
| Merged to `main` as | `f220e62` at 01:40:11Z on 17 Sep 2026 |
| PR summary | `docs/prs/PR-WI-0-project-skeleton.md` |
| Progress log | `docs/progress/r7-wi-0-project-skeleton.md` |

### What it delivers

The runtime of IMPLEMENTATION_PLAN.md section 1.2 pinned and reproducible, the
single suite command working from the repository root, four layer packages to
put things in, and the dependency rule of section 1.3 as a test that re-runs.

* `terminal_game/` with `domain/`, `application/`, `presentation/`, `shell/`
* `tools/layer_rule.py` — an `ast` import scanner and the policy it enforces
* `tests/test_runtime.py`, `tests/test_import_scanner.py`, `tests/test_layer_rule.py`
* `pytest.ini`, `requirements.txt`, `README.md`, and `.venv/` added to `.gitignore`

### The state of the test suite as it was left

Command, run from the repository root:

```
.venv/bin/python -m pytest -q
```

**56 passed, 0 failed, 0 skipped.** The same counts three times: on the branch
before the merge, in a clean clone of the branch built with the four commands
in `README.md`, and on the branch after `git fetch origin && git merge
origin/main` brought down S-1's merge as well.

By file: `tests/test_runtime.py` 3, `tests/test_import_scanner.py` 21,
`tests/test_layer_rule.py` 32.

Nothing is marked `needs_window` yet, so nothing is deselected. The marker and
its default exclusion exist for S-1 and WI-5 to use.

### What is waiting on a ruling

Five additive deviations, set out in full in the PR summary. The two that
constrain where other people put files, and so are worth settling before WI-1
and WI-3 branch:

* **`README.md` at the repository root** is not one of section 1.7's four
  document shapes.
* **`unplaced-module`** — the rule now requires every module under
  `terminal_game` to sit in one of the four layer packages, which the plan does
  not ask for.

### What WI-5 needs to know

`tools.layer_rule.PAINTING_MODULE` is `"terminal_game.presentation.surface"`.
If the character grid surface is named anything else, change that one constant
and nothing else. The suite pins that the exception stays one module inside
`presentation`; it does not care what it is called and does not require it to
exist yet.

---

## WI-1 — the maze as data

| | |
|---|---|
| Branch | `r7/wi-1-maze-grid`, cut from `main` at `c76bc37` |
| Head of branch | `e62af10` |
| Pull request | [#81](https://github.com/replicant1/NewTerminalGame/pull/81) — opened as a draft, marked ready, merged by developer B |
| Merged to `main` as | `ddc250e` |
| PR summary | `docs/prs/PR-WI-1-maze-grid.md` |
| Progress log | `docs/progress/r7-wi-1-maze-grid.md` |

### What it delivers

A 19 x 29 grid of wall and corridor squares with neighbour queries, and the
structural checker that became WI-2's oracle.

* `terminal_game/domain/maze.py` — `Maze`, `Position`, `Direction`, `Square`.
  MAZE-1 is a property of the type rather than of a call site: no size
  argument exists, so no other shape is representable. MAZE-2 is structural: a
  maze is stored as the frozenset of its corridor squares, so everything else
  is wall and there is nowhere for a third kind to live. Immutable.
* `terminal_game/domain/structure.py` — `border_breaches` (MAZE-3),
  `dead_ends` (MAZE-5), `unreachable_corridors` (MAZE-6), and `check`.
  Each returns *which squares* fail it, computed without reference to the
  others.
* `tests/conftest.py` — the `draw` fixture that places a picture inside the
  19 x 29 frame.
* `tests/test_maze.py` (57) and `tests/test_structure.py` (36).

### The state of the test suite as it was left

```
.venv/bin/python -m pytest -q
```

**174 passed, 0 failed, 0 skipped** after merging `main` down, and the same
again after PR #81 landed. 93 of those were new here.

### What it decided that later items depend on

* **Coordinates**: `x` 0-18 left to right, `y` 0-28 top to bottom, north is
  `y - 1`. Everything comes back in reading order.
* **Out of bounds raises rather than answering `WALL`.** The lead's
  consequence for WI-10: MAZE-3's "a move at the grid edge cannot leave it"
  must be satisfied by the border ring stopping the move, *not* by catching an
  exception. Needing to ask about a square outside the grid is a design smell.
* **`Direction` is the Domain layer's one direction vocabulary**, confirmed by
  ruling. WI-1 pins `opposite()` as its four pairs and nothing more; all ghost
  behaviour remains WI-9's.
