# WI-13 — input translation

**Branch:** `r7/wi-13-input-translation`, cut from `main` at `a2373a9`
**Lane:** B · **Iteration:** M2 · **Depends on:** WI-10
**Suite:** `.venv/bin/python -m pytest -q` from the repository root —
**627 passed, 0 failed, 0 skipped** (534 inherited, 93 new)

`terminal_game/presentation/keys.py`. A keysym goes in, an `Intent` or `None`
comes out, and that is the whole module.

---

## The shape, and why it was forced rather than chosen

`keys.py` **names no toolkit**. That is not a design preference — the
Presentation layer's rule permits only the painting surface to name the
toolkit, and the layer test enforces it. So input translation is necessarily
pure: a key *name* in, a meaning out.

That turns out to be the right shape for a second reason. Lane C measured
that `event_generate` on a withdrawn toplevel delivers nothing, so key
*delivery* cannot be tested headlessly. A translator that took a Tk event
would have dragged this item into the `needs_window` class for no gain.
Taking `event.keysym` sidesteps it entirely.

`Intent.QUIT` was already in the vocabulary from WI-10, put there so this item
would not have to invent a word for quitting. It did not.

## Keysyms are read strictly

`"<Key-Up>"` is a binding name, not a keysym. `"up"` is the wrong case.
Neither means anything here, and there is no leniency for either.

Being lenient would turn a wiring mistake into a silent one — and the silent
wiring mistake worth worrying about is precisely the one where the arrow keys
stop working and nothing says so. The near-miss tests pin this.

**The intended wiring is one binding, not six:**

```python
root.bind("<Key>", lambda event: handle(intent_for(event.keysym)))
```

A shell that does that needs no key list from this module and cannot fall out
of step with it. `TRANSLATED_KEYSYMS` is exported for the tests, not for the
wiring.

---

## The one risk a lookup table cannot catch, and how it is closed

If `"Up"` were misspelled `"UpArrow"`, **every table test in this file would
pass and the finished game would ignore the arrow keys.** Nothing else in the
project checks that these strings are what Tk actually calls those keys,
because the module cannot name Tk.

Measured first, on the withdrawn session root: **Tk validates keysym names at
bind time.** `Up`, `Down`, `Left`, `Right`, `q`, `Q`, `Escape`, `F1` and
`Shift_L` are accepted; `NotARealKeysym` and `Zzzz` raise
`bad event type or keysym`.

So one test registers all six translated keysyms as bindings, and **a
companion test binds a deliberate nonsense name and requires it to raise** —
without which, a Tk that accepted any string would make the check vacuous and
a misspelling would sail straight through it.

No window is involved: the session root is withdrawn before the first turn of
the event loop (S-1's technique, `docs/findings/S-1-tk-headless.md`), and no
event is generated or delivered. It uses the existing `tk_root` fixture
rather than constructing a root, per lane C's finding that a second `Tk()` in
one process can still crash this build.

This does **not** prove that pressing the up arrow produces keysym `"Up"` —
that needs real key delivery, which is `needs_window` and belongs to WI-16 or
WI-17. It proves the vocabulary is real and spelled correctly, which is the
half that would otherwise fail silently. **Named in "what needs a human"
below.**

---

## CTRL-5, tested two ways

**The spread the plan asks for** — letters (including the ones around `q` and
the WASD keys a player might try), digits, modifiers, function keys,
navigation keys, whitespace, punctuation, and the numeric keypad's own arrows,
which are *not* the arrow keys. About fifty of them, each asserted to produce
no intent.

**The near-misses**, which are the shapes a wiring mistake takes rather than
keys a player presses: `"up"`, `"UP"`, `"<Key-Up>"`, `"<Up>"`, `"Key-Up"`,
`"Up "`, `" Up"`, `"Up\n"`, `"qq"`, `"quit"`, `""`. A translator that
lowercased its input, or stripped `<Key-...>`, **would pass the entire spread
and fail these.**

And a test that **the spread contains no real key**, so the sweep cannot be
asserting something false — the same instinct as WI-2's discriminating fixture
and WI-8's self-checking sweep.

**"Nothing is echoed"** is tested as nothing written to stdout or stderr
across every meaningless key, not merely as nothing drawn. A translator that
logged unknown keys would be echoing them somewhere a player could eventually
find them.

---

## What this deliberately does not do

* **It does not bind anything.** Which keys reach the application is the
  window's business (WI-6) and wiring them is WI-14's.
* **It does not act on an intent.** Quitting is CTRL-4's and the session's;
  moving is WI-10's, which already has the resolver.
* **It does not decide what "nothing echoed" means on screen.** That the
  surface has no caret and no text entry is WI-5's, already tested there.
* **It does not define `Intent`.** WI-10 owns that vocabulary.

## Deviations needing a ruling

1. **Two tests touch Tk**, in an item that is otherwise pure. They use the
   existing withdrawn-root fixture and generate no events, so they stay in
   the default suite. The alternative was to leave the spelling of six
   strings unverified, which seemed the worse trade — but it does mean this
   item's tests fail if the toolkit is absent.
2. **`intent_for` returns `Optional[Intent]` rather than an `IGNORE` member.**
   An intent for doing nothing is a thing a caller can forget to check;
   `None` is the one value every caller already handles. This settles a
   question WI-10 deliberately left open.
3. **`ARROW_INTENTS` and `QUIT_KEYSYMS` are public.** Only the tests need
   them; exported so the table is readable from outside rather than
   re-derived.

## Contradictions found

**None.** CTRL-1, CTRL-4 and CTRL-5 are consistent and consistent with the
`Intent` vocabulary WI-10 landed.

## What needs a human

**One, and it is small but real.** Nothing in the default suite can prove that
pressing the up arrow on this machine produces keysym `"Up"` — only that
`"Up"` is a keysym Tk recognises. Key delivery needs a real window.

*What to do:* when WI-17's human-verification pack runs, press each of the
four arrows and both cases of `q` in the game window and confirm the player
moves in the expected direction and that `q` quits. *What to look for:* an
arrow that does nothing, or two arrows that do the same thing — those are the
shapes this gap would take. It is one line in WI-17's script and I have
flagged it rather than assumed it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
