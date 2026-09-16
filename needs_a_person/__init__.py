"""Everything about this game that no machine can settle.

Twelve checks, covering twenty-one requirement codes, each with what a person
must do, what a correct answer looks like, and — the field that carries the
weight — **why no machine can answer it**.

Run it with::

    python3 -m needs_a_person        # prints the register; opens nothing

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
