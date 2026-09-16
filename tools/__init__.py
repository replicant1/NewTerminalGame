"""Scripts that are run deliberately, by a person, and never by the suite.

Nothing in here is part of the application. Everything in here may open a
window, and so nothing in here is named ``test_*``: the pinned discovery
command must never collect any of it.

The one thing in here that is *imported* by the suite is
:mod:`tools.walking_skeleton`, and only for its assembly, which takes all of
its collaborators as arguments and touches no toolkit.
"""
