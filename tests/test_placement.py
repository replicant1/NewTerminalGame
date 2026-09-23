"""WI-9: where the game window goes. The policy is pure; the anchor query is read-only.

Nothing here opens a window. The last few tests call the real platform
queries, which only read the window server's list and the screens.
"""

import time

import pytest

from terminal_game.shell import anchor
from terminal_game.shell.placement import OFFSET, Rect, place

WINDOW = (400, 602)   # the game window's outer size: 400 x 570 drawing area + 32-pt title bar
MAIN = Rect(0, 33, 1512, 949)                 # measured: main display's visible area
LEFT = Rect(-3509, -1407, 2560, 1407)          # measured: a display up and to the left
MIDDLE = Rect(-949, -1407, 2560, 1407)         # measured: a display straight above
DISPLAYS = [MAIN, LEFT, MIDDLE]


def outer(x, y):
    return Rect(x, y, *WINDOW)


# -- C1 ---------------------------------------------------------------------------


def test_c1_top_left_goes_a_fixed_offset_below_and_right_of_the_anchor():
    assert 20 <= OFFSET <= 60
    for anchor_rect in (Rect(100, 200, 800, 500), Rect(10, 40, 300, 300), Rect(-3000, -1300, 900, 700)):
        x, y = place(anchor_rect, WINDOW, DISPLAYS)
        assert (x - anchor_rect.x, y - anchor_rect.y) == (OFFSET, OFFSET)


# -- C2 ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "anchor_rect, expected",
    [
        (Rect(1300, 100, 200, 300), (1512 - 400, 140)),         # too far right: moved left to the edge
        (Rect(100, 700, 600, 250), (140, 33 + 949 - 602)),      # too far down: moved up to the edge
        (Rect(1400, 800, 100, 100), (1112, 380)),               # both
        (Rect(-30, 0, 500, 500), (10, 40)),                     # anchor hangs off the left of the main display
    ],
)
def test_c2_moved_just_far_enough_to_lie_wholly_on_the_visible_screen(anchor_rect, expected):
    x, y = place(anchor_rect, WINDOW, DISPLAYS)
    assert (x, y) == expected
    assert MAIN.contains(outer(x, y))


def test_c2_a_position_already_on_screen_is_not_moved():
    x, y = place(Rect(200, 100, 600, 400), WINDOW, DISPLAYS)
    assert (x, y) == (240, 140)


# -- C3 ---------------------------------------------------------------------------


def test_c3_with_no_anchor_the_window_is_centred_wholly_on_the_main_display():
    x, y = place(None, WINDOW, DISPLAYS)
    assert MAIN.contains(outer(x, y))
    assert (x, y) == (556, 206)   # 33 + (949 - 602) / 2 = 206.5, rounded half to even


def test_c3_a_failing_query_means_no_anchor():
    def broken():
        raise OSError("window server unavailable")

    assert anchor.find_anchor(query=broken) is None


def test_c3_no_window_on_screen_means_no_anchor():
    assert anchor.find_anchor(query=lambda: []) is None


def test_c3_only_our_own_windows_means_no_anchor():
    ours = [{"layer": 0, "pid": 4242, "alpha": 1.0, "bounds": Rect(0, 0, 400, 602)}]
    assert anchor.find_anchor(query=lambda: ours, own_pid=4242) is None


# -- C4 ---------------------------------------------------------------------------


def test_c4_an_anchor_on_a_second_display_puts_the_window_on_that_display():
    chrome = Rect(-3351, -1398, 2248, 1374)   # measured: a browser window on the left display
    x, y = place(chrome, WINDOW, DISPLAYS)
    assert LEFT.contains(outer(x, y))
    assert (x, y) == (-3311, -1358)


def test_c4_near_a_shared_edge_it_stays_on_the_anchors_display():
    # The anchor sits at the right edge of the left display; the offset would push
    # the window across the seam onto the middle display. It must stay on the left one.
    edge = Rect(-1000, -600, 50, 50)
    x, y = place(edge, WINDOW, DISPLAYS)
    assert LEFT.contains(outer(x, y))
    assert x == LEFT.right - WINDOW[0]


def test_c4_an_anchor_whose_corner_is_off_every_display_goes_where_it_overlaps_most():
    straddling = Rect(-3600, -1300, 1000, 800)   # top-left beyond the left display's left edge
    x, y = place(straddling, WINDOW, DISPLAYS)
    assert LEFT.contains(outer(x, y))


# -- C5 ---------------------------------------------------------------------------


def test_c5_a_query_that_hangs_is_given_up_on_within_half_a_second():
    def hangs():
        time.sleep(3)
        return [{"layer": 0, "pid": 1, "alpha": 1.0, "bounds": Rect(0, 0, 500, 500)}]

    start = time.monotonic()
    found = anchor.find_anchor(query=hangs)
    elapsed = time.monotonic() - start
    assert found is None
    assert elapsed < 0.6


# -- choosing the frontmost window -------------------------------------------------


def test_the_first_ordinary_window_that_is_not_ours_is_the_anchor():
    windows = [
        {"layer": 25, "pid": 10, "alpha": 1.0, "bounds": Rect(1100, 0, 40, 33)},    # menu-bar item
        {"layer": 0, "pid": 99, "alpha": 1.0, "bounds": Rect(5, 38, 400, 602)},     # our own window
        {"layer": 0, "pid": 11, "alpha": 0.0, "bounds": Rect(0, 0, 900, 900)},      # invisible
        {"layer": 0, "pid": 12, "alpha": 1.0, "bounds": Rect(0, 0, 30, 400)},       # a sliver
        {"layer": 0, "pid": 13, "alpha": 1.0, "bounds": Rect(50, 60, 700, 500)},    # the anchor
        {"layer": 0, "pid": 14, "alpha": 1.0, "bounds": Rect(0, 0, 1000, 800)},     # behind it
    ]
    assert anchor.find_anchor(query=lambda: windows, own_pid=99) == Rect(50, 60, 700, 500)


# -- the real queries (read-only; no window is opened) ----------------------------


def test_c5_the_real_query_answers_well_inside_half_a_second():
    """The query itself, not the timeout, is what finishes: it answers with the window list in time."""
    start = time.monotonic()
    windows = anchor.on_screen_windows()
    elapsed = time.monotonic() - start
    print(f"\nWI-9/C5: real window list: {len(windows)} windows in {elapsed * 1000:.1f} ms")
    assert windows, "a Mac with a display always has some on-screen window (the menu bar at least)"
    assert elapsed < anchor.ANCHOR_TIMEOUT_S / 2


def test_the_real_display_list_starts_with_the_main_display():
    displays = anchor.visible_displays()
    assert displays, "no display found"
    main = displays[0]
    assert main.x == 0 and 0 <= main.y < 100 and main.width > 0 and main.height > 0


# -- displays (WI-9/C2, C4, A2) ------------------------------------------------------


def test_a2_screens_are_flipped_to_top_left_points_and_a_secondary_menu_bar_is_left_out():
    # NSScreen's own numbers, as measured on this desk: main 1512 x 982 with a
    # 33-pt menu bar; two 2560 x 1440 displays above it, reported with nothing
    # taken off although a menu bar is drawn across their tops.
    screens = [
        (Rect(0, 0, 1512, 982), Rect(0, 0, 1512, 949)),
        (Rect(-3509, 982, 2560, 1440), Rect(-3509, 982, 2560, 1440)),
        (Rect(-949, 982, 2560, 1440), Rect(-949, 982, 2560, 1440)),
    ]
    assert anchor.to_global(screens) == [MAIN, LEFT, MIDDLE]


def test_a2_a_secondary_display_that_reports_its_own_menu_bar_is_not_trimmed_twice():
    screens = [
        (Rect(0, 0, 1512, 982), Rect(0, 0, 1512, 949)),
        (Rect(1512, 0, 1920, 1080), Rect(1512, 0, 1920, 1050)),   # 30 pt already taken off the top
    ]
    assert anchor.to_global(screens)[1] == Rect(1512, -98 + 30, 1920, 1050)


# -- A1 -----------------------------------------------------------------------------


def test_a1_with_no_display_at_all_place_refuses_rather_than_inventing_a_position():
    with pytest.raises(ValueError, match="at least one display"):
        place(None, WINDOW, [])
