# WI-10a — the window census race fix

Branch `wi-10a-census-race`, based on `origin/main` at `37def54`.

## The defect

`termgame/window.py` :: `script_visible_window_ids()` built its census with

```applescript
repeat with w in windows
    if visible of w then set out to out & (id of w as text) & linefeed
end repeat
```

AppleScript resolves that loop variable **lazily** — every iteration is really
`item N of every window` — so a window that disappears while the loop is
running invalidates the index and the whole script dies:

```
osascript failed (1): execution error: Terminal got an error:
Can't get item 5 of every window. Invalid index. (-1719)
```

WI-10 *observed* this. It is not hypothetical, and it was observed on the
census taken **immediately after a close**, which is exactly the moment a
window is going away. Every close path in this project takes that census, so
this is load-bearing: the census failing throws `WindowError` out of
`visible_window_ids()` and takes the caller with it.

## The fix

One query, evaluated by Terminal in a single step, with no index to go stale:

```applescript
tell application "Terminal" to get id of every window whose visible is true
```

## Why the output still parses — measured, not assumed

The old script accumulated a linefeed-separated string. The new one returns an
AppleScript **list**, and `osascript` prints a list differently. Measured
against the real Terminal on 2026-09-11 (`docs/findings/WI-10a-census-output-shape.md`):

| visible windows | stdout (raw) | `parse_window_ids` |
| --- | --- | --- |
| two | `367, 2486\n` | `[367, 2486]` |
| one | `367\n` | `[367]` |
| none | `\n`, exit status 0 | `[]` |

`parse_window_ids` already split on `,` as well as on linefeeds, so all three
shapes parse, and the empty case — the one worth checking hardest — yields an
empty list rather than raising or yielding `[0]`. The only caller,
`visible_window_ids()`, therefore still gets exactly what it got before: a list
of ints, order not depended on anywhere (both smoke assertions `sorted()` it).

## Two stale literals the tests were hiding behind

Neither was in WI-10's original uncommitted patch, and each of them turned a
test green for the wrong reason once the script changed:

1. **`classify()` in `tests/test_window_failure_paths.py`** keyed the census
   off the literal `if visible of w then`. With the script rewritten, the fake
   Terminal stopped recognising the census entirely and answered `""` — so the
   smoke's before-census came back empty and the reconcile check passed
   vacuously. It now keys off `every window whose visible is true`.
2. **The census-lie in `tests/test_launch_smoke_script.py`** keyed off `set out
   to`. It stopped lying, so the test that proves *a census which does not
   reconcile fails the run* was passing against a smoke nothing was wrong with.
   It now recognises the census through `classify()`, so it cannot go stale
   against a script rewrite again.

The fake's census answer is also now `", "`-joined, the shape `osascript`
really prints. Otherwise the fake would have been the last place in the project
where the old wire shape still existed, and the parser would never have been
exercised on the shape it now actually receives.

## Tests

`tests/test_window_script.py`:

- `test_the_census_reads_visible_not_exists` / `test_the_census_only_reads_ids`
  — updated for the new script.
- `test_the_census_asks_once_rather_than_walking_an_index` — no `repeat`, no
  `item`, one line. True but weak on its own: it is a statement about the text,
  and it would go on passing if the census were rewritten into some *other*
  index-walking form.

`tests/test_window_supervisor.py` — new class
`CensusAcrossAVanishingWindowTest`, which is where the weight is carried,
because this file's whole purpose is asserting consequences with
`run_osascript` replaced:

- `TerminalLosingAWindow` is Terminal as measured *while a window is
  disappearing*: a script that resolves window references one at a time
  (`repeat`, `item `) raises the verbatim `Invalid index. (-1719)`
  `WindowError`; a single `whose` query answers.
- `test_the_fake_really_does_reject_a_census_that_walks_an_index` — a guard on
  the double itself, so the test below cannot pass against a fake that had
  quietly stopped objecting to anything.
- `test_the_census_survives_a_window_vanishing_mid_census` — drives
  `visible_window_ids()` through it and requires the census back.
- `test_the_census_parses_every_shape_osascript_prints_for_a_list` — the three
  measured shapes above, driven end to end, including the empty one.

Checked, not assumed: with `script_visible_window_ids` swapped back to the old
repeat-loop text, `visible_window_ids()` raises

```
osascript failed (1): execution error: Terminal got an error:
Can't get item 5 of every window. Invalid index. (-1719)
```

against the same fake the new census passes against. The test tells the two
apart.

`tests/test_window_failure_paths.py`:

- `every window whose visible is true` added to `ADDRESSING_ALLOWLIST` (WI-8's
  guard: every occurrence of a window reference in every script must match a
  sanctioned form). The existing
  `test_the_checker_passes_the_three_phrasings_that_are_allowed` already runs
  the census script through `addressing_faults`, so the new form is checked to
  be clean, and the denylist (`front window`, by index, by title, by name, by
  list position) still has nothing to say about it.

## Suite

Run from the repo root (no `-t .` — there is no `tests/__init__.py`):

```
/usr/bin/python3 -m unittest discover -s tests
Ran 749 tests in 12.5s
OK (skipped=2)
```

`main` is at 745. This branch adds 4: one from WI-10's patch and three of mine.
The two skips are the pre-existing `test_launch_smoke` pair, skipped for "no
controlling tty: nobody is watching this screen" — which is why the live check
below was run by hand rather than left to the suite.

## Verified live, against the real Terminal

Four windows opened and reaped, one at a time. Each id was captured at the
moment `do script` returned its tab; nothing was addressed as "the front
window", by title or by index; each child ended by itself and was *confirmed*
ended by `wait_until_idle` before anything closed the window; the failure path
reaps through `close_when_idle`, which refuses a busy tab.

```
BEFORE  all window ids                   [367, 2420, 2440, 2486]
BEFORE  visible (new one-query census)   [367, 2486]
BEFORE  visible (old repeat-loop census) [367, 2486]
OPENED  window id captured at creation   4623
OPEN    visible (new census)             [367, 2486, 4623]
OPEN    visible (old census)             [367, 2486, 4623]
IDLE    child confirmed exited           True
CLOSE   close_window returned            True
CLOSE   census immediately after (new)   [367, 2486]
CLOSE   census immediately after (old)   [367, 2486]
CLOSE   window still visible?            False
RACE 1..3  new census == old census == [367, 2486] each round
AFTER   all window ids                   [367, 2420, 2440, 2486, 4632]
AFTER   visible (new census)             [367, 2486]
AFTER   visible matches before           True
AFTER   window ids that went missing     []
```

The census the race actually threatens — the one taken *immediately* after the
close, with no pause — was taken four times, in both forms, and reconciled
every time. The all-windows census grew by `4632`, which is the
lingering-invisible closed id WI-2 measured and the reason the visible census
exists at all.

**What I did not reproduce: the `-1719` failure itself.** WI-10 observed it;
four rounds here did not trigger it, which is what "race" means. What these
rounds do establish is that the new census agrees with the old one exactly,
both on an undisturbed screen and immediately after a close, so the change is
behaviour-preserving wherever the old form worked at all. The failure mode is
pinned in the suite instead, against a fake that reproduces it deterministically.

## Not done, and why

No mutation sweep — `.claude/agents/developer.md` says that call is yours. If
you think the single-query property is fragile enough to warrant one, say so.

## For a human

Nothing is blocked on it, but the visible census before and after this work was
`[367, 2486]` on this machine and the user's own windows (`367`, `2420`, `2440`,
`2486`) were all still there at the end. If a Terminal window of theirs is
missing, that is worth knowing about and it would be mine.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
