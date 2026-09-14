"""The window launcher — the only part of the system that touches the desktop.

This package is the launcher process. It knows nothing about mazes, and nothing
in the game imports it (architecture caution C11).

The five modules divide the risk up so that almost all of it is testable with no
desktop attached:

``geometry``  pure arithmetic — the offset and the clamp. No I/O of any kind.
``script``    pure text — the AppleScript source each operation would run.
``runner``    the seam — the one place a subprocess is started, always bounded.
``desktop``   the typed adapter — script plus runner, parsing results back.
``launcher``  the lifecycle policy — ask first, create, capture, configure,
              move, and reap by the captured identity.
"""
