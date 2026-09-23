"""Terminal Game: a maze, a player, a ghost and some dots, in a window of its own.

The package is four layers, one subpackage each (IMPLEMENTATION_PLAN.md section
1.4), declared in ``pyproject.toml`` and checked by ``tools/layer_check.py``:

    shell  ->  presentation  ->  application  ->  domain

Each may import from the layers below it and never from one above.
"""
