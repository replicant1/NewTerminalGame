"""Tests for the Shell layer.

**No test in this package may construct a toolkit window.**  The windowing
toolkit is stood in for by :class:`tests.shell.recording_toolkit.RecordingToolkit`
throughout.  Anything that has to appear on a screen is a script under
``tools/``, run deliberately by a person, and is never discovered by the
suite.
"""
