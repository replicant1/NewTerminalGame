"""``tests/pixels.py`` — the reading of a capture, with no capture involved.

Everything here is a pure function of bytes or of a colour count, so none of it
needs a screen and all of it belongs in the default suite. That matters more
than it looks: the two tests that *use* these functions are ``needs_window``,
excluded by default, and both currently fail before ``near`` is ever reached.
Without this file nothing would exercise them at all, and a silently wrong
``histogram`` would let that pair report whatever it liked forever — which is
the exact failure its own docstring warns about.

``histogram`` is hand-rolled binary parsing: data offset at byte 10, depth at
28, BGRA read backwards. It is tested against a BMP built here byte by byte,
because a parser tested only against files it parsed correctly is a parser
tested against nothing.
"""

from __future__ import annotations

import struct

from tests import pixels

WALL_BLUE = (0x21, 0x21, 0xDE)


#: 32 only, and not a parameter. A conformant 24bpp BMP pads every row to a
#: four-byte boundary and ``histogram`` does not skip the padding — measured:
#: a padded 3x2 file yields two spurious black pixels. A ``depth`` argument
#: here would let a later test certify a depth the parser cannot read. Every
#: capture this project takes is 32bpp, which `screencapture -t bmp` emits
#: with no padding and no trailer.
DEPTH = 32


def _bmp(pixels_rgb, width=2, height=2):
    """A minimal BMP carrying ``pixels_rgb``, bottom-up as the format wants."""
    depth = DEPTH
    step = depth // 8
    body = b"".join(
        struct.pack("<BBBB", b, g, r, 255)[:step] for (r, g, b) in pixels_rgb
    )
    offset = 14 + 40
    header = b"BM" + struct.pack("<IHHI", offset + len(body), 0, 0, offset)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, depth,
                       0, len(body), 2835, 2835, 0, 0)
    return header + info + body


class TestHistogram:
    def test_it_reads_the_colours_out_of_a_bmp(self, tmp_path):
        shot = tmp_path / "x.bmp"
        shot.write_bytes(_bmp([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 0)]))
        counts = pixels.histogram(shot, sample_every=1)
        assert counts[(255, 0, 0)] == 2
        assert counts[(0, 255, 0)] == 1
        assert counts[(0, 0, 255)] == 1

    def test_it_does_not_read_the_channels_backwards(self, tmp_path):
        """BMP stores BGRA. Getting this wrong turns the wall blue into brown
        and the test that depends on it into one that can never pass."""
        shot = tmp_path / "x.bmp"
        shot.write_bytes(_bmp([WALL_BLUE] * 4))
        counts = pixels.histogram(shot, sample_every=1)
        assert list(counts) == [WALL_BLUE]

    def test_sampling_reads_fewer_pixels_than_a_census(self, tmp_path):
        shot = tmp_path / "x.bmp"
        shot.write_bytes(_bmp([(1, 2, 3)] * 16, width=4, height=4))
        assert sum(pixels.histogram(shot, sample_every=1).values()) == 16
        assert sum(pixels.histogram(shot, sample_every=4).values()) == 4


class TestBlank:
    """The question is "did anything at all get drawn", not "how much"."""

    def test_one_colour_is_blank(self):
        assert pixels.blank({(255, 255, 255): 100})

    def test_a_few_stray_pixels_are_still_blank(self):
        # What a white window with a little window-manager chrome looks like.
        assert pixels.blank({(255, 255, 255): 99, (200, 200, 200): 1})

    def test_ink_on_two_per_cent_of_it_is_not_blank(self):
        assert not pixels.blank({(0, 0, 0): 97, WALL_BLUE: 3})

    def test_the_threshold_is_inclusive(self):
        """Exactly 98 % dominant is blank; a hair under is not. ``TestNear``
        pins its tolerance at exactly 24 and 25, and this is the same job."""
        assert pixels.blank({(0, 0, 0): 98, WALL_BLUE: 2}, threshold=0.98)
        assert not pixels.blank({(0, 0, 0): 97, WALL_BLUE: 3}, threshold=0.98)

    def test_an_empty_count_is_not_called_blank(self):
        """Nothing measured is not the same as nothing drawn, and saying so
        would let a failed capture pass as a painted window."""
        assert not pixels.blank({})


class TestNear:
    def test_the_exact_colour_counts(self):
        assert pixels.near({WALL_BLUE: 7}, WALL_BLUE) == 7

    def test_an_antialiased_fringe_counts(self):
        # What the wall blue arrives as after a colour profile and a glyph edge.
        assert pixels.near({(0x30, 0x30, 0xd0): 5}, WALL_BLUE) == 5

    def test_a_different_blue_does_not(self):
        """This is what a tolerance of 24 actually admits: pure blue is 33
        away on the red channel, so it is not the wall's colour."""
        assert pixels.near({(0, 0, 255): 5}, WALL_BLUE) == 0

    def test_white_is_nowhere_near_it(self):
        assert pixels.near({(255, 255, 255): 1000}, WALL_BLUE) == 0

    def test_the_tolerance_is_a_cube_around_the_colour(self):
        just_in = (0x21 + 24, 0x21, 0xDE)
        just_out = (0x21 + 25, 0x21, 0xDE)
        assert pixels.near({just_in: 1}, WALL_BLUE) == 1
        assert pixels.near({just_out: 1}, WALL_BLUE) == 0
