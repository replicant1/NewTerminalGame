# Completion record: M1, Dev A (lane A)

Lane A's M1 items are WI-1, WI-4, WI-5 and WI-6. All four have merged.

## WI-1: Project scaffold and the layer guard: merged

- **PR:** #122, branch `r8/wi-1-scaffold`, cut from `main` at `8bc9496`.
- **Merged:** 2026-09-23 at 03:15:52Z as `75723e7`, by Dev A, under the non-local merge gate.
- **Risk:** MEDIUM, the plan's floor. Neither I nor the verifier raised it. No human gate.
- **Copilot:** one baseline review on `2c6f6ed`, with four threads. Two were fixed at `b79d586`: aliased import functions, and a module that swallows the refusal at import. Two were disputed: Copilot read `wantTk` as index 4, and the `_tkinter.create` signature puts it at index 5. The verifier checked the signature and agreed with the dispute.
- **Verifier:** round 1 `APPROVED` at `4968ef82989fd6d57aa3a121b810ee7d6e3fb288` by `newterminalgame-code-reviewer[bot]`. All six plan claims and all five added claims (A1 to A5) are REPRODUCED. The controls for C2, C5 and C6 fail on the base as stated.
- **Suite as left:** `.venv/bin/python -m pytest -q` on `origin/main` at `75723e7` gives **130 passed, 0 failed, 1 skipped**. The skip is the existing run-7 log test, which is absent from the checkout by design.

What it gives the other lanes: `requirements.txt`, `pyproject.toml` (the pytest config and the `[tool.terminal_game.layers]` declaration), `conftest.py`, and the README setup, tests and layers sections. It also adds the four layer packages under `terminal_game/`, `tools/layer_check.py` (which the default suite runs over the real tree), and `tools/pytest_guards.py`. The guards refuse a wrong interpreter, deselect `desktop` tests unless `-m` names `desktop`, and fail any unmarked test that asks for a Tk window.

Known limit, stated in the README and the brief: the window guard cannot see a window opened by a **subprocess** that a test launches. Such tests must carry `@pytest.mark.desktop`.

## WI-4: Wall glyphs: merged

- **PR:** #124, branch `r8/wi-4-wall-glyphs`, cut from `origin/main` at `75723e7`. It carried WI-1's completion record, on the conductor's ruling.
- **Merged:** 03:33:50Z as `cfe5822`. **Risk:** LOW, the floor. No human gate.
- **Copilot:** reviewed `e96ab9b` with no inline comments. Its summary pointed to a validation gap: specimen squares had been classified with the module's own character set. Fixed at `da5c2b0`. They are now classified from the plan's twelve characters, and the wall count is checked against 551 minus the lead's 264.
- **Verifier:** round 1 `APPROVED` at `da5c2b08c16c6f54ef930ef641d743093e2f5108`. C1–C4 are REPRODUCED.
- **Built:** `terminal_game/presentation/wall_glyphs.py` provides `wall_glyph`, `joining_glyph`, and `square_glyph` / `joining_cell` over an `is_wall(col, row)` predicate with an explicit grid size. `tests/specimen.py` reads the specimen from the requirements document for WI-10 to reuse. The specimen's walls redraw with 0 mismatches.

## WI-5: Status line: merged

- **PR:** #125, branch `r8/wi-5-status-line`, cut from `origin/main` at `75723e7`.
- **Merged:** 03:32:58Z as `796aebe`. **Risk:** LOW, the floor. No human gate.
- **Copilot:** one thread: an unhashable outcome raised `TypeError`. Fixed at `e5d5d81`.
- **Verifier:** round 1 `APPROVED` at `e5d5d8120ce54454df5cd971f0c56af7456bfb12`. C1–C5 are REPRODUCED.
- **Built:** `terminal_game/presentation/status_line.py` provides `status_text` and `status_row`. The score cell is fixed per state, with the text after it at cell 12, 20 or 21. `terminal_game/presentation/roles.py` holds the six colour-role strings, which are the same strings lane C's shell palette uses.

## WI-6: Input translation: merged

- **PR:** #126, branch `r8/wi-6-input-translation`, cut from `origin/main` at `75723e7`.
- **Merged:** 03:34:46Z as `0680c8c`. **Risk:** LOW, the floor. No human gate.
- **Copilot:** one thread: the harness's key list missed two modifiers. Fixed at `a8ca039`. The harness now imports the unit tests' corpus.
- **Verifier:** round 1 `APPROVED` at `a8ca03954869b6b30eacc1a2dbd4ca365b9a4f72`. C1–C3 are REPRODUCED.
- **Built:** `terminal_game/presentation/input_translation.py` provides `translate`, which maps Tk keysyms to the string intents `up`, `down`, `left`, `right` and `quit`, and anything else to `None`. The intents are strings so that WI-12, in the application layer, needs no import from presentation.

## Suite at the end of M1 for lane A

An export of `origin/main` at `0680c8c`, which includes lane B's WI-2: `.venv/bin/python -m pytest -q` gives **363 passed, 0 failed, 1 skipped**. `python -m tools.layer_check` gives PASS, with shell 1, presentation 5, application 1, domain 3 and entry 1.
