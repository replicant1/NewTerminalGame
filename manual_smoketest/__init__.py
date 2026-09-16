"""The half of the smoke test a person has to do by hand.

Twelve checks, covering twenty-one requirement codes, each with what a person
must do, what a correct answer looks like, and — the field that carries the
weight — **why no machine can answer it**.

Not all of it is looking. Seven of the twelve are settled by watching the
screen; the other five are pressing arrow keys, playing several games, typing
at a shell afterwards, comparing saved preferences, and revoking a macOS
permission to answer its dialog with "Don't Allow". "Manual" is the honest
word for the set; "visual" would leave five of them outside their own package.

**Read `why_machine_cannot` as a claim about a measured route, not about
every possible one.** Each says how somebody found out, and a reason that
holds for AppleScript need not hold for a pseudo-terminal or a screen
capture. The name of this package says these are done by hand today, which is
a fact about the process; it does not assert that no instrument could ever
reach them.

Run it with::

    python3 -m manual_smoketest        # prints the register; opens nothing

**Nothing here is recorded as verified, and nothing here can be.** A
``HumanCheck`` has no ``passed`` field — not set to ``False``, absent — so an
agent cannot mark one done, because there is nowhere to write it. That is the
whole reason this is code rather than a markdown checklist.

## Its other half

``smoketest`` is what a machine *can* establish about the assembled game, and
the two are meant as a pair: ``python3 -m smoketest`` puts the real game on
the screen, and this says what to look at while it is there. They are separate
packages because they have different contracts — one reports numbers and exits,
the other is read by a person and never passes or fails at all.

This package imports nothing. It is a register, not an instrument.
"""
