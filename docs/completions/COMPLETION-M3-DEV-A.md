# COMPLETION — M3 · Dev A · WI-13, closing the gaps the final gate found

**Branch** `wi-13-close-the-gaps`, cut from `origin/main` at `d49f046`.
**PR** #16, against `main`. Not merged — the lead merges.
**Product code changed:** none. `git diff origin/main -- termgame/` is empty.

---

## 1. The suite

```
$ /usr/bin/python3 -m unittest discover -s tests
Ran 774 tests in 13.246s

OK (skipped=2)
```

`main` was 749. **25 tests added, none removed, none weakened.** The two skips
are the unchanged `tests/test_launch_smoke.py::LaunchSmokeTest` — *"no
controlling tty: nobody is watching this screen"* — which skips in every agent
session by design.

## 2. What was confirmed, and what was built

All eight of WI-12's findings were **re-checked against the code before being
acted on**, and all eight held. Nothing was taken on trust.

| # | WI-12's finding | Confirmed? | What now covers it |
| --- | --- | --- | --- |
| 1 | SCRN-7's hidden cursor asserted by the probe's own `curs_set` | yes | `ScriptedGameThroughRealCursesTest::test_the_text_cursor_is_not_visible_while_the_game_is_running` reads back what the **game** left behind, from inside the real `session()` |
| 2 | WIN-2 size test is a closed loop over the pty it sized | yes | pty sized from `model.SCREEN_*`, asserted against `window.ROWS/COLUMNS`; breaks from either side |
| 3 | no test asserts any colour; SCRN-6 has nothing | yes — `33`, `178`, `51` appeared nowhere in `tests/` | three levels: the index and its **hue** in `test_theme.py`, the number handed to `init_pair` in `test_screen_adapter.py`, the escape sequence a real terminal receives in `test_curses_pty.py` |
| 4 | CTRL-5's echo clause asserted nowhere; ARCHITECTURE misrecords it | yes — and there is no `Screen.__enter__` at all | `NothingTypedIsEchoedTest`, plus `docs/findings/WI-13-curses-echo.md` and a correction in `docs/ARCHITECTURE.md` |
| 5 | START-2's metric is not pinned; blocks WI-11 | yes — **I recomputed it: 0 of 200 seeds disagree** | `GhostMetricDiscriminationTests`, two hand-built boards |
| 6 | `test_maze.py:152` named for 1000 seeds, loops 200 | yes | sweep raised to `SEEDS` (1000); 0.74 s, all 1000 distinct |
| 7 | `test_window_supervisor.py:112` tautology | yes | once-each count over open/configure/move/close |
| 8 | the pty unmapped-key test's "did not quit" half is hollow | yes — **measured**: with `z` in `QUIT_KEYS` and the old order, all 21 tests still passed | `z` moved to second; the same mutation now reddens five |

## 3. Every new assertion, broken on purpose

Not a mutation sweep (plan §2.7 forbids that, and none was run): one specific
break per assertion, to prove one specific test discriminates. Messages
verbatim.

| what was broken | what went red |
| --- | --- |
| `starting_ghost` → Manhattan | `Position(row=1, col=6) != Position(row=4, col=4) : START-2 is not being measured by squared Euclidean distance. If this is WI-11 applying the user's answer to question A2, this is the test that was built to notice, and the expected square above changes with the metric.` |
| `starting_ghost` → Chebyshev | `Position(row=5, col=5) != Position(row=1, col=6) : ...` (plus the pre-existing hand-written-board test WI-12 predicted) |
| theme status `51` → `39` | `5 != 3 : the status line is not full green, so not cyan`; `51 != 39 : the status style no longer asks for colour 51, cyan (SCRN-6)`; `39 != 51 : the fallback's status has drifted from theme.py`; `b'\x1b[38;5;51m' not found in b'...' : the terminal was never asked for colour 51, the cyan status line (SCRN-6)` |
| `init_pair(pair, 7, -1)` | `33 != 7 : the wall style reaches curses as 7, not as the theme's 33` |
| `_hide_cursor()` deleted | `0 != 1 : the game left the text cursor visible in the maze (SCRN-7)` |
| `curses.noecho()` deleted | `b'z' unexpectedly found in b'\x1b[?1049h ... \x1b[H\x1b[2Jzzz ...' : the keystrokes the player typed were echoed back into the window: `z` appears 3 times in what the game wrote to the terminal (CTRL-5)` |
| `window.COLUMNS` 40 → 41 | `Lists differ: [30, 41] != [30, 40]` |
| `model.SCREEN_ROWS` 30 → 29 | `Lists differ: [30, 40] != [29, 40]` |
| `z` added to `QUIT_KEYS` | five red, including `the unmapped key did not quit`: `Lists differ: [2, 5] != [1, 2]` |
| `supervise()` opening twice | `1 != 2 : expected exactly one 'open', got [... 'open', 'open', ...]` |

**One of my own tests failed this check and was rewritten.** The first CTRL-5
test read the tty's ECHO bit; deleting `noecho()` left it green. See §5.

## 4. No defect in `termgame/`

Every gap was a missing or hollow assertion. Nothing required a product
change and none was made.

## 5. The finding worth keeping

`docs/findings/WI-13-curses-echo.md`. Two measurements that make the obvious
CTRL-5 tests hollow:

1. **`initscr` clears the tty's ECHO bit by itself, and `curses.echo()` never
   sets it back.** ncurses echoes in software from inside `wgetch`. An
   assertion on that bit passes whatever the game does.
2. **A painted screen swallows the echo.** `wechochar` writes at the cursor,
   and after a full repaint the cursor is parked on the bottom-right cell —
   this project's own C1 hazard. Measured, three `z`s with `curses.echo()`
   forced on: 3 back with no paint, 1 with a paint, 3 with a paint and a
   `move(5, 5)`, and **0** in the real scripted game.

Consequence for the product, **not a defect**: CTRL-5's echo clause currently
holds for two independent reasons, `noecho()` and the corner. Nothing needs
changing, but it is why the clause looks untestable from the game and is not.

## 6. Deviations needing a ruling

1. **An extra test file was touched that the brief did not name.**
   `tests/test_screen_adapter.py` gained `BuildAttributesTest` and
   `TheFallbackPaletteTest`. The brief said to assert what the code requests
   "for the status line and for anything else with a colour in it";
   `build_attributes` is the last place a colour is a number, so I judged it
   in scope. Additive, and easy to drop if not wanted.
2. **`test_maze.py` now runs 1000 seeds instead of 200**, adding ~0.75 s to
   the suite. I chose to make the name true rather than make it smaller. Say
   if the second-of-suite matters more.
3. **`docs/ARCHITECTURE.md` carries a visible correction note**, not just a
   rewritten row. I thought a silent rewrite would lose the fact that the
   project once recorded a verification that had not happened.
4. **`docs/findings/WI-13-curses-echo.md` was written unasked.** It is a
   measurement someone will rely on later and the PR summary will not be read
   again, so it went where the conventions say findings go.
5. **`./verify` was not run.** Its smoke stage opens a real window on the
   user's screen and nobody asked for one.

## 7. Contradictions found in the plan or the architecture

1. **`docs/ARCHITECTURE.md:642`** claimed CTRL-5 was *"measured: `noecho` set
   in `Screen.__enter__`"*. Wrong twice over — no such method, and nothing
   measured. **Corrected by this branch**, in place, with a note.
2. **`IMPLEMENTATION_PLAN.md:1151`** carries the same claim in the milder form
   *"echo is off"*. It is **now true**, so it is left alone — but it inherited
   the same unverified belief and the lead may want to date it.
3. **Plan §11 credits START-2 to an "exhaustive recount"**, which is real and
   exhaustive and, as WI-12 said and I confirmed, blind to the metric. The
   recount is no longer the only evidence; the traceability row could now name
   `GhostMetricDiscriminationTests` beside it.

## 8. What needs a human

Unchanged by this branch, and still outstanding:

- **The six human checks, 0 of 6 run.** Plan §13 item 4 is still not met.
  `docs/findings/WI-12-human-check-results.md` holds a line for each.
- **H6 in particular.** This branch asserts that the code *asks* for cyan, at
  three levels including the bytes a real terminal receives. Whether cyan
  *looks* cyan in the user's Terminal profile is still H6's, exactly as the
  lead ruled.
- **The three open questions A1, A2, A3.** Still with the user. **A2 is no
  longer dangerous to answer**: WI-11 can change the metric and
  `GhostMetricDiscriminationTests` will notice.
- **A trap, for whoever runs the suite next.** This `python3` uses
  `sys.pycache_prefix` under `~/Library/Caches/com.apple.python`, and a
  same-size source edit made within the same second as the cached `.pyc` is
  not invalidated. It cost me five spurious failures from a `51` → `39`
  restore that silently did not take. If a test fails against a source file
  that plainly says otherwise, purge that cache before believing it.

## 9. Window hygiene

**No window was opened by this work.** Everything here is pty-based, and a pty
belongs to nobody and is on nobody's screen. Terminal census taken at the end,
read-only: all `[367, 2486, 2420, 2440]`, visible `[367, 2486]` — exactly the
established values. Nothing of the user's was opened, closed or touched.
