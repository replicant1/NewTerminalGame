"""The six colours the specification names, and that they are usable as colours."""

from __future__ import annotations

import pytest

from terminal_game.presentation import palette


class TestEveryRequirementThatNamesAColourHasOne:
    """Six requirements name a colour in words; six constants answer them."""

    @pytest.mark.parametrize(
        "requirement",
        ["WIN-2", "SCRN-3", "SCRN-4", "SCRN-5 player", "SCRN-5 ghost", "SCRN-6"],
    )
    def test_the_requirement_has_a_colour(self, requirement):
        assert requirement in palette.BY_REQUIREMENT

    def test_there_are_no_colours_belonging_to_no_requirement(self):
        assert len(palette.BY_REQUIREMENT) == 6

    def test_every_colour_is_a_real_colour(self):
        not_colours = {
            name: value
            for name, value in palette.BY_REQUIREMENT.items()
            if not palette.is_colour(value)
        }
        assert not_colours == {}


class TestTheColoursThemselves:
    """The exact values, so a change to one is a change somebody decided to make."""

    def test_the_ground_is_black(self):
        assert palette.GROUND == "#000000"

    def test_the_player_is_bright_yellow(self):
        assert palette.PLAYER == "#ffff00"

    def test_the_status_line_is_cyan(self):
        assert palette.STATUS == "#00ffff"

    def test_the_wall_is_blue(self):
        # SCRN-3's "blue": the arcade maze blue, not a pure #0000ff.
        assert palette.WALL == "#2121de"

    def test_the_dot_is_dim_gold(self):
        # SCRN-4's "dim gold": CSS darkgoldenrod.
        assert palette.DOT == "#b8860b"

    def test_the_ghost_is_pink(self):
        # SCRN-5's "pink": CSS hotpink.
        assert palette.GHOST == "#ff69b4"


class TestTheColoursDoTheirJob:
    """What the requirements ask of the colours, as opposed to what they are."""

    def test_the_two_actors_differ_in_colour(self):
        # SCRN-5: "so the two can be told apart by colour and by outline".
        # The outline half is WI-4's; this is the colour half.
        assert palette.distinct_actor_colours()
        assert palette.PLAYER != palette.GHOST

    def test_nothing_drawn_on_the_ground_is_the_ground_colour(self):
        # Anything painted in the background colour would be invisible.
        drawn = set(palette.ALL_COLOURS) - {palette.GROUND}
        assert palette.GROUND not in drawn
        assert len(drawn) == 5

    def test_every_colour_is_different_from_every_other(self):
        # Six requirements, six distinguishable colours.  Two the same would
        # mean a requirement is not actually being met on screen.
        assert len(palette.ALL_COLOURS) == 6

    def test_the_dot_is_dimmer_than_the_player(self):
        # SCRN-4 asks for a *dim* gold and SCRN-5 for a *bright* yellow, and
        # the two sit next to each other whenever the player is on a dot's
        # square.  Compare total ink: the dim one must be the darker.
        def brightness(colour):
            return sum(int(colour[i : i + 2], 16) for i in (1, 3, 5))

        assert brightness(palette.DOT) < brightness(palette.PLAYER)


class TestWhatCountsAsAColour:
    """``is_colour`` is what keeps a non-colour from reaching the toolkit."""

    @pytest.mark.parametrize(
        "value", ["#000000", "#ffffff", "#2121de", "#ABCDEF", "#abcdef"]
    )
    def test_an_rrggbb_triple_is_a_colour(self, value):
        assert palette.is_colour(value)

    @pytest.mark.parametrize(
        "value",
        [
            "pink",         # a toolkit colour name: the toolkit's table, not ours
            "#fff",         # the short form, which we do not accept
            "#12345",       # too short
            "#1234567",     # too long
            "#gggggg",      # not hexadecimal
            "000000",       # no hash
            "",
            None,
            0x000000,       # a number is not a colour
            ("#000000",),
        ],
    )
    def test_anything_else_is_not_a_colour(self, value):
        assert not palette.is_colour(value)
