"""WI-3: the shell's real window, on the real desktop. Desktop tests: opt-in only.

Run with ``.venv/bin/python -m pytest -q -m desktop``. Each fixture below runs
``tests/shell_driver.py`` once, as its own process started from a
pseudo-terminal, under a hard timeout; a module's worth of claims is judged
from a handful of short runs, so the desktop sees as few windows as possible.
Every window is the driver's own and closes itself within seconds.

What the picture looks like is judged from ``screencapture`` of the window,
never from what Tk says it was told (see ``tests/shell_screen.py``).

**Do not touch the desktop while these run.** Key tests need the game's
window to stay the key window; if it lost focus, the tests say so rather than
reporting a wrong key.
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import shell_testcard as card  # noqa: E402
from shell_pixels import blank_findings, cell_distance, clip_mask, judge_cell  # noqa: E402
from shell_run import process_alive, program_output, run_driver  # noqa: E402
from shell_screen import read_bmp  # noqa: E402

from terminal_game.shell.frame import COLUMNS, ROWS  # noqa: E402
from terminal_game.shell.palette import BACKGROUND, COLOURS, ROLES  # noqa: E402

pytestmark = pytest.mark.desktop

RGB = {role: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for role, v in COLOURS.items()}
TITLE_BAR_POINTS = 32   # macOS 26, measured; only used to relate CG bounds to Tk's content origin


def _run(tmp_path_factory, scenario):
    run = run_driver(scenario, tmp_path_factory.mktemp(scenario))
    assert run.status is not None, f"{scenario}: the driver hung and was killed; terminal said {run.terminal!r}"
    assert not process_alive(run.pid), f"{scenario}: process {run.pid} is still alive"
    assert not run.stragglers, f"{scenario}: a child of the driver outlived it"
    return run


@pytest.fixture(scope="module")
def card_run(tmp_path_factory):
    return _run(tmp_path_factory, "card")


@pytest.fixture(scope="module")
def keys_run(tmp_path_factory):
    return _run(tmp_path_factory, "keys")


@pytest.fixture(scope="module")
def flip_run(tmp_path_factory):
    return _run(tmp_path_factory, "flip")


@pytest.fixture(scope="module")
def resize_control_run(tmp_path_factory):
    return _run(tmp_path_factory, "resize-control")


def _image(run, name):
    return read_bmp(run.outdir / f"{name}.bmp")


def _geometry(run, image):
    """(scale, cell width, cell height) in device pixels, from the run's own facts."""
    cw, ch = run.result["facts"]["cell"]
    scale = image.width / run.result["facts"]["size"][0]
    return scale, cw * scale, ch * scale


def _judge_frame(run, image, frame, mask):
    """Every cell of ``frame`` in ``image``: cells holding ink of the wrong colour, and painted cells with none."""
    scale, cw, ch = _geometry(run, image)
    inset = round(scale)
    foreign, missing = [], []
    for r in range(ROWS):
        for c in range(COLUMNS):
            character, role = frame[r][c]
            # A painted space, in any role, must leave its cell showing only the background.
            colour = RGB[BACKGROUND] if character == " " else RGB[role]
            judged = judge_cell(image, mask, c, r, cw, ch, colour, inset)
            if judged["foreign"]:
                foreign.append((c, r, character, role, judged["foreign"][:2]))
            if role != BACKGROUND and character != " ":
                if judge_cell(image, mask, c, r, cw, ch, colour, 0)["strong"] == 0:
                    missing.append((c, r, character, role))
    return foreign, missing


def show(claim, text):
    """One line of what was measured, so ``-s`` output shows the claim, not just a pass."""
    print(f"\nWI-3/{claim}: {text}")


def _focus_or_fail(facts, when):
    if not (facts["ns_app_active"] and facts["ns_key_window"]):
        pytest.fail(
            f"the game's window was not the key window of the active application {when} "
            f"({facts}); something else took focus. Re-run without touching the desktop."
        )


# -- WI-3/C1 ---------------------------------------------------------------------


def test_c1_one_window_of_its_own_and_nothing_on_the_terminal(card_run, keys_run, flip_run):
    windows = json.loads((card_run.outdir / "windows.json").read_text())
    assert len(windows) == 1, windows
    assert windows[0]["layer"] == 0
    facts = card_run.result["facts"]
    assert facts["ns_visible_windows"] == 1
    assert facts["toplevels"] == []
    for run in (card_run, keys_run, flip_run):
        assert run.status == 0
        assert program_output(run.terminal) == "", f"{run.scenario} wrote {run.terminal!r}"
    show("C1", f"window server: {len(windows)} window for pid {card_run.pid} ({windows[0]['width']:.0f}x{windows[0]['height']:.0f}); NSApp visible windows {facts['ns_visible_windows']}; terminal output after the harness echo: " + ", ".join(f"{r.scenario}={program_output(r.terminal)!r}" for r in (card_run, keys_run, flip_run)))


# -- WI-3/C2 ---------------------------------------------------------------------


def test_c2_drawing_area_is_exactly_40_by_30_cells(card_run):
    facts = card_run.result["facts"]
    cw, ch = facts["cell"]
    assert facts["family"] == "Menlo"
    assert facts["size"] == [COLUMNS * cw, ROWS * ch] == [400, 570]
    assert facts["root_xywh"][2:] == facts["size"]
    assert facts["canvas_wh"] == facts["size"]
    assert facts["canvas_xy_in_root"] == [0, 0]
    # The window server agrees: the window is 400 wide, and exactly one title bar taller.
    (window,) = json.loads((card_run.outdir / "windows.json").read_text())
    assert window["width"] == 400
    assert window["height"] - 570 == TITLE_BAR_POINTS
    assert (window["x"], window["y"] + TITLE_BAR_POINTS) == tuple(facts["root_xywh"][:2])
    # And the screen agrees: every cell of every role-block picture is where 40 x 30 cells put it.
    mask = clip_mask(_image(card_run, "blank"), _geometry(card_run, _image(card_run, "blank"))[0])
    for k in range(6):
        image = _image(card_run, f"roles{k}")
        assert image.width * 570 == image.height * 400   # the capture of the 400 x 570 rectangle
        foreign, missing = _judge_frame(card_run, image, card.role_blocks(k), mask)
        assert foreign == [] and missing == [], (k, foreign[:3], missing[:3])
    show("C2", f"{facts['family']} cell {cw}x{ch}; root {facts['root_xywh'][2:]} canvas {facts['canvas_wh']} at {facts['canvas_xy_in_root']}; window server {window['width']:.0f}x{window['height']:.0f} = 570 + {TITLE_BAR_POINTS}-pt title bar; 6 x 1200 role cells judged on screen, 0 out of place")


# -- WI-3/C3 ---------------------------------------------------------------------


def test_c3_resize_attempts_leave_40_by_30(card_run, resize_control_run):
    control = resize_control_run.result
    assert control["after"] != control["before"], "the control drag did not resize a resizable window"
    for attempt, sizes in card_run.result["resize"].items():
        assert sizes["root"] == [400, 570], attempt
        assert sizes["canvas"] == [400, 570], attempt
    assert card_run.result["facts"]["zoom_button_enabled"] is False
    image = _image(card_run, "border-after-resize")
    assert image.height * 400 == 570 * image.width
    mask = clip_mask(_image(card_run, "blank"), _geometry(card_run, image)[0])
    foreign, missing = _judge_frame(card_run, image, card.border(), mask)
    assert foreign == [] and missing == []
    show("C3", "control drag on a resizable Tk window: " + f"{control['before']} -> {control['after']}; " + "; ".join(f"{k}: root {v['root']} canvas {v['canvas']}" for k, v in card_run.result["resize"].items()) + f"; zoom button enabled={card_run.result['facts']['zoom_button_enabled']}")


# -- WI-3/C4 ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def fallback_run(tmp_path_factory):
    return _run(tmp_path_factory, "fallback")


@pytest.fixture(scope="module")
def fallback_none_run(tmp_path_factory):
    return _run(tmp_path_factory, "fallback-none")


def test_c4_without_the_preferred_face_another_fixed_face_still_measures_40_by_30(fallback_run, fallback_none_run):
    facts = fallback_run.result["facts"]
    assert facts["family"] == "Courier New"
    cw, ch = facts["cell"]
    assert (cw, ch) == (10, 18)
    assert facts["size"] == [COLUMNS * cw, ROWS * ch]
    assert facts["root_xywh"][2:] == facts["size"] == facts["canvas_wh"]
    image = _image(fallback_run, "border")
    assert image.height * facts["size"][0] == facts["size"][1] * image.width
    blank = _image(fallback_run, "blank")
    mask = clip_mask(blank, _geometry(fallback_run, blank)[0])
    foreign, missing = _judge_frame(fallback_run, image, card.border(), mask)
    assert foreign == [] and missing == [], (foreign[:3], missing[:3])
    # With no preferred face installed at all, the toolkit's own fixed-width face is used.
    none = fallback_none_run.result["facts"]
    assert none["family"] == "Menlo"   # TkFixedFont on this machine
    assert none["size"] == [COLUMNS * none["cell"][0], ROWS * none["cell"][1]] == none["root_xywh"][2:]
    for run in (fallback_run, fallback_none_run):
        assert run.status == 0 and program_output(run.terminal) == ""
    show("C4", f"preferred face missing -> {facts['family']} cell {cw}x{ch}, root {facts['root_xywh'][2:]} canvas {facts['canvas_wh']}, border ring judged on screen; no preference installed -> {none['family']} {none['size']}")


# -- WI-3/C5 ---------------------------------------------------------------------


def test_c5_black_wherever_nothing_is_painted(card_run):
    blank = _image(card_run, "blank")
    scale = _geometry(card_run, blank)[0]
    for name in ["blank"] + [f"blank-burst{n}" for n in range(6)]:
        found = blank_findings(_image(card_run, name), scale)
        assert found["stray"] == [], (name, found["stray"][:5])
        assert found["not_staircase"] == [], (name, found["not_staircase"][:5])
    # In the specimen, every unpainted cell is black, including every cell of the two right-hand columns.
    mask = clip_mask(blank, scale)
    image = _image(card_run, "specimen")
    frame = card.specimen_frame()
    _, cw, ch = _geometry(card_run, image)
    right_columns = 0
    for r in range(ROWS):
        for c in range(COLUMNS):
            if frame[r][c][1] == BACKGROUND:
                judged = judge_cell(image, mask, c, r, cw, ch, RGB[BACKGROUND], round(scale))
                assert judged["foreign"] == [], (c, r, judged["foreign"][:3])
                right_columns += c >= COLUMNS - 2
    assert right_columns == 2 * ROWS
    show("C5", f"7 blank captures: 0 non-black pixels outside macOS's outline and rounded corners; specimen: every background cell black, {right_columns} cells in columns 38-39 checked")


# -- WI-3/C6 ---------------------------------------------------------------------


def test_c6_title_is_exactly_terminal_game(card_run):
    assert card_run.result["facts"]["title"] == "Terminal Game"
    (window,) = json.loads((card_run.outdir / "windows.json").read_text())
    assert window["name"] == "Terminal Game"
    show("C6", f"Tk title {card_run.result['facts']['title']!r}; window server name {window['name']!r}")


# -- WI-3/C7 ---------------------------------------------------------------------


def test_c7_any_character_in_any_cell_in_any_role_lands_in_its_cell_in_its_colour(card_run):
    blank = _image(card_run, "blank")
    mask = clip_mask(blank, _geometry(card_run, blank)[0])
    for k in range(6):   # every cell in every one of the six roles
        foreign, missing = _judge_frame(card_run, _image(card_run, f"roles{k}"), card.role_blocks(k), mask)
        assert foreign == [] and missing == [], (f"roles{k}", foreign[:3], missing[:3])
    assert " " in card.ALPHABET and len(card.ALPHABET) == 257
    spaces = sum(ch == " " for k in range(5) for row in card.alphabet(k) for ch, _ in row)
    assert spaces > 0
    for k in range(5):   # every character of the alphabet in each of the five visible roles
        foreign, missing = _judge_frame(card_run, _image(card_run, f"alphabet{k}"), card.alphabet(k), mask)
        assert foreign == [] and missing == [], (f"alphabet{k}", foreign[:3], missing[:3])
    foreign, missing = _judge_frame(card_run, _image(card_run, "specimen"), card.specimen_frame(), mask)
    assert foreign == [] and missing == []
    show("C7", "roles0-5: 7200 cell/role pairs, alphabet0-4: " + f"{len(card.ALPHABET)} characters (the space among them) x 5 roles, specimen: 1200 cells; 0 cells with ink of another colour, 0 painted cells without ink, {spaces} painted spaces showing only background")


# -- WI-3/C8 ---------------------------------------------------------------------


def test_c8_only_text_on_the_drawing_surface(card_run):
    facts = card_run.result["facts"]
    assert facts["children"] == [".!canvas"]
    assert facts["item_types"] == ["text"]
    assert facts["item_count"] == COLUMNS * ROWS
    show("C8", f"children {facts['children']}; canvas item types {facts['item_types']}; {facts['item_count']} items")


# -- WI-3/C9 ---------------------------------------------------------------------


def test_c9_repaints_only_ever_show_a_frame_that_was_asked_for_and_no_caret(flip_run, card_run):
    blank = _image(flip_run, "blank")
    scale, cw, ch = _geometry(flip_run, blank)
    assert blank_findings(blank, scale)["stray"] == []
    mask = clip_mask(blank, scale)
    a, b = _image(flip_run, "ref-a"), _image(flip_run, "ref-b")
    differing = sum(1 for r in range(ROWS) for c in range(COLUMNS) if cell_distance(a, b, c, r, cw, ch, mask) > 5)
    assert differing > 1000, "the two frames must differ almost everywhere for a mix to show"
    seen = {"a": 0, "b": 0}
    names = [n for n in flip_run.result["captures"] if n.startswith("flip")]
    assert len(names) >= 20 and flip_run.result["paints"] >= 100
    for name in names:
        image = _image(flip_run, name)
        dist_a = max(cell_distance(image, a, c, r, cw, ch, mask) for r in range(ROWS) for c in range(COLUMNS))
        dist_b = max(cell_distance(image, b, c, r, cw, ch, mask) for r in range(ROWS) for c in range(COLUMNS))
        assert min(dist_a, dist_b) <= 2.0, f"{name} matches neither frame (worst cell {dist_a:.1f} / {dist_b:.1f})"
        seen["a" if dist_a <= dist_b else "b"] += 1
    assert seen["a"] and seen["b"], seen
    # No caret: an empty picture looked at six times over 1.5 s is black every time (C5's test checks all six).
    for n in range(6):
        assert blank_findings(_image(card_run, f"blank-burst{n}"), scale)["stray"] == []
    show("C9", f"{flip_run.result['paints']} repaints in 5 s; frames differ in {differing} cells; {len(names)} captures: {seen['a']} are frame A, {seen['b']} are frame B, 0 neither; 6 blank captures over 1.5 s show no caret")


# -- WI-3/C10 --------------------------------------------------------------------


EXPECTED_KEYS = ["Up", "Down", "Left", "Right", "q", "Q", "Q", "a", "z", "1",
                 "space", "Return", "Escape", "Tab", "BackSpace", "F1"]


def test_c10_keys_arrive_named_and_nothing_typed_appears(keys_run):
    _focus_or_fail(keys_run.result["facts"], "when keys were posted")
    received = [name for name, _ in keys_run.result["keys"][:len(EXPECTED_KEYS)]]
    assert received == EXPECTED_KEYS
    before, after = _image(keys_run, "before-typing"), _image(keys_run, "after-typing")
    scale = _geometry(keys_run, before)[0]
    assert blank_findings(after, scale)["stray"] == []
    assert blank_findings(before, scale)["stray"] == []
    show("C10", f"posted {keys_run.result['posted']} -> received {received}; screen before and after typing: black; focus taken back before phases: {keys_run.result.get('refocused', [])}")


# -- WI-3/C11 --------------------------------------------------------------------


def test_c11_tick_rate_with_and_without_keys(keys_run):
    _focus_or_fail(keys_run.result["focus_at_flood"], "during the key flood")
    ticks = keys_run.result["ticks"]
    for window in ("idle_window", "flood_window"):
        start, end = keys_run.result[window]
        count = sum(1 for t in ticks if start <= t < end)
        rate = count / (end - start)
        assert 6.5 <= rate <= 7.5, f"{window}: {count} ticks in {end - start:.3f} s = {rate:.2f}/s"
    assert keys_run.result["flood_keys"] >= 1000
    show("C11", "; ".join(f"{w}: {sum(1 for t in ticks if keys_run.result[w][0] <= t < keys_run.result[w][1])} ticks in {keys_run.result[w][1] - keys_run.result[w][0]:.3f} s" for w in ("idle_window", "flood_window")) + f"; keys delivered during the flood: {keys_run.result['flood_keys']}")


# -- WI-3/C12 --------------------------------------------------------------------


def test_c12_ending_the_session_closes_the_window_and_exits_0_within_a_second(keys_run, card_run):
    _focus_or_fail(keys_run.result["focus_at_quit"], "when q was posted")
    assert keys_run.result["keys"][-1][0] == "q", "the session did not end on q"
    for run in (keys_run, card_run):
        assert run.status == 0
        assert run.exit_record["status"] == 0
        assert run.exited_at - run.result["close_called_at"] < 1.0
        assert not process_alive(run.pid)
    show("C12", "; ".join(f"{r.scenario}: exit {r.status} {r.exited_at - r.result['close_called_at']:.3f} s after close(), alive={process_alive(r.pid)}" for r in (keys_run, card_run)))


# -- WI-3/C13 --------------------------------------------------------------------


@pytest.fixture(scope="module")
def close_button_run(tmp_path_factory):
    return _run(tmp_path_factory, "close-button")


@pytest.fixture(scope="module")
def app_quit_run(tmp_path_factory):
    return _run(tmp_path_factory, "app-quit")


def test_c13_close_button_and_quit_menu_end_the_process_the_same_way(close_button_run, app_quit_run):
    assert app_quit_run.result["menu_item"].startswith("Quit")
    for run in (close_button_run, app_quit_run):
        assert "close_called_at" not in run.result, f"{run.scenario}: the driver had to end the session itself"
        assert run.status == 0
        assert run.exit_record["status"] == 0
        assert run.exited_at - run.result["clicked_at"] < 1.0
        assert program_output(run.terminal) == ""
        assert not process_alive(run.pid)
    show("C13", "; ".join(f"{r.scenario}: exit {r.status} {r.exited_at - r.result['clicked_at']:.3f} s after the click, alive={process_alive(r.pid)}" for r in (close_button_run, app_quit_run)) + f"; menu item {app_quit_run.result['menu_item']!r}")


# -- WI-3/C14 --------------------------------------------------------------------


@pytest.fixture(scope="module")
def raise_key_run(tmp_path_factory):
    return _run(tmp_path_factory, "raise-key")


@pytest.fixture(scope="module")
def raise_tick_run(tmp_path_factory):
    return _run(tmp_path_factory, "raise-tick")


def test_c14_a_failing_handler_closes_the_window_exits_nonzero_and_prints_the_error(raise_key_run, raise_tick_run):
    for run, message in ((raise_key_run, "key handler"), (raise_tick_run, "tick handler")):
        assert "close_called_at" not in run.result, f"{run.scenario}: the handler never failed"
        assert run.status == 1
        assert run.exit_record["status"] == 1
        output = program_output(run.terminal)
        assert "Traceback (most recent call last)" in output
        assert f"RuntimeError: deliberate failure in a {message} (WI-3/C14)" in output
        assert not process_alive(run.pid)
    show("C14", "; ".join(f"{r.scenario}: exit {r.status}, last line {program_output(r.terminal).strip().splitlines()[-1]!r}" for r in (raise_key_run, raise_tick_run)))


# -- WI-3/A1 ---------------------------------------------------------------------


def test_a1_a_malformed_frame_is_rejected_whole_and_changes_nothing(card_run):
    assert "row 29" in card_run.result["bad_frame_error"] or "(39, 29)" in card_run.result["bad_frame_error"]
    specimen, after = _image(card_run, "specimen"), _image(card_run, "after-bad-frame")
    scale, cw, ch = _geometry(card_run, specimen)
    mask = clip_mask(_image(card_run, "blank"), scale)
    changed = [(c, r) for r in range(ROWS) for c in range(COLUMNS)
               if cell_distance(specimen, after, c, r, cw, ch, mask) > 0]
    assert changed == []
    show("A1", f"rejected with {card_run.result['bad_frame_error']!r}; cells changed on screen: {len(changed)}")


# -- WI-3/A2 ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def exit_key_run(tmp_path_factory):
    return _run(tmp_path_factory, "exit-key")


def test_a2_system_exit_from_a_handler_ends_with_its_status_and_no_window(exit_key_run):
    assert "close_called_at" not in exit_key_run.result
    assert exit_key_run.status == 3
    assert program_output(exit_key_run.terminal) == ""
    assert not process_alive(exit_key_run.pid)
    show("A2", f"handler raised SystemExit(3) -> process exit {exit_key_run.status}, alive={process_alive(exit_key_run.pid)}")


# -- WI-3/A3 ---------------------------------------------------------------------


def test_a3_place_puts_the_outer_top_left_at_the_point_given(card_run):
    (window,) = json.loads((card_run.outdir / "windows.json").read_text())
    assert (window["x"], window["y"]) == (120, 140)
    assert tuple(card_run.result["facts"]["root_xywh"][:2]) == (120, 140 + TITLE_BAR_POINTS)
    show("A3", f"place(120, 140) -> window server top-left ({window['x']:.0f}, {window['y']:.0f}), drawing area at {tuple(card_run.result['facts']['root_xywh'][:2])}")


