01:14:26Z  START   WI-4 curses adapter and the loop with its one deadline
01:14:44Z  READ    FUNCTIONAL_REQUIREMENTS.md in full (CTRL-1..5, GHOST-1, SCRN-7, END-6)
01:14:59Z  READ    IMPLEMENTATION_PLAN §2 ground rules, §5 WI-4 brief, §10.1 ruling
01:15:13Z  READ    ARCHITECTURE §5.5, §6.1, §6.2, §7, §8
01:17:43Z  PLAN    pure controls.py (key->command) + ticker.py (deadline), impure screen.py (sole curses importer), loop.py rewritten as a fake-drivable loop, standins.py that WI-9 deletes
01:17:53Z  TEST    186 passed, 0 failed, 2 skipped (baseline on main before any WI-4 change)
01:19:01Z  NOTE    purity guard names the impure trio {screen, loop, window}; the curses adapter must therefore be termgame/screen.py
01:19:01Z  ASK     what style identifiers does WI-3 use for wall/dot/player/ghost/status? Dev A owns the names and WI-3 has not merged
01:19:01Z  ASSUME  the adapter palette is keyed on those five plain names and an unknown identifier falls back to the default attribute, so a mismatch loses colour and never the picture. Affects termgame/screen.py PALETTE only; a self-arming test asserts every identifier WI-3 emits is known the moment view.py lands
01:19:47Z  NOTE    lead endorses the lenient-palette design and the self-arming test; will relay WI-3 style names when Dev A commits termgame/theme.py. Proceeding on the ASSUME, not holding up
01:22:23Z  NOTE    lead relayed WI-3 style names: wall/dot/player/ghost/status + default — my guess matched. Adapter now READS termgame.theme.STYLES when present rather than hardcoding colours; the fallback table stays for this branch alone
01:22:39Z  COMMIT  5f4a24c WI-4: the two pure decisions, the curses adapter and the real loop
01:24:34Z  TEST    40 passed, 0 failed, 0 skipped (test_controls.py + test_ticker.py alone)
01:24:34Z  NOTE    measured: int((10.1-10.0)*1000) is 99, not 100 — truncating a dirty float loses up to 1ms, costing one extra turn of the loop (0.25ms paint) and no tick. Tests assert exact ms only on binary-exact values
