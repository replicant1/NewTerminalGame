# WI-20b — the specification sweep, second landing

**Branch** `r6/wi-20b-spec-sweep-final`, based on `main` at `06da112`, with
`origin/main` merged in at `03d0913` once **WI-21 (#66)** and **WI-22a (#67)**
had landed.
**Suite** `/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"` →
**815 passed, 0 failed, 0 skipped** (796 on `main` after those two, +19 here).

---

## One file, written twice

`docs/TRACEABILITY.md` is the file WI-20a created and this item **completes in
place**. There is one traceability document, not two. The two things WI-20a's
own section 14 said the second landing must delete are deleted: the *"first of
two landings"* notice at the top, and section 14 itself.

**No row is waiting on a work item any more.** Every work item of the run has
landed, so *"awaiting WI-18"* has nowhere left to point.

## What actually changed, row by row

**GAME-1 and START-5 are closed.** Both halves WI-20a left open — the game
assembled behind a window and run from one command, and START-5's *"the moment
the **window** opens"* — are pinned in `tests/test_game.py` and were then
observed on a real screen in `docs/findings/WI-18-the-game-on-screen.md`.

**Every other row was re-checked against the wired game rather than against
the parts**, which is what a second landing is for. **Nothing was found that is
true of a component and false of the assembly.** That is a result rather than
an absence of effort, and it is recorded as finding 3.

**CTRL-5 no longer carries a tick.** It is *honoured for letters and not for
modified arrows*, under A11. The reason is one line long and structural:

```python
class KeyPress(NamedTuple):
    keysym: str
    char: str = ""
```

There is no modifier state on the value that crosses the toolkit seam, so
control-Up cannot be told from Up and moves the player. A modified **letter** is
rejected correctly, because a letter's character changes under a modifier and an
arrow's does not. Ruled deliberate in amendment 9; the row says so, and there is
a test that stops anyone ticking it later.

**New section 3a — two Shell functions have no automated test at all.**
`tk_grid.measure_metrics` and `tk_grid.create_surface` both construct a toolkit
interpreter, which house rule 5 forbids the suite. They are *covered by
observation, not by test* in exactly the sense amendment 9 names: the
observations are recorded in five findings and in the project window ledger
(**39 windows opened, 39 reaped, no modal sheet ever raised**) and cited from
the section. **No row anywhere claims test coverage for them**, and there is a
test that keeps it that way.

**WIN-4 is recorded as satisfied by its fallback for a known cause, not as a
gap.** The window opens at `(120, 120)` for a reason no Accessibility grant
would change — Tk reports the pointer in whole-desktop coordinates while
describing only the primary display, so the anchor cannot be bounded (C-7).
A row citing only the permission would imply a fix that does not exist.

**SCRN-3 is not closed, deliberately.** Advance widths are measured uniform with
a control, which settles the spacing and nothing else. Five developers declined
to convert that into an answer about whether the strokes meet; this landing is
the sixth. The row also carries the sting: the specimen picture contains **no
crossing glyph at all**, so the question must be asked against WI-16's joinery
view and not against a game screen.

**A9 is honoured.** A whole game is worth **259–271** points, so no row claims
274 as an achieved score. It is a formatting exemplar and nothing else.

## One correction I was asked to check rather than take on trust, and it did not hold

The conductor relayed that WI-21's second window *"reached phase `ended` with
nothing pressed at all"*, offered as a correction to *"nobody has played a whole
game"*, and told me to check WI-21's findings rather than treat that sentence as
final. **I checked, and the original row stands.**

`ended` is the **session's phase** — the harness's own scheduled `quit` shutting
the session down — and **not a game outcome.** WI-21's §9 records zero dots
eaten on each of its six windows, and its §8 says in as many words: *"A whole
game played to an ending. **Nobody has ever played one.**"*

So the sweep keeps the row and now states the distinction explicitly, because
it is exactly the kind of thing that gets rounded up on a second reading:
**a phase of `ended` and an outcome of `CLEARED` or `CAUGHT` are different
things, and only the second is missing.** Thirty-nine real windows, and not one
of them reached an ending.

## Two corrections upward in honesty, not in coverage

These change the count and no code.

| Row | Was | Is | Why |
| --- | --- | --- | --- |
| **END-3** | Pinned | Pinned, **caveated — A8** | WI-20a named A8 in the row's prose but did not count the row as caveated. A8 is a live question and it changes the last number the player ever sees |
| **SCRN-5** | Pinned | **Pinned in part** | `docs/findings/WI-16-the-look.md` §4 declared the *"distinguishable to a person"* half open and the first landing did not carry it. The five colours being five different **values** is tested; whether a person can tell two hues apart is not |

## The count

**35** pinned outright, **9** caveated by a named assumption, **1** pinned as
formatting only, **3** pinned in part with a half needing a human, **1**
honoured in part with a named gap. **35 + 9 + 1 + 3 + 1 = 49**, with no row
counted twice and none awaiting a work item.

**Rows additionally observed on a real screen: 17**, against 4 at the first
landing — WI-17, WI-18 and WI-21 put the assembled game in front of real Tk.

## The tests

19 new tests in `tests/test_spec_sweep.py`, taking it from 21 to 40. The
existing four checks are about what **exists**; these five are about what the
finished document **claims**, because a completed traceability document fails
differently from an incomplete one — an incomplete one is merely unhelpful, and
a finished one that rounds an open question up to a tick is worse than none.

| Class | What goes red |
| --- | --- |
| `TheSweepIsFinished` | the notice comes back, a row goes outstanding again, or the document stops saying it is complete |
| `CtrlFiveIsNotTicked` | CTRL-5 stops naming A11, stops saying modified arrows are not covered, or acquires a tick |
| `NoRowClaimsTestCoverageForWhatOnlyAPersonHasSeen` | either untestable function is presented as pinned or offered a test citation, or the category phrase disappears |
| `EveryOpenQuestionIsStillRecordedAsOpen` | any of A1, A2 revised, A3, A4, A7, A8, A9, A10, A11, C-7, the tie-break or the unplayed whole game stops being named in section 13 |
| `EveryMeasurementThisRunTookIsCited` | any of the thirteen findings stops being cited — the sweep is the only place left pointing at them once the spikes are gone |

Each asserts a floor before it asserts anything else, so none can pass over an
empty set. Listing the thirteen findings explicitly rather than reading the
directory means a finding added by a later item does not turn this red for the
wrong reason.

**The guard caught its own author, twice, and both were real.** First I
backticked `docs/findings/WI-21-the-five-questions.md` before WI-21 had landed
and `EveryDocumentTheSweepCitesExists` went red — a backtick is a claim that a
file exists. Then, on merging `origin/main`, `EveryTestTheSweepNamesExists`
caught that **WI-22a had renamed**
`tests/test_game.py::ThePictureTheSessionIsComposedWithTest::test_row_29_is_exactly_what_the_status_line_says_it_is`
to `::test_the_session_is_composed_with_presentations_picture_function`. One
citation line, and the new test is a *better* one for the claim SCRN-1 was
making. **Neither would have been noticed by eye.**

## Proved against the real toolkit

**Nothing.** This item opened no window, needed none, and asked for none, and
never held the screen gate. Everything it asserts about a real screen is
**cited** from the thirteen findings rather than re-derived, which is what the
plan asks of it. The project ledger is unchanged by this lane and closes the
run at **39 windows opened, 39 reaped, no modal sheet ever raised**. `/usr/bin/python3 -m
terminal_game` was **not** run: section 4 rule 5 makes the finished game the one
artefact no agent may start.

## Deviations needing a ruling

1. **SCRN-5 is carried as an open question and WI-20a did not carry it.**
   Additive. `docs/findings/WI-16-the-look.md` §4 states it plainly and dropping
   it would lose information; if the lead considers it out of scope for the
   sweep, it is one row in section 13 and one status cell.
2. **END-3 recounted as caveated.** Changes the published count from 8 caveated
   to 9. No code, no test, no claim about behaviour.
3. **The WI-21 findings document is cited as
   `WI-21-the-five-questions.md`, not the plan's `WI-21-human-answers.md`.**
   WI-21 renamed it and flagged the rename for a ruling; I asked WI-21 directly
   on PR #66 rather than guessing and it confirmed that is the one and only
   file it would add. One line to flip in each place if the lead prefers the
   planned name.
4. **Section 13 gained two columns** — *what a person does* and *what the answer
   costs* — where WI-20a had one. An open question a reader cannot act on is a
   complaint rather than a finding, and there is a test for the column.
5. **A category was added to the column legend**: *covered by observation, not
   by test*. Amendment 9 names it; WI-20a predates it.

## Contradictions found in the plan or the architecture

**None new.** C-1 through C-7 are all recorded and all still true as written;
this item re-derived none of them and confirmed the four that bear on rows
(C-1 as 37 + 3, C-2 under A3, C-3/C-4 under A7, C-7 under WIN-4).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
