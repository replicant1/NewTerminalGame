"""WI-3: the shell's pure parts, with no window: typeface choice, tick schedule, frame shape, geometry.

None of these modules imports a toolkit, so this file runs in the default suite.
"""

import pytest

from terminal_game.shell.frame import COLUMNS, ROWS, blank_frame, check_frame
from terminal_game.shell.geometry import geometry_position
from terminal_game.shell.palette import BACKGROUND, COLOURS, ROLES, colour_of
from terminal_game.shell.ticker import TICK_HZ, TickSchedule
from terminal_game.shell.typeface import PREFERRED_FAMILIES, choose_family

# -- typeface (WI-3/C4) ------------------------------------------------------------

FIXED = {"Menlo", "Monaco", "Courier New", "Andale Mono", "PT Mono", "TkFixed"}


def fixed(family):
    return family in FIXED


def test_menlo_is_chosen_when_installed():
    assert choose_family(PREFERRED_FAMILIES, FIXED | {"Helvetica"}, fixed, "TkFixed") == "Menlo"


def test_without_menlo_the_next_installed_fixed_face_is_chosen():
    installed = {"Helvetica", "Courier New", "PT Mono"}
    assert choose_family(PREFERRED_FAMILIES, installed, fixed, "TkFixed") == "Courier New"


def test_an_installed_but_proportional_preference_is_passed_over():
    # Asked for a face it lacks, Tk hands back a proportional one; a preference
    # that is not fixed-width must never be taken.
    assert choose_family(("Menlo", "Courier New"), {"Menlo", "Courier New"}, lambda f: f != "Menlo", "TkFixed") == "Courier New"


def test_with_no_preference_installed_the_toolkits_fixed_face_is_used():
    assert choose_family(PREFERRED_FAMILIES, {"Helvetica", "Times"}, fixed, "TkFixed") == "TkFixed"


# -- tick schedule (WI-3/C11) ------------------------------------------------------


def test_the_cadence_is_seven_a_second():
    assert TICK_HZ == 7
    assert TickSchedule(0.0).period == pytest.approx(1 / 7)


def test_first_tick_is_due_one_period_after_start():
    schedule = TickSchedule(100.0, hz=7)
    assert schedule.delay_ms(100.0) == 143


def test_slow_handlers_do_not_slow_the_rate():
    """Ticks follow deadlines: 35 ticks in 5 s even when every tick's work takes 60 ms."""
    clock, schedule, fired = 0.0, TickSchedule(0.0, hz=7), []
    while True:
        clock += schedule.delay_ms(clock) / 1000   # the timer fires
        if clock > 5.07:                             # half a period past the fifth second
            break
        fired.append(clock)
        schedule.advance(clock)
        clock += 0.060                               # the handler's work
    within_five_seconds = [t for t in fired if t <= 5.001]
    assert len(within_five_seconds) == 35
    assert within_five_seconds[-1] == pytest.approx(5.0, abs=0.002)


def test_a_stall_longer_than_a_period_does_not_burst():
    schedule = TickSchedule(0.0, hz=7)
    schedule.advance(3.0)            # the process was stopped for three seconds
    assert schedule.delay_ms(3.0) == 143


def test_rate_must_be_positive():
    with pytest.raises(ValueError):
        TickSchedule(0.0, hz=0)


# -- frames (WI-3/C7, A1) ----------------------------------------------------------


def good_frame():
    return [[("x", ROLES[(c + r) % len(ROLES)]) for c in range(COLUMNS)] for r in range(ROWS)]


def test_a_well_formed_frame_comes_back_as_given():
    frame = good_frame()
    assert check_frame(frame) == frame


def test_every_role_and_any_single_character_is_accepted():
    frame = good_frame()
    for i, ch in enumerate("═║▪▐█▌▗▖■ aQ~é中"):
        frame[0][i] = (ch, ROLES[i % len(ROLES)])
    assert check_frame(frame)[0][:15] == frame[0][:15]


def test_a_str_subclass_role_such_as_a_strenum_is_accepted():
    import enum

    Role = enum.StrEnum("Role", {name.upper(): name for name in ROLES})
    frame = [[("x", Role.WALL)] * COLUMNS for _ in range(ROWS)]
    assert check_frame(frame)[29][39] == ("x", "wall")


@pytest.mark.parametrize(
    "mutate, words",
    [
        (lambda f: f.pop(), "30 rows"),
        (lambda f: f[29].pop(), "row 29 has 39 cells"),
        (lambda f: f[29].__setitem__(39, ("xy", "wall")), "cell (39, 29)"),
        (lambda f: f[29].__setitem__(39, ("", "wall")), "cell (39, 29)"),
        (lambda f: f[29].__setitem__(39, ("x", "purple")), "unknown role 'purple'"),
        (lambda f: f[29].__setitem__(39, "x"), "not a (character, role) pair"),
        (lambda f: f.__setitem__(29, None), "row 29 is NoneType"),
    ],
)
def test_a_malformed_frame_is_rejected_naming_the_fault_even_at_the_last_cell(mutate, words):
    frame = good_frame()
    mutate(frame)
    with pytest.raises(ValueError, match=words.replace("(", r"\(").replace(")", r"\)")):
        check_frame(frame)


def test_something_that_is_not_a_frame_at_all_is_a_value_error_too():
    with pytest.raises(ValueError, match="not NoneType"):
        check_frame(None)


def test_the_blank_frame_is_blanks_on_the_background():
    frame = blank_frame()
    assert len(frame) == ROWS and all(row == [(" ", BACKGROUND)] * COLUMNS for row in frame)


# -- palette ---------------------------------------------------------------------


def test_six_roles_six_distinct_colours_on_black():
    assert set(ROLES) == {"wall", "dot", "player", "ghost", "status", "background"}
    assert len(set(COLOURS.values())) == 6
    assert colour_of(BACKGROUND) == "#000000"


def test_an_unknown_role_is_named():
    with pytest.raises(ValueError, match="unknown colour role 'purple'"):
        colour_of("purple")


# -- geometry (WI-3/A3) ------------------------------------------------------------


@pytest.mark.parametrize(
    "x, y, text",
    [(120, 140, "+120+140"), (0, 0, "+0+0"), (-877, -1348, "+-877+-1348"), (-3509, 25, "+-3509+25")],
)
def test_positions_are_always_absolute_even_when_negative(x, y, text):
    assert geometry_position(x, y) == text
