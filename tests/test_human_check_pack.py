"""``docs/findings/WI-10-human-checks.md`` — the pack, kept honest.

A document cannot be unit-tested for being *good*. It can be tested for going
**stale**, and that is the failure this pack is actually exposed to: it quotes
a title, a font size, a window shape, a status line, four glyphs and the first
words of an error message, every one of which lives in the code and every one
of which somebody could change without opening this file. A pack that tells a
person to look for the wrong thing is worse than no pack, because they will
report a pass.

So each fact the pack asserts about the game is checked here against the module
that decides it. Nothing here judges the prose.

The other property tested is the one the plan asks for in so many words: *it
must be usable by someone who has not read this plan*. That is checked as the
absence of the plan's own vocabulary from the part a reader reads.
"""

import io
import os
import re
import unittest

from termgame import theme, window
from termgame.model import Outcome

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO_ROOT, "docs", "findings", "WI-10-human-checks.md")

with io.open(PACK_PATH, encoding="utf-8") as handle:
    PACK = handle.read()

#: The part a person reads. The last section is addressed to whoever collects
#: the answers and is allowed to speak the plan's language.
FOR_THE_READER = PACK.split("## For whoever collects the answers")[0]

#: The six check headings, in the order they must appear — the same order as
#: H1..H6, which is what makes the mapping at the foot of the pack trivial.
CHECK_HEADINGS = (
    "## 1. Where the game window lands",
    "## 2. That `q` closes the game's window and nothing else",
    '## 3. That the title bar reads exactly "Terminal Game"',
    "## 4. That the text is big enough to read comfortably",
    "## 5. That nothing flickers while the ghost moves",
    "## 6. That the picture looks right",
)


class TheSixChecksAreAllThere(unittest.TestCase):
    def test_there_is_a_section_for_each_of_the_six(self):
        for heading in CHECK_HEADINGS:
            self.assertIn(heading, PACK, heading)

    def test_they_are_in_the_order_the_mapping_at_the_foot_claims(self):
        positions = [PACK.index(heading) for heading in CHECK_HEADINGS]
        self.assertEqual(sorted(positions), positions)

    def test_each_one_says_what_to_type_what_to_see_and_what_would_be_wrong(self):
        # The three things the plan asks every check to be written as.
        sections = PACK.split("\n## ")
        for heading in CHECK_HEADINGS:
            body = next(
                part for part in sections if part.startswith(heading[3:])
            )
            for required in (
                "### What to type",
                "### What you should see",
                "### What counts as a failure",
            ):
                self.assertIn(required, body, "%s is missing %s" % (heading, required))

    def test_each_one_says_what_to_write_down(self):
        # The answers are collected verbatim, so the pack has to ask for words.
        self.assertEqual(6, PACK.count("### What to write down"))

    def test_the_mapping_to_the_requirement_codes_is_at_the_foot(self):
        for code in ("H1", "H2", "H3", "H4", "H5", "H6"):
            self.assertIn(code, PACK)
        for code in ("WIN-2", "WIN-3", "WIN-4", "WIN-5", "SCRN-7", "SCRN-3"):
            self.assertIn(code, PACK)


class ItIsWrittenForSomebodyWhoHasNotReadThePlan(unittest.TestCase):
    """Plan §5, WI-10: *"It must be usable by someone who has not read this
    plan."*"""

    def test_the_part_a_person_reads_uses_none_of_the_plans_vocabulary(self):
        for jargon in (
            "work item",
            "WI-",
            "iteration",
            "milestone",
            "M0",
            "M2",
            "the conductor",
            "the technical lead",
            "developer.md",
        ):
            self.assertNotIn(jargon, FOR_THE_READER, "found %r" % jargon)

    def test_it_does_not_make_the_reader_learn_the_h_codes(self):
        for code in ("H1", "H2", "H3", "H4", "H5", "H6"):
            self.assertNotIn(code, FOR_THE_READER, code)

    def test_it_never_asks_for_a_requirement_code_in_an_answer(self):
        for code in ("WIN-4", "SCRN-7", "SCRN-5", "STAT-1"):
            self.assertNotIn(code, FOR_THE_READER, code)

    def test_it_says_up_front_that_no_prior_reading_is_needed(self):
        self.assertIn("You do not need to know anything about how the game was", PACK)

    def test_it_says_roughly_how_long_it_will_take(self):
        self.assertIn("about ten minutes", PACK)


class EveryCommandItTellsYouToTypeExists(unittest.TestCase):
    """A pack that names a program that is not there wastes somebody's evening."""

    def commands(self):
        found = set(re.findall(r"^\./([A-Za-z0-9][-A-Za-z0-9_]*)$", PACK, re.M))
        self.assertTrue(found, "the pack tells nobody to type anything")
        return found

    def test_it_names_the_three_programs_and_only_those(self):
        self.assertEqual(
            {"play", "verify", "check-window-placement"}, self.commands()
        )

    def test_every_one_of_them_is_there_and_is_executable(self):
        for name in self.commands():
            path = os.path.join(REPO_ROOT, name)
            self.assertTrue(os.path.exists(path), "%s does not exist" % name)
            self.assertTrue(os.access(path, os.X_OK), "%s is not executable" % name)

    def test_the_file_it_sends_the_reader_to_for_the_picture_exists(self):
        self.assertIn("docs/FUNCTIONAL_REQUIREMENTS.md", PACK)
        self.assertTrue(
            os.path.exists(os.path.join(REPO_ROOT, "docs", "FUNCTIONAL_REQUIREMENTS.md"))
        )


class EveryFactItQuotesIsStillTrueOfTheCode(unittest.TestCase):
    """The staleness guard. Each of these lives somewhere in ``termgame``."""

    def test_the_title_it_says_to_look_for_is_the_one_the_window_is_given(self):
        self.assertEqual("Terminal Game", window.CHILD_NAME)
        self.assertIn('reads exactly "Terminal Game"', PACK)
        self.assertIn("```\nTerminal Game\n```", PACK)

    def test_the_window_shape_it_quotes_is_the_one_the_launcher_sets(self):
        self.assertIn(
            "%d characters wide and %d\nlines tall" % (window.COLUMNS, window.ROWS),
            PACK,
        )

    def test_the_font_it_quotes_is_the_one_the_launcher_sets(self):
        self.assertEqual("Menlo-Regular", window.FONT_NAME)
        self.assertEqual(18, window.FONT_SIZE)
        self.assertIn("**%d point Menlo**" % window.FONT_SIZE, PACK)

    def test_the_offset_it_describes_is_the_one_the_launcher_applies(self):
        self.assertEqual((30, 30), tuple(window.OFFSET))
        self.assertIn("about 30 pixels each way", PACK)

    def test_the_status_line_it_quotes_is_the_one_the_game_draws(self):
        drawn = " " * theme.STATUS_INDENT + theme.status_text(Outcome.PLAYING, 0)
        self.assertIn(drawn, PACK)

    def test_the_two_entity_glyphs_it_quotes_are_the_ones_the_game_draws(self):
        self.assertIn("".join(theme.PLAYER_GLYPHS), PACK)
        self.assertIn("".join(theme.GHOST_GLYPHS), PACK)

    def test_the_lone_wall_block_it_quotes_is_the_one_the_game_draws(self):
        # A wall square with no wall beside it: mask 0.
        self.assertIn("(`%s`)" % theme.glyph_for_mask(0), PACK)

    def test_the_corner_and_tee_glyphs_it_quotes_are_in_the_wall_alphabet(self):
        for glyph in "╔╗╚╝╦╣╩╠╬":
            self.assertIn(glyph, theme.WALL_ALPHABET, glyph)
            self.assertIn(glyph, PACK, glyph)

    def test_the_ghost_speed_it_quotes_is_the_one_the_clock_keeps(self):
        from termgame import ticker

        self.assertEqual(7.0, ticker.GHOST_TICKS_PER_SECOND)
        self.assertIn("seven squares a second", PACK)

    def test_the_redraw_budget_it_quotes_is_one_tick_of_the_clock(self):
        from termgame import ticker

        self.assertEqual(143, round(ticker.GHOST_TICK_SECONDS * 1000))
        self.assertTrue(
            "It has 143" in PACK and "milliseconds to redraw" in PACK,
            "the pack no longer quotes the 143 ms redraw budget",
        )

    def test_the_blank_right_hand_margin_it_mentions_is_the_real_width(self):
        from termgame import view
        from termgame.model import MAZE_COLS, SCREEN_COLS

        self.assertEqual(3, SCREEN_COLS - (2 * MAZE_COLS - 1))
        self.assertIn("right-hand three columns", PACK)
        self.assertEqual(3, len(view.margin_columns(_a_full_width_maze())))


def _a_full_width_maze():
    from termgame import maze as mazelib
    from termgame.model import MAZE_COLS

    return mazelib.from_text("\n".join(["#" * MAZE_COLS] * 3))


class TheMeasurementsItQuotesAreTheOnesThatWereTaken(unittest.TestCase):
    """Numbers WI-9 measured against real processes, quoted rather than
    re-derived.

    They are in the pack for one reason: a person who sees flicker, or thinks
    the ghost feels wrong, should not spend an afternoon on a cause that has
    already been ruled out. So each one is checked against the document that
    recorded it, and a change to either without the other is a failure here.
    """

    def setUp(self):
        with io.open(
            os.path.join(REPO_ROOT, "docs", "findings", "WI-9-the-running-game.md"),
            encoding="utf-8",
        ) as handle:
            self.source = handle.read()

    def test_the_slowest_redraw_it_quotes_was_actually_measured(self):
        self.assertIn("20.3 ms", self.source)
        self.assertIn("**20.3 ms**", PACK)

    def test_the_three_tick_rates_it_quotes_were_actually_measured(self):
        for rate in ("6.99990", "7.00078", "6.99999"):
            self.assertIn(rate, self.source, rate)
            self.assertIn(rate, PACK, rate)

    def test_the_time_it_says_a_motionless_player_survived_was_measured(self):
        self.assertIn("4.14 seconds", self.source)
        self.assertIn("**4.14 seconds**", PACK)

    def test_it_tells_the_reader_the_game_ends_without_them(self):
        # Otherwise a person watching for flicker reads a finished game as a
        # frozen one, and reports the wrong failure.
        self.assertIn("The game will end on its own if you leave it alone", PACK)
        self.assertIn("only `q` does", PACK)


class TheKnownDisplayFaultIsExplainedInTheWordsTheGameUses(unittest.TestCase):
    """WI-8 measured this and made it audible. The pack is where it becomes
    useful to a person."""

    def test_the_pack_quotes_the_launchers_line_exactly(self):
        # Quoted, not paraphrased: it is what the person greps for.
        self.assertIn("could not read the screen layout", PACK)

    def test_the_launcher_really_prints_that_line(self):
        with io.open(
            os.path.join(REPO_ROOT, "termgame", "window.py"), encoding="utf-8"
        ) as handle:
            source = handle.read()
        self.assertIn("could not read the screen layout", source)

    def test_it_warns_the_reader_before_they_look_at_anything(self):
        preamble = PACK.split("## A. All six in one sitting")[0]
        self.assertIn("could not read the screen layout", preamble)
        self.assertIn("known fault", preamble)
        self.assertIn("displays", preamble)

    def test_it_says_what_the_wrong_screen_looks_like_and_asks_for_a_report(self):
        self.assertIn("main", PACK)
        self.assertIn("worth reporting", PACK)

    def test_the_fallback_it_describes_is_the_one_the_launcher_falls_back_to(self):
        left, top, wide, tall = window.FALLBACK_SCREEN_BOUNDS
        self.assertIn("%d × %d" % (wide, tall), PACK)


class TheSafetyAdviceMatchesWhatTheProgramsActuallyDo(unittest.TestCase):
    def test_it_tells_the_reader_what_the_LEFT_OPEN_message_means(self):
        # Both ./launch-smoke and ./verify print it, and neither forces a busy
        # tab. A person who sees it needs to know it is deliberate.
        self.assertIn("LEFT OPEN: Terminal window id", PACK)
        with io.open(os.path.join(REPO_ROOT, "verify"), encoding="utf-8") as handle:
            self.assertIn("LEFT OPEN: Terminal window id", handle.read())

    def test_it_names_the_modal_sheet_by_the_words_that_appear_on_it(self):
        self.assertIn(
            "Do you want to terminate running processes in this", PACK
        )

    def test_it_tells_the_reader_to_cancel_that_dialog_rather_than_terminate(self):
        found = PACK.split("Do you want to terminate running processes in this")[1]
        self.assertIn("Cancel", found[:400])

    def test_it_promises_only_what_the_launcher_actually_does(self):
        self.assertIn("opens **one** new Terminal window", PACK)
        self.assertIn("does not change any Terminal preference", PACK)

    def test_it_says_q_is_the_only_way_out(self):
        self.assertIn("That is the only\nkey that ends it", PACK)


class WhatItSaysTheMachineAlreadyChecked(unittest.TestCase):
    def test_it_names_the_verification_command_and_what_it_covers(self):
        tail = PACK.split("## What the machine already checked")[1]
        self.assertIn("./verify", tail)
        self.assertIn("it says which part and why", tail)

    def test_it_does_not_claim_the_machine_checked_any_of_the_six(self):
        tail = PACK.split("## What the machine already checked")[1]
        self.assertIn("None of that can see a screen or press a key", tail)


if __name__ == "__main__":
    unittest.main()
