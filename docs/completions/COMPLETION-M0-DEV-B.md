# Lane B, iteration M0 — completion record

Lane B's M0 is **WI-0** and **WI-1**. This records the first of them. When WI-1
lands it is appended here rather than filed separately, because section 1.7
allows one completion document per lane per iteration.

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
