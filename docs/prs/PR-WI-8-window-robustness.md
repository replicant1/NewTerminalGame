# WI-8 — window robustness, the failure-path close, and the launch smoke

**Branch** `wi-8-window-robustness` · **base** `main` (merged at `0c4b93f`,
after WI-5) · **lands no new requirement codes**; it hardens WIN-1..5, which
WI-2 landed.

WI-2 proved the happy path, and the happy path is not what loses somebody's
work. Every failure path in the launcher now ends with the window closed, the
user's other windows untouched, and a message that says what happened.

## Suite

```
/usr/bin/python3 -m unittest discover -s tests
Ran 479 tests in 10.193s
OK (skipped=2)
```

409 on `main` after WI-5, plus **70** from this item. The two skips are WI-2's
and WI-4's live tests, which skip without a controlling tty; no agent has one.

## Live evidence

`./launch-smoke --repeat 2`, run for real against Terminal.app while the user
had other windows open:

```
run 1: PASS in 9.7s      window 4248, title settled in 0.8s, at (-868, 106)
run 2: PASS in 9.4s      window 4251, title settled in 0.4s, at (-868, 106)
launch smoke: 2 run(s), 0 failed
```

**Window census: `[367, 2486]` before and `[367, 2486]` after — both runs.**
The same set WI-2 and WI-4 measured and left unchanged. Six windows were
opened across three attempts; all six were closed by the id captured at
creation, and every one was confirmed gone with `visible`.

---

## The rule that matters most, and its regression test

> **Never touch a window you did not open.**

`tests/test_window_failure_paths.py` walks the supervisor down **fourteen named
paths** and, for every command issued on every one of them, asserts the rule.
It is built as an **allowlist, not a denylist**: every occurrence of the word
`window` in every script must be part of one of exactly four phrases —

| phrase | why it is allowed |
|---|---|
| `first window whose id is <N>` | the addressing idiom; the window was watched into existence and this is its id |
| `first window whose tabs contains newTab` | the *creation* idiom, the only one without an id, because at that instant there is no id yet |
| `repeat with w in windows` | enumerating, in a **read**, to count or to find a reference position; nothing is ever acted on as a result |
| `title displays window size` | not a window reference at all — a tab title component, part of the WIN-3 recipe |

A denylist would let the next new phrasing through. This will not. The same
check also asserts that no command mentions any of the four window ids WI-2
measured as the user's own, that every *write* after the open carries the
captured id, and that the user's windows are all still in the census afterwards
while ours is not.

**The fourteen paths, all swept by it:** a normal game · a game played for a
while · the child crashing on startup · configure failing with the tab ended ·
configure failing with the tab **still busy** · positioning failing · the open
itself failing · the tty reference query failing · both reference queries
failing · **the close itself failing** · a signal · a `KeyboardInterrupt` · the
player closing the window themselves · a window that lingers visible after a
close.

That includes the exception path, which was the specific thing asked for.

`test_the_checker_itself_can_fail` feeds the checker the four phrasings that
have actually destroyed somebody's work or would have — `close front window`,
`close window 1`, `close window "Terminal Game"`, `first window whose name
is …` — and requires it to reject each. A regression test that cannot fail is
worse than no test, and this is the most valuable one in the item.

---

## The timeout, and why

**`CLOSE_GRACE_SECONDS = 10.0`** — how long the supervisor waits, *on the
failure path only*, for the child to exit before giving up, reporting the
window id, and **leaving the window open rather than forcing a close on a busy
tab**.

Ten seconds is **forty times** the larger of WI-2's two measured transitions
(0.25 s from `do script` returning to the tab holding the child's processes;
0.19 s from the child exiting to holding none). The trade is asymmetric and
that is why it is generous: too short leaves a window behind on somebody's
desktop, too long only delays a message, and a window is worse than a message.
Ten is also about the longest a person reads as "it is trying" rather than "it
is stuck".

It is **observed, not asserted about**. `window._sleep` and `window._now` are
module-level indirections so a test can watch the full ten seconds elapse
against a fake clock in a few milliseconds. A test that only compared the
constant to `10.0` would pass on a launcher that never waited.

The other four constants — `STARTUP_GRACE_SECONDS`, `POLL_SECONDS`,
`OSASCRIPT_TIMEOUT_SECONDS`, `INTERRUPTED_EXIT_STATUS` — and the arithmetic
behind each are in **`docs/findings/WI-8-close-grace-timeout.md`**.

---

## What changed in `termgame/window.py`

| Failure | Before | Now |
|---|---|---|
| **The child crashes on startup** | worked, untested | tested; the startup grace lets the empty tab be waited on, then it closes by id |
| **The child hangs** | grace existed | the grace is observed in a test, the id is reported, **the window is left open, and the close is not even attempted** |
| **The supervisor is interrupted** | `finally` caught exceptions only | `SIGINT`, `SIGTERM` and `SIGHUP` are turned into `SupervisorInterrupted` for the duration of the game, so the `finally` actually runs. Handlers are restored on the way out; off the main thread it is a deliberate no-op. Exit status `130`. |
| **The reference query fails / Terminal is not running / launched from something that is not Terminal** | `WindowError` killed `./play` before a window existed | both queries may fail; the fixed fallback is used, **the game still runs**, and the `osascript` text is reported |
| **`osascript` errors at any step** | raised, but the `finally`'s own failure replaced it | the clean-up is one function that **never raises**; the original error survives and the clean-up failure is reported beside it |
| **The player closes the window themselves** | `Can't get window … Invalid index. (-1719)` out of `./play` | the poll, the close and the visibility read all answer `gone`; it is not an error, because a window that is gone is already in the goal state |
| **After a close** | not confirmed | confirmed with **`visible`**, never `exists` — Terminal keeps a stale window object |
| **The screen layout cannot be read** | fell back **silently** | falls back and **says why** (see below) |

Two hooks were added to `supervise` — `on_window_opened` and
`on_window_ready` — so a caller learns about *our* window from the supervisor
itself rather than by enumerating Terminal's windows and guessing which is new.
That is the smoke's only source of the window id.

---

## `./launch-smoke` — the one command

```
./launch-smoke              once
./launch-smoke --repeat 2   twice in a row, which is the gate
```

It censuses the visible windows, runs the whole of `window.supervise` for real
against a temporary repo root, learns the id from `on_window_opened`, waits for
`on_window_ready` before reading the title and geometry back **by that id**,
lets the child exit, confirms the window is gone with `visible`, and censuses
again. Its clean-up is unconditional, waits no longer and no more forcefully
than `./play` itself, and if the tab is still busy it prints `LEFT OPEN` with
the id rather than forcing it.

**The child is a stand-in, deliberately.** A Python script named literally
`Terminal Game`, written into a temp directory, which makes the same first
write the real child makes and then **exits by itself**. The real game blocks
until a person presses `q`; launching something this script cannot end is
exactly what §2.6 rule 4 forbids, because a window whose process will not exit
cannot be closed without Terminal's modal sheet. A person pressing `q` is
**human check H2** and no agent can stand in for it.

`tests/test_launch_smoke_script.py` runs the *entire* smoke with
`run_osascript` replaced — so the suite opens no window — across the happy
path, a wrong title, a wrong tab size, a window that stays visible, a census
that does not reconcile, a supervisor that raises, the reap-on-failure path and
the never-force-a-busy-tab path, plus the same §2.6 allowlist over every
command the smoke causes.

---

## Three defects the live run found that no unit test would have

Recorded in full in **`docs/findings/WI-8-title-settling-race.md`**.

**1. The window title is wrong for the first half-second, and it is not WIN-3's
fault.** The first live run read
`rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519`. `do script`
opens a window running the user's **login shell**, which sources their startup
files before our `exec` line runs, and Terminal's title follows whatever that
shell is doing. WI-2 never saw it because it sampled the title a full second
after creating the window; the `on_window_ready` hook fires about 0.4 s
earlier. The smoke now **polls** the title until it settles and reports how
long it took — 0.4 s to 0.8 s across four runs. **The WIN-3 recipe is
unchanged**; only *when you may believe the answer* changed.

**2. `displays()` fell back to a fake screen, silently.** Between two runs it
returned the conservative `(0, 0, 1440, 900)` fallback on a machine whose three
displays `CGGetActiveDisplayList` reported perfectly a few seconds later. Not
cosmetic: the reference at `(-898, 76)` is then on *no* display, the clamp
moves the game to the main screen, and the window landed at `(0, 106)` instead
of `(-868, 106)` — WIN-4 quietly not holding, with nothing said. Both positions
were observed in consecutive runs from the same reference.

The **behaviour is unchanged** — the game must start either way, and WI-2's
conservative fallback is still right. What changed is that it now says why.
I did **not** add a retry: the cause is not understood, it was not reproducible
on demand, and a retry that papers over an unexplained CoreGraphics failure is
worth less than the line of output that lets the next person recognise it.

**3. Passing checks printed their failure detail.** The first run reported
`ok  the window we opened is no longer visible -- window 4081 is still on the
screen`. That is the line a person reads to decide whether their screen is
safe. Fixed, and pinned by a test.

---

## Deviations needing a ruling

1. **A third top-level executable, `launch-smoke`.** The plan fixes the names
   of `play` and `Terminal Game` and does not say where a runnable smoke goes.
   It could not go in `termgame/` — WI-1's purity guard treats every module
   there that is not `screen`/`loop`/`window` as pure core, so a smoke module
   importing `os`, `sys` and `threading` would fire it. **I did not loosen the
   guard.** If you want it somewhere else, it is one `git mv` and one constant
   in its test.
2. **Two `docs/findings/` documents rather than one.** The brief asks for the
   timeout to be recorded; the title race and the display fallback are separate
   measurements that a later item will want to find by name. Both follow the
   `<ITEM>-<slug>.md` shape.
3. **`window.py` gained `signal`.** Necessary for "the supervisor itself is
   interrupted → the window is still closed": a `finally` does not run for a
   `SIGTERM`. It is the impure shell, so the purity guard is untroubled, and
   handlers are installed only for the duration of the game and then restored.
4. **`displays()` now reports.** Strictly additive, no behaviour change, but it
   is a change to a WI-2 function that the brief did not name.
5. **Two hooks on `supervise`** (`on_window_opened`, `on_window_ready`). Also
   additive. The alternative was for the smoke to enumerate windows and guess
   which one was new, which is the thing this whole item exists to prevent.
6. **One line of `tests/test_window_supervisor.py` changed** — WI-2's
   `window.displays` stub needed the new keyword argument. Nothing else in
   WI-2's tests was touched.

## Contradictions found

None new. WI-2's two corrections to the architecture (§6.3's `busy` recipe, and
`exists` versus `visible`) both held under every failure path tested here, and
both now have regression tests rather than only a findings document.

## Open questions

**A1 is still unanswered and this branch proceeds on the architect's
assumption** — the last picture stays, `q` exits, the window closes then. It is
recorded as an `ASSUME` in the progress log, **not** as a ruling. What depends
on it: the main wait in `supervise`, every failure-path test that asserts the
close happens only after the tab is empty, and human check H2. Flipping it is
one wait removed.

## What needs a human

- **H1 (WIN-4)** and **H2 (WIN-5)** are unchanged and still cannot be answered
  by an agent. H2 in particular: the smoke's child exits by itself, so nothing
  here proves that *pressing `q`* closes the window.
- **H3 (WIN-3)**: the title reads back as exactly `Terminal Game` from
  AppleScript on every run, but only after it settles. Whether the **title bar**
  shows anything else during that first half-second is something only a person
  watching the screen can say. Worth a glance during H3.
- **The transient `displays()` fallback.** If the game ever opens on the wrong
  screen, `./play` will now print a line beginning `could not read the screen
  layout`. That line is the evidence; it would be worth knowing if it recurs.

## Mutation checks

not applicable — not part of this workflow

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01XxWn98HypPEZtVf1TKWf63
