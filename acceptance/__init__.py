"""The acceptance pack: what a machine can check, and what it cannot.

WI-14a. This is the machinery WI-14b runs. It has two halves and the division
between them is the point of it:

* :mod:`acceptance.pack` — **exercises**, which drive the real launcher and the
  real game on the real desktop and report what they observed.
* :mod:`acceptance.checks` — **the human-check register**, everything no agent
  can settle, with the exact steps for a person and what to look for.

**Nothing here records a human check as verified**, and there is a test that
nothing can. The register carries observations and questions; the answers are
WI-14b's to collect from a person.

Run it with::

    python3 -m acceptance --list       # the human checks, and nothing opened
    python3 -m acceptance --run        # the exercises, on the real desktop

**This pack arranges its own way out.** M0's ``--hold`` was scaffolding and the
real game exits on ``q`` and never on a timer, so anything that starts a game
with nobody at the keyboard has to end it. This pack ends it by writing ``q``
into the tab it created — ``do script "q" in selected tab of window id N``,
measured by WI-3 reaching the game in 0.14 s. It names the captured window id
like every other call, so it does not depend on which window has focus and does
not inject a keystroke into whatever the person at the machine is looking at.

It **never** uses a hold, and it never starts a game and hopes.

The five stale executables at the repository root — ``verify``,
``launch-smoke``, ``check-window-placement``, ``play`` and ``Terminal Game`` —
are not used, not read and not resurrected. This is written from nothing.
"""
