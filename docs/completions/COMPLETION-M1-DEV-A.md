# Completion record: M1, Dev A (lane A)

Lane A's M1 items are WI-1, WI-4, WI-5 and WI-6. This record covers the ones finished so far and is extended as each lands.

## WI-1: Project scaffold and the layer guard: merged

- **PR:** #122, branch `r8/wi-1-scaffold`, cut from `main` at `8bc9496`.
- **Merged:** 2026-09-23 at 03:15:52Z as `75723e7`, by Dev A, under the non-local merge gate.
- **Risk:** MEDIUM, the plan's floor. Neither I nor the verifier raised it. No human gate.
- **Copilot:** one baseline review on `2c6f6ed`, with four threads. Two were fixed at `b79d586`: aliased import functions, and a module that swallows the refusal at import. Two were disputed: Copilot read `wantTk` as index 4, and the `_tkinter.create` signature puts it at index 5. The verifier checked the signature and agreed with the dispute.
- **Verifier:** round 1 `APPROVED` at `4968ef82989fd6d57aa3a121b810ee7d6e3fb288` by `newterminalgame-code-reviewer[bot]`. All six plan claims and all five added claims (A1 to A5) are REPRODUCED. The controls for C2, C5 and C6 fail on the base as stated.
- **Suite as left:** `.venv/bin/python -m pytest -q` on `origin/main` at `75723e7` gives **130 passed, 0 failed, 1 skipped**. The skip is the existing run-7 log test, which is absent from the checkout by design.

What it gives the other lanes: `requirements.txt`, `pyproject.toml` (the pytest config and the `[tool.terminal_game.layers]` declaration), `conftest.py`, and the README setup, tests and layers sections. It also adds the four layer packages under `terminal_game/`, `tools/layer_check.py` (which the default suite runs over the real tree), and `tools/pytest_guards.py`. The guards refuse a wrong interpreter, deselect `desktop` tests unless `-m` names `desktop`, and fail any unmarked test that asks for a Tk window.

Known limit, stated in the README and the brief: the window guard cannot see a window opened by a **subprocess** that a test launches. Such tests must carry `@pytest.mark.desktop`.
