"""Where the game window lands — WIN-4, and the fallback when it cannot be known.

**Everything here runs against supplied numbers.** The plan's bar says so in
as many words: *"do this against a supplied anchor position, not against the
real desktop."* Nothing in this file queries the desktop, opens a window, or
asks any application anything.

Two of these tests exist because of measurements rather than requirements,
and they are the ones most likely to save somebody:

* **The coordinate space has negative origins.** Three displays on this desk:
  the main one at ``(0, 0) 1512x982``, and two at ``(-3509, -1440)`` and
  ``(-949, -1440)``. Arithmetic assuming a screen starts at zero is wrong
  here, and it is wrong in the way that works on the developer's display.
* **Tk's geometry string does not spell a negative origin the tidy way.**
  ``"{:+d}"`` produces ``-877``, which Tk reads as *877 from the right edge*.
  The whole difference between the right window position and one a screen
  away is a format string.
"""

from __future__ import annotations

from typing import List, Optional

import pytest

from terminal_game.shell.placement import (
    OFFSET,
    AnchorReader,
    NoAnchor,
    Point,
    Rect,
    anchor_from,
    below_and_right_of,
    centred_on,
    geometry_string,
    no_anchor,
    placement_for,
    position_in_geometry,
)

#: The displays S-2 measured on this machine. The second and third are the
#: reason nothing in this module clamps and nothing assumes a zero origin.
MAIN_DISPLAY = Rect(0, 0, 1512, 982)
LEFT_DISPLAY = Rect(-3509, -1440, 2560, 1440)
UPPER_DISPLAY = Rect(-949, -1440, 2560, 1440)
ALL_DISPLAYS = [MAIN_DISPLAY, LEFT_DISPLAY, UPPER_DISPLAY]

#: WI-6's window, as measured for P4: Menlo 12, cell 10x19, 40x30 cells.
WINDOW_SIZE = (400, 570)


class FixedAnchor(object):
    """A reader that answers with a rectangle nobody went to the desktop for."""

    def __init__(self, rect: "Optional[Rect]") -> None:
        self.rect = rect
        self.reads = 0

    def read(self) -> "Optional[Rect]":
        self.reads += 1
        return self.rect


class BrokenAnchor(object):
    """A reader that fails the way a real one would — permission, dead process."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    def read(self) -> "Optional[Rect]":
        raise self.error


# --------------------------------------------------------------------------
# WIN-4 — a little below and to the right of the anchor
# --------------------------------------------------------------------------


def test_the_window_lands_below_and_right_of_the_anchor() -> None:
    assert below_and_right_of(Rect(300, 200, 800, 600)) == Point(340, 240)


def test_the_offset_is_the_one_constant_assumption_p3_names() -> None:
    """P3: a fixed pixel offset chosen by eye, +40/+40 to start with.

    Pinned to the constant rather than to 40, so that a human who looks at
    the running game and wants it moved changes one number and this test
    follows.
    """
    anchor = Rect(300, 200, 800, 600)
    assert below_and_right_of(anchor) == Point(
        anchor.x + OFFSET[0], anchor.y + OFFSET[1]
    )


def test_the_offset_is_from_the_anchors_corner_not_its_centre() -> None:
    """So the game overlaps the anchor rather than being flung past a big one.

    Two anchors with the same corner and very different sizes put the window
    in the same place; an offset from the centre would not.
    """
    small = below_and_right_of(Rect(300, 200, 100, 80))
    huge = below_and_right_of(Rect(300, 200, 2000, 1400))
    assert small == huge == Point(340, 240)


@pytest.mark.parametrize("display", ALL_DISPLAYS)
def test_an_anchor_on_any_display_is_offset_the_same_way(display) -> None:
    """Including the two whose origins are negative.

    This is the test that fails if anybody adds a clamp, an ``abs``, or a
    ``max(0, ...)`` to the arithmetic.
    """
    anchor = Rect(display.x + 100, display.y + 50, 700, 500)
    assert below_and_right_of(anchor) == Point(
        display.x + 140, display.y + 90
    )


def test_a_negative_anchor_origin_stays_negative() -> None:
    """Said flatly, because it is the whole of the negative-origin hazard."""
    landed = below_and_right_of(Rect(-3509, -1440, 2560, 1440))
    assert landed == Point(-3469, -1400)
    assert landed.x < 0 and landed.y < 0


def test_an_anchor_at_the_origin_is_not_a_special_case() -> None:
    assert below_and_right_of(Rect(0, 0, 1512, 982)) == Point(40, 40)


# --------------------------------------------------------------------------
# The fallback — a sane default rather than a crash or a prompt
# --------------------------------------------------------------------------


def test_with_no_anchor_the_window_is_centred_on_the_display() -> None:
    assert centred_on(MAIN_DISPLAY, WINDOW_SIZE) == Point(556, 206)


def test_the_centred_window_really_is_in_the_middle() -> None:
    """Asserted as a property rather than as the arithmetic restated: the
    margins on either side are equal, give or take an odd pixel."""
    placed = centred_on(MAIN_DISPLAY, WINDOW_SIZE)
    left = placed.x - MAIN_DISPLAY.x
    right = (MAIN_DISPLAY.x + MAIN_DISPLAY.width) - (placed.x + WINDOW_SIZE[0])
    assert abs(left - right) <= 1


@pytest.mark.parametrize("display", ALL_DISPLAYS)
def test_centring_works_on_a_display_with_a_negative_origin(display) -> None:
    placed = centred_on(display, WINDOW_SIZE)
    assert display.x <= placed.x
    assert placed.x + WINDOW_SIZE[0] <= display.x + display.width
    assert display.y <= placed.y
    assert placed.y + WINDOW_SIZE[1] <= display.y + display.height


def test_a_window_bigger_than_the_display_is_placed_rather_than_refused() -> None:
    """It goes off the edges symmetrically. A crash here would stop a game
    starting over something cosmetic."""
    placed = centred_on(Rect(0, 0, 200, 200), WINDOW_SIZE)
    assert placed == Point(-100, -185)


# --------------------------------------------------------------------------
# The seam, and degrading when it fails
# --------------------------------------------------------------------------


def test_the_default_reader_reads_nothing_and_says_so() -> None:
    """S-2's option C, which ships until the user rules on the others."""
    assert no_anchor().read() is None
    assert "WIN-4 not met" in repr(no_anchor())


def test_an_anchor_that_is_there_is_used() -> None:
    reader = FixedAnchor(Rect(300, 200, 800, 600))
    assert placement_for(reader, MAIN_DISPLAY, WINDOW_SIZE) == Point(340, 240)
    assert reader.reads == 1


def test_no_anchor_falls_back_to_the_centre() -> None:
    assert placement_for(NoAnchor(), MAIN_DISPLAY, WINDOW_SIZE) == centred_on(
        MAIN_DISPLAY, WINDOW_SIZE
    )


@pytest.mark.parametrize(
    "error",
    [
        PermissionError("not authorised"),
        OSError("no such process"),
        ValueError("could not parse the answer"),
        RuntimeError("the thing that reads anchors has gone wrong"),
    ],
)
def test_a_reader_that_fails_degrades_rather_than_crashing(error) -> None:
    """The plan's bar in as many words: *"a failure to read the anchor
    degrades to a sane default rather than crashing or prompting."*

    Four different failures, because the response to all of them is the same
    and a handler that only caught one kind would be worse than none.
    """
    placed = placement_for(BrokenAnchor(error), MAIN_DISPLAY, WINDOW_SIZE)
    assert placed == centred_on(MAIN_DISPLAY, WINDOW_SIZE)


def test_a_failing_reader_yields_no_anchor_rather_than_propagating() -> None:
    assert anchor_from(BrokenAnchor(PermissionError("nope"))) is None


def test_a_reader_answering_none_yields_no_anchor() -> None:
    assert anchor_from(FixedAnchor(None)) is None


def test_a_readers_answer_is_taken_as_a_rectangle() -> None:
    assert anchor_from(FixedAnchor(Rect(1, 2, 3, 4))) == Rect(1, 2, 3, 4)


def test_the_seam_accepts_anything_with_a_read_method() -> None:
    """So that whichever route the user permits is a substitution, not a
    rewrite. No inheritance required."""

    class Whatever(object):
        def read(self):
            return Rect(-949, -1440, 2560, 1440)

    assert placement_for(Whatever(), MAIN_DISPLAY, WINDOW_SIZE) == Point(-909, -1400)


def test_the_abstract_reader_refuses_to_be_used_as_one() -> None:
    with pytest.raises(NotImplementedError):
        AnchorReader().read()


# --------------------------------------------------------------------------
# The geometry string, which is where a negative origin goes wrong
# --------------------------------------------------------------------------


def test_a_positive_position_formats_the_obvious_way() -> None:
    assert geometry_string(Point(100, 200)) == "+100+200"


def test_a_negative_position_keeps_its_sign_inside_the_field() -> None:
    """Measured on a withdrawn Tk root: ``+-877+-1348`` round-trips as
    x = -877, y = -1348."""
    assert geometry_string(Point(-877, -1348)) == "+-877+-1348"


def test_the_tidy_sign_format_would_mean_something_else_entirely() -> None:
    """The trap, written down as a test so nobody 'tidies' the format string.

    ``"{:+d}{:+d}"`` looks like the right way to write a signed pair. It
    produces ``-877-1348``, which Tk reads as *877 from the right edge, 1348
    from the bottom* — a different place by about the width of a display, and
    correct-looking on the main display where x and y are positive.
    """
    point = Point(-877, -1348)
    tidy = "{:+d}{:+d}".format(point.x, point.y)

    assert tidy == "-877-1348"
    assert geometry_string(point) != tidy
    assert position_in_geometry(tidy) is None  # not an absolute position at all


def test_the_geometry_string_carries_no_size() -> None:
    """The size is WI-6's. A geometry string with a ``WxH`` would overrule it."""
    assert "x" not in geometry_string(Point(400, 570))


@pytest.mark.parametrize(
    "point",
    [Point(0, 0), Point(100, 200), Point(-877, -1348), Point(-3509, -1440), Point(1512, 0)],
)
def test_a_position_survives_the_round_trip_through_a_geometry_string(point) -> None:
    assert position_in_geometry("400x570" + geometry_string(point)) == point


@pytest.mark.parametrize(
    "geometry,expected",
    [
        ("1x1+100+200", Point(100, 200)),
        ("1x1+-877+-1348", Point(-877, -1348)),
        ("400x570+0+0", Point(0, 0)),
        ("+100+200", Point(100, 200)),
        ("1x1+-3509+-1440", Point(-3509, -1440)),
    ],
)
def test_a_geometry_string_is_read_back_the_way_tk_writes_it(geometry, expected) -> None:
    """Every one of these is a string a real Tk produced during WI-15."""
    assert position_in_geometry(geometry) == expected


@pytest.mark.parametrize(
    "geometry", ["1x1-877-1348", "1x1+100-200", "1x1-100+200", "1x1", "", "nonsense"]
)
def test_a_position_measured_from_the_far_edge_is_refused_not_guessed(geometry) -> None:
    """``-877`` means 877 from the right, which is not an absolute coordinate
    and cannot be made into one without knowing the display.

    Answering ``None`` rather than ``-877`` matters: silently treating one as
    the other is wrong by the width of a display, which is precisely the
    class of mistake S-2 found in Terminal's own AppleScript ``position``.
    """
    assert position_in_geometry(geometry) is None


# --------------------------------------------------------------------------
# The rectangle itself
# --------------------------------------------------------------------------


def test_a_rectangle_reports_its_corner_and_its_middle() -> None:
    rect = Rect(100, 200, 800, 600)
    assert rect.origin == Point(100, 200)
    assert rect.centre == Point(500, 500)


def test_a_rectangle_at_a_negative_origin_reports_both_correctly() -> None:
    rect = Rect(-3509, -1440, 2560, 1440)
    assert rect.origin == Point(-3509, -1440)
    assert rect.centre == Point(-2229, -720)


def test_a_point_offsets_without_being_changed() -> None:
    point = Point(10, 20)
    assert point.offset_by(5, -5) == Point(15, 15)
    assert point == Point(10, 20)
