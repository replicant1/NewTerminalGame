# WI-14 — what the anchor query actually returns on this machine

**Measured by:** DEV-C, run 6, on this machine, with `/usr/bin/python3`
(3.9.6, Tk 8.5.9, windowing system `aqua`). Everything below was run, not
reasoned about.

**No window was mapped.** Every run created a Tk root, called `withdraw()`
before anything else, never entered an event loop, and destroyed the root in
a `finally`. Both runs reported `root mapped: False`, `root state:
withdrawn`, and `tkinter._default_root` back to `None` afterwards. `pgrep`
found no leftover process.

Reproduce with:

```
/usr/bin/python3 tools/probe_anchor_query.py
```

---

## 1. The headline, and it is not the one the plan expected

**On this machine, as configured right now, the anchor query returns nothing
and the game opens at the fallback `(120, 120)`. Assumption A2's permission
is not the reason.**

The plan treats A2 — Accessibility permission for seeing another
application's window — as the one thing standing between us and a real
anchor. There is a **second, unrelated obstacle underneath it**, and no
permission grant would clear it. Section 3 below.

---

## 2. Was a permission dialog raised? No — and here is the evidence

| Measured | Run 1 | Run 2 |
| --- | --- | --- |
| Query returned | `None` | `None` |
| Elapsed | **118.6 ms** | **115.0 ms** |
| Dialog seen | none | none |
| `tkinter._default_root` afterwards | `None` | `None` |

**A TCC permission dialog blocks its calling process until a human answers
it.** A query that returns in 115 ms waited for nobody. That is the strongest
evidence available short of a person watching the screen, and it is why the
elapsed time is printed.

**There is no code in this item that could raise a dialog.** The privileged
route is *absent*, not guarded — no `osascript`, no System Events, no window
list, nothing that touches another application. A flag someone could flip
would be a weaker assurance than code that does not exist.

Amendment 2 says *"a stub cannot prove the absence of a permission dialog"*
and requires the real query to be run. It was. What that run establishes is
narrower than it sounds, and worth stating precisely: **it establishes that
*this* query does not prompt.** It says nothing about whether the privileged
query would, because the privileged query was never written. See section 6.

---

## 3. Why the query returned nothing: a second display

The query asks Tk for the mouse pointer and the screen size. Both are things
the toolkit knows about the machine it is on; neither needs any permission.

| Measured | Value |
| --- | --- |
| `winfo_pointerxy()` | **`(-175, -448)`** — stable over 5 consecutive reads |
| `winfo_screenwidth()` × `winfo_screenheight()` | **1512 × 982** |
| `winfo_vrootx, vrooty, vrootwidth, vrootheight` | **`(0, 0, 1512, 982)`** |
| `maxsize()` | **`(5120, 2422)`** |
| `tk windowingsystem` | `aqua` |
| `info patchlevel` | `8.5.9` |

**The pointer is on a display up and to the left of the primary.** Tk reports
it in the whole desktop's coordinates, which on a multi-display Mac are
negative to the left of and above the primary display's origin.

**But `winfo_screenwidth`/`height` and `winfo_vrootwidth`/`height` all
describe the primary display alone.** They agree exactly — 1512 × 982 — and
that is the built-in display, not the desktop. `maxsize()` reports 5120 ×
2422, so Tk *knows* the desktop is bigger; but `maxsize` is a size with no
origin, so it does not give a rectangle anything can be clamped into.

**Nothing Tk 8.5 offers gives the bounds of the display the pointer is on.**

### What follows, and why it is the right answer

An anchor that cannot be bounded cannot be kept inside anything. Placing the
window at pointer + offset would risk it landing half off the edge of that
display — and **WIN-4's entire purpose is that the window "always lands
somewhere visible"**. A fixed position on the primary display is certainly
visible. Visibility is the requirement, so the fallback wins.

So: **a pointer outside the only bounds we have is treated as nothing seen.**

---

## 4. A defect this probe found in the code that was written to run it

This is the reason the plan makes us run these, so it is recorded plainly
rather than quietly fixed.

The first version of the query guarded with:

```python
if pointer_x < 0 or pointer_y < 0:
    # Tk answers -1, -1 when it cannot say where the pointer is.
    return None
```

**That comment is false.** Tk does not answer `-1, -1` to mean "unknown". It
answers with real desktop coordinates that happen to be negative, and here
they were `(-175, -448)` — a genuine pointer position on a real display.

The guess produced the right behaviour on this machine **by luck**. It would
have been wrong on a machine with a second display to the *right* of the
primary, where the pointer reads past 1512 and is exactly as unbounded, and
the window would have been placed off the edge of the primary display with no
clamp able to save it.

It is now `is_on_screen(position, screen)` — written on the measurement,
tested at both edges and both signs, with the numbers in its docstring.

**The unit tests would never have found this.** Every test supplies its own
query, so every test was consistent with the wrong belief. Only the real
toolkit on the real machine had the number.

---

## 5. What the game does, end to end, as configured today

```
pointer (-175, -448) is outside 1512 x 982
  -> the query sees nothing
  -> WindowAnchor falls back
  -> the window opens at (120, 120), the fixed offset WI-3 already used
```

With a 400 × 570 window that occupies 120…520 × 120…690, comfortably inside
the primary display. The offset path — anchor + `(30, 30)`, clamped — is
exercised by 25 unit tests and by nothing on this machine today, because the
pointer happens to be elsewhere.

**If the person moves the pointer onto the built-in display and runs the
probe again, it will return an anchor and the window will open 30 pixels
below and to the right of the pointer.** That is a prediction, not a
measurement, and it is cheap for anyone to check: run the command above.

---

## 6. What this does NOT establish

**Whether the privileged query would raise a dialog.** It was never written
and never run, deliberately. A dialog is modal, a modal sheet blocks
AppleScript, and the next scripted call anyone in the run makes would hang
behind it unwatched. **This is an `ASK` for the user, not something to
establish by trying it.**

**Whether the pointer is the right thing to anchor on.** A2 says *window*.
The pointer is a permission-free stand-in and a deviation from A2's wording,
flagged for a ruling. It is one constant's worth of change either way: hand
`WindowAnchor` the `no_anchor` query and the game goes to `(120, 120)`, which
is A2's literal reading, and every fallback test already passes.

**Whether the window lands somewhere the person finds sensible.** Nobody has
watched it open. That is WI-21's, with A1 and A4.

---

## 7. A contradiction in the plan, found here

**Section 4 asks for a measurement it also forbids taking — and only the
shape of this item hides it.**

- Section 4, amendment 2: *"a stub cannot prove the absence of a permission
  dialog… the real query must be run for real, once, and what happened
  written down."*
- Section 4, and the conductor's standing instruction: *"If you find
  yourself on a code path that could prompt, stop and record it rather than
  trying it to see."*

Both held on this branch **only because the query built here cannot prompt.**
Had the privileged query been built, they would have contradicted each other
outright, and the honest answer would be that **the absence of a permission
dialog is not establishable by any action available to us** — it would take
the user granting or refusing the permission in front of a person who can
see the screen.

WI-21 will meet the same shape when it asks A2 for real. Better written down
now than discovered there.
