"""Plug the assembled game in and see whether smoke comes out.

The real launcher, the real game, a real window on the real desktop. This is
the only code in the project that watches the two halves meet: the launcher
and the game never import each other — they meet as processes, across a
window — so there is nothing in code for a unit test to wrap around. This
package may import the launcher, must import nothing from the game, and
nothing that ships may import it. ``tests/test_layering.py`` enforces all
three.

Run it with::

    python3 -m smoketest                  # opens one window, and takes it back
    python3 -m smoketest --show-picture   # and prints what the tab showed

Each exercise returns an :class:`~smoketest.pack.Observation` — what it did,
what it saw, and whether what it saw is what the requirement asks for.
**Exercises report; they do not assert**, because this is run by a person who
needs to see the numbers even when they are right. ``ok`` is ``True``,
``False``, or ``None`` for "observed, not judged" — the third case matters,
because several of these record a figure for a person to rule on rather than
a pass.

**It is not a gate.** Nothing blocks on it, it is in no test suite and no CI,
and it cannot be: it opens windows on a person's screen and asks macOS for
permissions.

## It arranges its own way out

The real game ends on ``q`` and on nothing else (END-6), so anything that
starts one with nobody at the keyboard has to end it. This writes ``q`` into
the tab it created, naming the captured window id, so it cannot type into
whatever the person at the machine is looking at. That is a harness technique
and it lives here rather than in ``launcher/``, because nothing in the
launcher sends input to the game and nothing should.

## Its other half

``needs_a_person`` is the register of what no machine can settle — the
colours, the legibility, a real key pressed by a real finger. The two are
meant as a pair: this puts the game on the screen, and that says what to look
at while it is there.
"""
