# -*- coding: utf-8 -*-
"""The Application layer: what drives a game, as opposed to what a game is.

``Shell -> Presentation -> Application -> Domain``.  This layer may name the
Domain and nothing above it: no windowing toolkit, no frame, no intent, no
clock.  Everything it needs from above is **handed to it** as a plain
callable, which is what lets a whole game run with no window at all.
"""
