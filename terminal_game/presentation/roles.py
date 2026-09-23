"""The six colour roles a frame's cells carry (IMPLEMENTATION_PLAN.md section 4).

Presentation names a role; the shell alone decides the colour it is painted in.
The strings are the ones the shell's palette uses, so a ``(character, role)``
cell built here is what the shell's frame check accepts.
"""

WALL = "wall"
DOT = "dot"
PLAYER = "player"
GHOST = "ghost"
STATUS = "status"
BACKGROUND = "background"

ROLES = (WALL, DOT, PLAYER, GHOST, STATUS, BACKGROUND)
