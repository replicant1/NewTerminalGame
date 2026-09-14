"""The Domain: the game as a set of facts, with nothing impure in it.

Nothing in this package imports `curses`, `subprocess`, `os`, `time` or
`sys`, and nothing in it knows anything about a screen (implementation plan
§3, architecture caution C5). Two columns per square, three-column actor
glyphs and the 40 x 30 frame belong to Presentation; if any of that leaked in
here, the maze tests would stop being about mazes and MAZE-5 and MAZE-6 would
become much harder to check.

Randomness enters only through a seed or a random source handed in, so every
maze this package produces can be reproduced exactly in a test.

`tests/test_layering.py` holds that rule to account.
"""
