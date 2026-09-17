# Coverage audit — all 49 requirement codes

**WI-18.** Developer B, 17 September 2026. Written against **`main` =
`b302b2d`**, suite **919 passed, 0 failed, 0 skipped, 5 deselected**; then
**re-checked against `874e0ca`**, suite **929 passed, 0 failed, 0 skipped, 7
deselected**, after WI-14b and WI-14c landed mid-audit. Both figures were
read from runs of `.venv/bin/python -m pytest -q` at the repository root,
not recalled.

**One row changed between the two and §1.1 records both states**, because an
audit that silently updates itself is a worse document than one that shows
what moved.

Every row below is a judgement about *what is established*, not about what
landed. Two rules govern it:

> **An item landing is not evidence its requirement is met.** This audit
> reports what tests establish, never that work was done.

> **A requirement whose satisfaction depends on an unanswered human item is
> reported NOT MET regardless of the suite**, with the item named. A green
> suite is evidence about code, not about promises.

---

## The verdict, in one table

| | codes | |
|---|---|---|
| **MET** — pinned by tests that assert consequences | **38** | |
| **MET, pending a human confirmation** that is a formality | **3** | WIN-3, STAT-2, STAT-3 |
| **NOT MET — unanswered human item** | **4** | WIN-2, WIN-5, END-5, END-6 |
| **NOT MET — not implemented** | **1** | WIN-4 |
| **PARTLY MET** — structure pinned, appearance never seen | **2** | SCRN-2, SCRN-3 |
| **NOT CLAIMED BY ANYTHING** | **1** | GAME-1 |
| | **49** | |

**Eleven rows need a human, and they need two different things from one.**
Seven need somebody to *look* — nobody has seen this game, though windows
have been opened, measured and closed. Four need somebody to *rule*: WIN-5,
END-5 and END-6 are one unanswered contradiction, and WIN-4 is one
unanswered question about permission. No amount of looking settles those,
and no amount of testing settles any of the eleven.

---

## 1. The findings, in the order they matter

### 1.1 WIN-4 — the fallback now runs; the requirement is still not met

**This row was re-checked and corrected during the audit**, which is worth
saying because the audit itself demanded it.

**At `b302b2d`, when the audit was written**, `grep` for `placement_for`,
`move_to` and `no_anchor` across `terminal_game/` returned exactly one hit —
`move_to`'s own definition. `run_game` was build → start → show → run, with
no placement step. `placement.py` was complete, tested, and **dead**: the
window appeared at Tk's default corner, measured `(5, 38)`.

**At `874e0ca`, WI-14b and WI-14c have wired it.** `Game.place()` asks
`placement_for` and carries the answer to `move_to`, and `run_game` calls it
immediately before `show()`. WI-14c added an `anchor_reader` seam to
`build_game`, so a test can supply a reader and assert both that the game
**asked** and that it **used the answer**.

So the two things that were wrong are now one:

| | at `b302b2d` | at `874e0ca` |
|---|---|---|
| The fallback runs | **no — dead code** | **yes** |
| The player's last window is followed | no | **no** |

**WIN-4 remains NOT MET.** The shipped reader is `NoAnchor`, which follows
nothing, so the window is centred on the main display. That is the honest
fallback, it is what the user is being asked about, and it is not the
requirement. The route is still **plan section 9, item 4, unanswered**.

**Why this row is the audit's own best evidence.** The gap existed for the
length of WI-14, the suite was green throughout, and it was found by reading
the tree rather than by a test. `test_placement.py` tested the arithmetic in
isolation; `test_window_placement.py` tested the join through a window the
test built itself; both passed. **No test can catch an absent call site by
testing the things on either side of it** — and the fix, correctly, was not
another unit test but a call plus a test that the assembled game makes it.

**How no test caught it.** `test_placement.py` tests the arithmetic in
isolation. `test_window_placement.py` tests the join through a window the
test built itself. Both pass. Neither can know whether the assembled game
ever asks — **no test can catch an absent call site by testing the things on
either side of it.** The gap is between the items, not inside either.

### 1.2 GAME-1 — claimed by nothing

> *"The player guides a single character around a walled maze, eating dots
> while a ghost chases them."*

**No file in the project names it** — not a test, not a source module, not a
docstring. It is arguably realised by everything: `tests/test_end_to_end.py`
plays whole games, and if GAME-1 were false the suite would collapse.

But a code no file mentions is a code nobody has claimed, and I would rather
report it than assume it. **Recommendation:** name it in
`test_end_to_end.py`'s class that plays a game to a win and to a loss. That
is a one-line change and it converts an assumption into a claim.

### 1.3 WIN-5, END-5, END-6 — not met, and it is the same unanswered question

These three are **contradiction C-1**, the one the plan calls the one that
matters. WIN-5 says the window closes as soon as the game ends; END-5 says
the last picture stays on screen; END-6 says `q` is the only way to leave a
finished game. **They cannot all be literally true.**

The project proceeds on the architect's reading (assumption P1): outcome
decided → final picture shown → player presses `q` → the window closes
itself.

**That reading is heavily tested — 14, 12 and 8 tests respectively.** It is
also *an assumption the user has not ruled on*, and the tests pin the
assumption rather than the requirement. If the user rules the other way,
three requirements change behaviour and the tests change with them.

By the rule above, all three are **NOT MET**. This is the clearest case in
the audit of a green suite being evidence about code and not about promises:
**34 tests, and the question they answer is one we chose.**

*Blast radius if it flips:* WI-11's Decided state, WI-6's self-close, WI-14's
assembly. The plan calls this cheap to flip while M2 is open and expensive
afterwards; M2 is closed.

### 1.4 WIN-2 — the pixel size is met, the legibility is not

Two claims in one code. The window is 40 × 30 cells at a measured cell of
10 × 19 for Menlo 16, giving 400 × 570, and **30 tests pin that arithmetic
end to end.** P4 is retired *as a measurement*.

*"Large enough to read comfortably"* has **no objective test and cannot
have one.** Nobody has looked. Reported NOT MET on the second half only;
human item 3.

### 1.5 SCRN-2 and SCRN-3 — structure pinned, appearance never seen

**SCRN-2** (*everything the player sees is a character*) is a rule rather
than a fact under candidate 2, and the rule is enforced structurally: the
surface offers no route to draw anything but a glyph and a flat cell colour,
and the assembled game creates no image object. 15 tests. What no test can
say is what appeared on a screen.

**SCRN-3** (*the wall glyphs join up neatly*) is the more interesting one,
and its status improved during the run. All sixteen neighbour combinations
are pinned against the specimen, and lane A established by parsing
`Menlo.ttc` directly that the box-drawing glyphs are **designed to tile** —
they overlap at every joining edge rather than merely meeting, with controls
showing an ordinary `M` stopping well inside its advance.

> That is **evidence at the font level, not at the rendered level.** The
> remaining check is cosmetic rather than structural — a real change in its
> status, and a smaller ask of the human than "does this look right".

### 1.6 START-4 — covered, but labelled at the wrong level

No test function names START-4; only `test_state.py`'s module docstring does.
The behaviour *is* pinned — `test_the_score_starts_at_zero` and
`test_a_new_game_is_undecided_and_not_over` assert exactly it.

**This is a labelling gap, not a coverage gap**, and it is worth separating
from GAME-1, which is a real one.

---

## 2. A finding about the audit itself

**This project cannot be traced from requirements to tests mechanically, and
an audit that tried would be wrong.**

My first scanner attributed a code to a test only when the code appeared in
the test's own body. It reported **WIN-1, WIN-3 and STAT-1 as having no
test**, which is false — those files group tests in classes whose *name or
docstring* carries the code. I fixed it to inherit codes from enclosing
classes. **I nearly published three false gaps**, and a false gap in an audit
is worse than a missing one: it sends somebody to fix what is not broken and
spends the credibility of the rows that are true.

Even corrected, the count is a **labelling** measure and not a coverage one:

| code | tests that *name* it | tests that actually pin it |
|---|---|---|
| START-1 | 1 | ~10, including a 120-seed sweep |
| CTRL-3 | 1 | 3 |
| SCRN-6 | 1 | several, across three files |

**Recommendation:** not a convention change now — the suite is finished and
churning 900 tests for labels would risk more than it buys. But if this
project continues, the cheapest fix is a class-level docstring naming the
code, which four files already do and which the scanner now understands.

---

## 3. The `.outcome` sweep, and why it stays a finding

**The sweep is clean.** Four `.outcome` attribute accesses in the whole
source tree, all four legitimate:

| where | receiver | verdict |
|---|---|---|
| `game.py:128` | `self._session.outcome` | Session's derived property — fine |
| `game.py:201`, `game.py:241` | `self.outcome` | Game's own derived property — fine |
| `session.py:243` | `self.outcome` | Session's own derived property — fine |

**No module reads `GameState.outcome`.** Both known defects are gone:
`Session.__repr__` (found by lane C reading ahead) and the status row (found
by lane A going looking after the first) — **neither found by a test
failing.**

### The guard rots, and the reason is sharp

Tested against the real tree rather than reasoned about:

| candidate rule | exemptions needed |
|---|---|
| **A** — no `.outcome` outside `state.py` and `turn.py` | **4**, in 2 modules |
| **B** — no `.outcome` on a receiver other than `self` | **1** — `self._session.outcome` |

Rule B is nearly clean, and I still recommend against it:

> **Its single exemption is structurally indistinguishable from the defect it
> exists to catch.** Defect one was `self._game.outcome`. The exemption is
> `self._session.outcome`. Same shape, same depth, differing only in the
> *type* of the attribute — which a static scan cannot see.

A guard whose only allowlist entry looks exactly like the thing it forbids is
not a guard; it is the place where the next defect gets added to the
allowlist by someone who thinks it matches the entry already there.

**What would make the guard free.** The allowlist exists because
`GameState.outcome` is *public* and shares its name with the legitimate
derived properties. Were the stored field private — readers calling
`outcome_of(state)`, which is always available — the guard becomes "nothing
outside `state.py` touches `._outcome`", with **zero exemptions**, and a
zero-exemption guard is permanent.

**Measured cost of that change: 26 assertions across 5 test files owned by
three lanes.** That is a cross-lane API change during M3 and it is not an
audit's to make. **Recorded as the concrete thing to do if the guard is ever
wanted.**

---

## 4. Every code

`tests` counts test functions that **name** the code, directly or through
their enclosing class. Read it with section 2 in mind.

| code | status | tests | pinned by |
|---|---|---|---|
| GAME-1 | **NOT CLAIMED** | 0 | nothing names it; realised by `test_end_to_end.py` in practice |
| GAME-2 | MET | 7 | win reached by eating every dot; loss by meeting the ghost |
| GAME-3 | MET | 2 | no lives, levels, timers or pause — `test_session.py`, by omission and assertion |
| WIN-1 | MET | 5 | a real toplevel of its own, owned by this process |
| WIN-2 | **NOT MET** (legibility) | 30 | 40 × 30 at 10 × 19 → 400 × 570 pinned end to end; *"comfortable"* untestable — **human item 3** |
| WIN-3 | MET, pending a look | 4 | title is exactly `Terminal Game` as a string; no titlebar seen — **human item 2** |
| WIN-4 | **NOT MET** | 1 | fallback now wired and running (WI-14b/c); the player's last window is still not followed — §1.1, **human item 4** |
| WIN-5 | **NOT MET** | 14 | tests pin assumption P1, not the requirement — **C-1, human item 1** |
| SCRN-1 | MET | 2 | 30 rows: 0–28 the maze, 29 the status line |
| SCRN-2 | PARTLY | 15 | no route to draw anything but glyph + colour; no image object. Rendering unseen |
| SCRN-3 | PARTLY | 6 | all 16 combinations vs the specimen; Menlo glyphs measured to tile. **Font level, not rendered** |
| SCRN-4 | MET | 5 | dot glyph and colour |
| SCRN-5 | MET | 5 | three-cell actors, their glyphs and colours |
| SCRN-6 | MET | 1 | the status row is cyan (several tests, one names it) |
| SCRN-7 | MET | 13 | composed off-screen, presented once; no caret, no text focus |
| MAZE-1 | MET | 2 | 19 × 29 and **no other shape representable** |
| MAZE-2 | MET | 4 | two kinds only; no corridor wider than one square, proven by parity over the whole lattice |
| MAZE-3 | MET | 14 | border solid by parity; movement cannot leave or wrap |
| MAZE-4 | MET | 3 | same seed same maze, 50 seeds 50 mazes |
| MAZE-5 | MET | 9 | no dead ends, over 200 seeds |
| MAZE-6 | MET | 6 | fully connected, over 200 seeds |
| START-1 | MET | 1 | nearest the centre, **swept over seeds** because the centre is corridor in only ~55% of mazes |
| START-2 | MET | 4 | straight-line furthest, on a maze where the two metrics disagree |
| START-3 | MET | 1 | a dot on every corridor square but the player's; the ghost's keeps its dot |
| START-4 | MET (mislabelled) | 0 | score zero, game undecided — §1.6 |
| START-5 | MET | 4 | under way the moment the window opens |
| CTRL-1 | MET | 2 | four arrows to four directions, through the translator |
| CTRL-2 | MET | 1 | one press, one square, no drift |
| CTRL-3 | MET | 1 | a blocked move returns the identical state |
| CTRL-4 | MET | 10 | `q` and `Q`, at any point |
| CTRL-5 | MET | 6 | ~50 other keys produce no intent; nothing written anywhere |
| GHOST-1 | MET | 4 | one square per tick at `CADENCE_MS`, with the constant's value pinned separately |
| GHOST-2 | MET | 5 | straight on while the corridor allows |
| GHOST-3 | MET | 5 | turns at random; reverses only as a last resort, on a hand-built dead end (**C-3**) |
| GHOST-4 | MET | 2 | the player is not a parameter |
| SCORE-1 | MET | 4 | the dot goes and stays gone |
| SCORE-2 | MET | 7 | one point each |
| SCORE-3 | MET | 3 | an eaten square scores nothing |
| SCORE-4 | MET | 4 | the ghost eats nothing and hides nothing |
| SCORE-5 | MET | 3 | structural: one transition touches the score and only adds |
| END-1 | MET | 11 | both arms, decided by one function |
| END-2 | MET | 6 | the last dot wins |
| END-3 | MET | 10 | **structural**: the win branch is unreachable while player and ghost share a square |
| END-4 | MET | 2 | ghost over player — and verified over 106 real caught games |
| END-5 | **NOT MET** | 12 | tests pin P1 — **C-1, human item 1** |
| END-6 | **NOT MET** | 8 | tests pin P1 — **C-1, human item 1** |
| STAT-1 | MET | 10 | row 29 carries the status and nothing else |
| STAT-2 | MET, pending | 5 | exact string; ruling C-4 takes the specimen as normative — **human item 6** |
| STAT-3 | MET, pending | 8 | both decided forms as exact strings — **human item 6** |

---

## 5. What is pinned only by a human check

Five things, and no test can be written for any of them.

1. **WIN-2** — is the type large enough to read comfortably? *Human item 3.*
2. **WIN-3** — does the titlebar read exactly `Terminal Game`? *Human item 2.*
3. **SCRN-3** — do the wall glyphs look joined **on screen**? Font-level
   evidence now exists; this is the cosmetic remainder.
4. **SCRN-2 / END-4 / SCRN-4 / SCRN-5** — does the picture look like the
   specimen? Composition is pinned exactly; appearance is not.
5. **CTRL-1 physically** — does pressing the up arrow move the player up?
   The keysym names are validated against Tk and, once WI-17 extends the
   existing `needs_window` test, synthetic delivery will be too. **A physical
   keypress remains the honest irreducible.**

All five are in `docs/findings/WI-17-verification-checklist.md` with failure
shapes.

## 6. What WI-20 must do with this

1. **WIN-4 is the row to read twice** (§1.1). Its *wiring* was fixed
   mid-audit by WI-14b/c and the fallback now runs — but the requirement is
   still not met, and a release note that says "placement fixed" would be
   true and misleading in the same sentence.
2. **Run the whole suite including the 4 `needs_window` tests**, once, under
   section 1.5 in full, and report both counts. Those tests are excluded by
   default and **nothing else in the project ever runs them**, so they can
   rot silently; this audit reports their existence and WI-20 is what makes
   them true.
3. **Do not record WIN-5, END-5, END-6 or WIN-2 as met** on the strength of
   the suite. They are the rows where a green number is most misleading.
4. **Carry §5 to the user as five questions**, not as "does it look right".

## 7. Provenance

Every count is from a scan of the tree at `b302b2d`, and the scanners are
described in section 2 including the fault in the first one. The suite figure
was read from a run I made, not recalled. Claims attributed to other lanes
are theirs: the `Menlo.ttc` measurement and the status-row defect are lane
A's, the `Session.__repr__` defect is lane C's. The END-4 and integration
figures are mine, measured earlier this run.

**One caveat on the whole document.** Plan amendment PR #78 has been blocked
on a permission refusal for the length of this run, so the plan on `main` is
older than the rulings this audit was written against. I have audited 49
requirement codes against a specification I can read and a plan I cannot
confirm is current.
