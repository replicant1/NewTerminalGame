"""WI-13: the assembled game in the real window. Desktop tests: opt-in only.

Run with ``.venv/bin/python -m pytest -q -s -m desktop tests/test_game_desktop.py``.
Each fixture runs ``tests/game_driver.py`` once, from a pseudo-terminal, under a
hard timeout: four short windows in all. The driver plays a fixed-seed game
with real key events and ends every session with ``q`` or ``Q``.

Pictures are judged from captures of the window, cell by cell, against the
frame the composer made for the state at that moment. The bottom-corner
squares, which macOS clips (WI-3 finding F1), are left out.

**Do not touch the desktop while these run.**
"""

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from shell_pixels import cell_distance, corner_mask, judge_cell  # noqa: E402
from shell_run import process_alive, program_output, run_driver  # noqa: E402
from shell_screen import read_bmp  # noqa: E402

from terminal_game.presentation.status_line import status_text  # noqa: E402
from terminal_game.shell.palette import BACKGROUND, COLOURS  # noqa: E402

pytestmark = pytest.mark.desktop

DRIVER = HERE / "game_driver.py"
RGB = {role: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for role, v in COLOURS.items()}


def show(claim, text):
    print(f"\nWI-13/{claim}: {text}")


def _run(tmp_path_factory, scenario):
    run = run_driver(scenario, tmp_path_factory.mktemp(scenario), driver=DRIVER)
    assert run.status is not None, f"{scenario}: the driver hung and was killed; terminal said {run.terminal!r}"
    assert run.status == 0, f"{scenario}: the driver exited {run.status}; terminal said {program_output(run.terminal)!r}"
    assert not process_alive(run.pid) and not run.stragglers
    for phase in run.result.get("refocused", []):
        print(f"\n({scenario}: focus taken back before {phase})")
    return run


@pytest.fixture(scope="module")
def ghost_run(tmp_path_factory):
    return _run(tmp_path_factory, "ghost-and-key")


@pytest.fixture(scope="module")
def loss_run(tmp_path_factory):
    return _run(tmp_path_factory, "loss")


@pytest.fixture(scope="module")
def win_run(tmp_path_factory):
    return _run(tmp_path_factory, "win")


@pytest.fixture(scope="module")
def quit_run(tmp_path_factory):
    return _run(tmp_path_factory, "quit-playing")


def capture(run, name):
    image = read_bmp(run.outdir / f"{name}.bmp")
    frame = json.loads((run.outdir / f"{name}.frame.json").read_text())
    return image, frame


def geometry(image):
    scale = image.width / 400
    return scale, 10 * scale, 19 * scale


def judge(image, frame):
    """Cells whose ink is not a shade of their role's colour, and painted cells with no ink."""
    scale, cw, ch = geometry(image)
    mask = corner_mask(image, scale)
    foreign, missing = [], []
    for r in range(30):
        for c in range(40):
            character, role = frame[r][c]
            colour = RGB[BACKGROUND] if character == " " else RGB[role]
            j = judge_cell(image, mask, c, r, cw, ch, colour, round(scale))
            if j["foreign"]:
                foreign.append((c, r, character, role))
            mostly_masked = r == 29 and (c <= 1 or c >= 38)   # inside macOS's clipped corner squares
            if character != " " and role != BACKGROUND and not mostly_masked \
                    and judge_cell(image, mask, c, r, cw, ch, colour, 0)["strong"] == 0:
                missing.append((c, r, character, role))
    return foreign, missing


def changed_cells(a, b):
    scale, cw, ch = geometry(a)
    mask = corner_mask(a, scale)
    return {(c, r) for r in range(30) for c in range(40) if cell_distance(a, b, c, r, cw, ch, mask) > 0}


def frame_diff(fa, fb):
    return {(c, r) for r in range(30) for c in range(40) if fa[r][c] != fb[r][c]}


def unmasked(cells, image):
    """Leave out cells lying wholly inside a masked bottom corner (none of the cells we compare do)."""
    return {(c, r) for c, r in cells if not (r >= 29 and (c <= 1 or c >= 38))}


# -- C3 -------------------------------------------------------------------------


def test_c3_the_ghost_moves_32_to_38_squares_in_5_seconds_with_no_key(ghost_run):
    moves = ghost_run.result["ghost_moves_in_5s"]
    show("C3", f"{moves} ghost moves in {ghost_run.result['ghost_window_s']:.3f} s, no key pressed")
    assert 32 <= moves <= 38


# -- C4 -------------------------------------------------------------------------


def test_c4_one_arrow_press_moves_one_square_onto_a_dot_which_disappears_and_scores_one(ghost_run):
    key = ghost_run.result["key"]
    before, after = key["before"], key["after"]
    moved = abs(after["player"][0] - before["player"][0]) + abs(after["player"][1] - before["player"][1])
    assert moved == 1 and after["player"] == key["target"]
    assert after["score"] == before["score"] + 1 and after["dots"] == before["dots"] - 1
    shot_b, frame_b = capture(ghost_run, "before-key")
    shot_a, frame_a = capture(ghost_run, "after-key")
    for image, frame in ((shot_b, frame_b), (shot_a, frame_a)):
        foreign, missing = judge(image, frame)
        assert foreign == [] and missing == [], (foreign[:3], missing[:3])
    tx, ty = key["target"]
    assert frame_b[ty][2 * tx] == ["▪", "dot"] and frame_a[ty][2 * tx] == ["█", "player"]
    assert frame_b[29] != frame_a[29]
    expected = unmasked(frame_diff(frame_b, frame_a), shot_a)
    seen = unmasked(changed_cells(shot_b, shot_a), shot_a)
    assert seen == expected, (sorted(seen - expected)[:5], sorted(expected - seen)[:5])
    status_cells = sorted(c for c, r in expected if r == 29)
    show("C4", f"{key['name']} moved the player {before['player']} -> {after['player']} onto a dot; "
               f"score {before['score']} -> {after['score']}, dots {before['dots']} -> {after['dots']}; "
               f"both captures match their frames cell for cell in role colour; the screen changed in exactly the "
               f"{len(expected)} cells the frames differ in, status cells {status_cells} among them")


# -- C5 -------------------------------------------------------------------------


def test_c5_a_loss_shows_the_ghost_over_the_player_and_caught_and_holds_for_3_seconds(loss_run):
    decided, dots_at_start = loss_run.result["decided"], loss_run.result["dots_at_start"]
    assert decided["outcome"] == "lost" and decided["player"] == decided["ghost"]
    n = decided["score"]
    assert n == dots_at_start - decided["dots"]
    final, frame = capture(loss_run, "final")
    later, frame_later = capture(loss_run, "final-after-3s")
    assert "".join(ch for ch, _ in frame[29]) == status_text(n, "lost").ljust(40)
    assert "".join(ch for ch, _ in frame[29]).startswith(f" CAUGHT  score {n}   q quits")
    gx, gy = decided["ghost"]
    for k, glyph in zip((-1, 0, 1), "▗█▖"):
        if 0 <= 2 * gx + k < 40:
            assert frame[gy][2 * gx + k] == [glyph, "ghost"]
    assert not any(role == "player" for row in frame for _, role in row)
    foreign, missing = judge(final, frame)
    assert foreign == [] and missing == [], (foreign[:3], missing[:3])
    assert frame_later == frame and loss_run.result["after_3s"] == decided
    assert changed_cells(final, later) == set()
    show("C5", f"lost at score {n} ({dots_at_start} - {decided['dots']} dots left) after {loss_run.result['moves_posted']} keys; "
               f"ghost drawn over the player at {decided['ghost']}, no player cell visible; status '{status_text(n, 'lost')}'; "
               f"screen identical after 3.2 s of ticks and 256 arrow keys")


# -- C6 -------------------------------------------------------------------------


def test_c6_a_win_shows_cleared_with_every_dot_scored_and_holds_until_q(win_run):
    decided, dots_at_start = win_run.result["decided"], win_run.result["dots_at_start"]
    assert decided["outcome"] == "won" and decided["dots"] == 0
    assert decided["score"] == dots_at_start
    final, frame = capture(win_run, "final")
    later, frame_later = capture(win_run, "final-after-keys")
    assert "".join(ch for ch, _ in frame[29]).startswith(f" CLEARED  score {dots_at_start}  q quits")
    foreign, missing = judge(final, frame)
    assert foreign == [] and missing == [], (foreign[:3], missing[:3])
    assert frame_later == frame and changed_cells(final, later) == set()
    assert win_run.result["quit_key"] == "q" and "quit_ignored" not in win_run.result
    show("C6", f"won: score {decided['score']} = {dots_at_start} dots at start, after {win_run.result['moves_posted']} keys; "
               f"status '{status_text(dots_at_start, 'won')}'; screen identical after 40 arrow keys over 2 s; then q ended it")


# -- C7 -------------------------------------------------------------------------


def test_c7_q_and_Q_during_play_and_after_an_ending_close_it_within_a_second(ghost_run, quit_run, loss_run, win_run):
    lines = []
    for run, when in ((ghost_run, "during play"), (quit_run, "during play"), (loss_run, "after a loss"), (win_run, "after a win")):
        assert "quit_ignored" not in run.result, f"{run.scenario}: {run.result['quit_key']} did not end it"
        assert run.status == 0 and run.exit_record["status"] == 0
        lag = run.exited_at - run.result["quit_posted_at"]
        assert lag < 1.0
        assert program_output(run.terminal) == ""
        assert not process_alive(run.pid) and not run.stragglers
        lines.append(f"{run.result['quit_key']} {when}: exit 0 in {lag:.3f} s")
    assert quit_run.result["phase_at_quit"] == "playing"
    show("C7", "; ".join(lines) + "; no process left, nothing on the terminal")


# -- C9 -------------------------------------------------------------------------


def test_c9_a_screenshot_shows_every_role_in_its_colour_and_dots_dimmer_than_the_player(ghost_run):
    image, frame = capture(ghost_run, "start")
    foreign, missing = judge(image, frame)
    assert foreign == [] and missing == [], (foreign[:3], missing[:3])
    roles = {role for row in frame for ch, role in row if ch != " "}
    assert roles == {"wall", "dot", "player", "ghost", "status"}
    # Measured colours, from the capture: the brightest pixel of each role's cells.
    scale, cw, ch = geometry(image)

    def brightest(role):
        best = (0, 0, 0)
        for r in range(29):
            for c in range(40):
                if frame[r][c][1] == role and frame[r][c][0] != " ":
                    x0, y0 = round(c * cw), round(r * ch)
                    for y in range(y0, round(y0 + ch)):
                        for x in range(x0, round(x0 + cw)):
                            px = image.rgb(x, y)
                            if sum(px) > sum(best):
                                best = px
        return best

    def luminance(rgb):
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    dot, player = brightest("dot"), brightest("player")
    assert luminance(dot) < luminance(player)
    show("C9", f"start capture: all 1200 cells match their frame in role colour (walls, dots, player, ghost, status; "
               f"blanks black); dot {dot} luminance {luminance(dot):.0f} < player {player} luminance {luminance(player):.0f}")
