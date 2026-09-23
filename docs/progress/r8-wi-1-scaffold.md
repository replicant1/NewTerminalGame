02:33:23Z  WI-1 START   WI-1 project scaffold and the layer guard, branch r8/wi-1-scaffold from 8bc9496 (Dev A, lane A)
02:33:49Z  WI-1 READ    docs/IMPLEMENTATION_PLAN.md (whole; WI-1 in section 4, ground rules 1.2, 1.4, 1.6, 1.9)
02:39:14Z  WI-1 READ    existing tests/, tools/code_reviewer_token.py (expects a requirements.txt comment on why pytest only), the ignore file (.venv, README.md referenced), orchestration/server.py log parser
02:39:14Z  WI-1 VERIFY  fresh 3.14.7 venv at .venv with pytest 9.1.1 -> base suite 36 passed, 1 skipped; Homebrew python reports TkVersion 9.0, Tcl patchlevel 9.0.4; /usr/bin/python3 is 3.9.6 with Tk 8.5
02:39:40Z  WI-1 PLAN    requirements.txt + pyproject.toml (pytest config and the layer declaration) + README setup; tools/runtime_pin.py (pure check of interpreter and Tk), tools/layer_check.py (AST scan of terminal_game/<layer>/), tools/pytest_guards.py (plugin: runtime refusal, desktop deselection, window-creation guard); four empty layer packages; tests for each; evidence harnesses in evidence/WI-1/
02:39:40Z  WI-1 VERIFY  pytest.UsageError raised in pytest_configure prints 'ERROR: <msg>' and exits 4, on pytest 9.1.1 (3.14) and 8.4.2 (3.9 venv)
02:39:40Z  WI-1 DECIDE  C2 mechanism -> the guard plugin raises UsageError at configure naming found and wanted interpreter and Tk, because it stops the run before any test can pass or fail for an unrelated reason; guard code kept 3.9-parsable so a 3.9 venv reaches it
02:39:40Z  WI-1 DECIDE  pinned interpreter identity -> realpath of the base executable equals realpath of /opt/homebrew/bin/python3.14, plus CPython 3.14, because the plan pins that path and a same-version python.org build is still 'other'
02:39:40Z  WI-1 DECIDE  'working Tk 9' -> tkinter imports, TkVersion major 9, and a Tcl interpreter constructs reporting Tcl 9; Tk itself is not initialised, because initialising Tk creates a window and the default suite must open none
02:43:46Z  WI-1 DECIDE  layer declaration -> [tool.terminal_game.layers] in pyproject.toml, one package per layer, root __init__/__main__ held to shell rules, because a table read by the check is one place, visible, and needs no edit when a module is added
02:43:46Z  WI-1 DECIDE  desktop deselection -> in the plugin (deselect unless the -m expression names desktop), not addopts -m, because any other -m on the command line would override an addopts expression and let window tests run
02:43:46Z  WI-1 DECIDE  window guard -> wrap _tkinter.create (wantTk true) and Tk.loadtk for the whole session, allowed only inside a desktop-marked item, because that covers tests, fixtures and module import during collection
02:43:46Z  WI-1 RISK    the window guard cannot see a window opened by a subprocess the test launches (Homebrew ships its own sitecustomize, so injecting one is fragile); documented in README and the plugin; such tests must carry the desktop mark
02:43:46Z  WI-1 VERIFY  3.9 venv (pytest 8.4.2) running the suite -> ERROR naming CPython 3.9.6 at the CLT path with Tk 8.5 and wanting 3.14 at /opt/homebrew/bin/python3.14 with Tk 9, exit 4; pinned venv -> 36 passed, 1 skipped, header names the runtime
02:43:46Z  WI-1 TEST    36 passed, 0 failed, 1 skipped (scaffold, before WI-1 tests)
02:43:53Z  WI-1 COMMIT  75a3e6f WI-1: scaffold, pinned-runtime refusal, desktop opt-in, window guard, layer check
02:46:55Z  WI-1 TEST    115 passed, 0 failed, 1 skipped (tests for C2-C6 added: test_runtime_pin, test_suite_guards, test_layer_check)
02:53:12Z  WI-1 VERIFY  guards_probe at HEAD 859648c -> C5 HOLDS, C6 HOLDS; at base 8bc9496 -> C5 DOES NOT HOLD (desktop probe PASSED under default), C6 DOES NOT HOLD (window probe reached the create sentinel, no refusal)
02:53:12Z  WI-1 VERIFY  runtime_probe at HEAD -> both runs exit 4 naming found and wanted; at base -> both runs 36 passed, 1 skipped, no message
02:53:12Z  WI-1 VERIFY  fresh_clone at HEAD -> README 2 steps ran, default suite 115 passed 1 skipped, infra files 19 and 17 passed, 1 skip
02:53:12Z  WI-1 VERIFY  layer_samples -> 5 of 5 sample violations named, empty presentation layer fails, real tree PASS with 1 module per layer
02:53:12Z  WI-1 CLAIM   WI-1/C1 executable -- .venv/bin/python evidence/WI-1/fresh_clone.py
02:53:12Z  WI-1 CLAIM   WI-1/C2 executable -- .venv/bin/python evidence/WI-1/runtime_probe.py (control --commit 8bc9496); tests/test_runtime_pin.py, tests/test_suite_guards.py
02:53:12Z  WI-1 CLAIM   WI-1/C3 and C4 executable -- .venv/bin/python evidence/WI-1/layer_samples.py; tests/test_layer_check.py
02:53:12Z  WI-1 CLAIM   WI-1/C5 and C6 executable -- .venv/bin/python evidence/WI-1/guards_probe.py (control --commit 8bc9496); tests/test_suite_guards.py
02:53:12Z  WI-1 CLAIM   WI-1/A1 A2 A3 added (desktop deselected under any other -m or a node id; misspelt mark is an error; domain randomness) -- tests/test_suite_guards.py, tests/test_layer_check.py
02:53:12Z  WI-1 RISK    WI-1 MEDIUM, because it is the plan floor and nothing here opens a window or touches game behaviour
