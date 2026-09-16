# WI-10 — The rules of the house, enforced

**Announced, because every lane will meet it:** the guard runs as part of the
ordinary suite from now on. Six rules, six separate tests, each failure
naming the file and the line. If one of them stops you doing something you
believe is right, say so rather than working around it — amendment 2 exists
because a rule stated wrongly is worse than no rule.

**Branch:** `r6/wi-10-house-rules`, cut from `main` at `b7dd6ea` and merged
up to `4c82efe` (amendment 4), both merges clean. **Developer:** DEV-C.
**Depends on:** WI-2 and WI-5, both landed.

The plan requires this item to land **last in M1**. WI-6, WI-7, WI-8 and WI-9
have all landed, so it does. Landing it now also means it applies to WI-16,
WI-17, WI-18 and WI-19 as they arrive rather than being retrofitted over
them.

---

## The six rules

Built to **amendment 2's list**, not to the original three.

| # | Rule | Scope inspected |
| --- | --- | --- |
| 1 | No **production code below the Shell** names the windowing toolkit | `terminal_game/`, minus `shell/`. Not the suite. |
| 2 | The **Domain names nothing above it**, reads no clock, reaches for no global random source | `terminal_game/domain/` |
| 3 | **Nothing draws an image** — no image or bitmap objects, no geometric primitives standing in for glyphs | `terminal_game/` and `tools/` |
| 4 | There is **exactly one root package** | the whole repository |
| 5 | The suite **never constructs a Tk interpreter** | the live interpreter |
| 6 | **Nothing that is not a test depends on test code** | `terminal_game/` and `tools/` |

Each returns a `Report(rule, inspected, violations)`. `describe()` renders it
as the failure message, so a red test says which rule, which file and which
line without anybody reading the guard's source.

---

## Three decisions worth reading

### Every check parses the syntax tree. None of them greps.

`terminal_game/shell/grid_surface.py`'s own docstring says, in as many words,
*"Do not add `create_image`, `create_bitmap`, `create_rectangle`,
`create_line`, `create_oval`, `create_polygon` or `create_arc`"*. **A grep
for those names would fail the file whose documentation is the thing keeping
the rule.** Every rule parses with `ast` and looks at calls and imports, so a
name written in prose costs nothing and a name actually invoked is caught.
There is a test for exactly that case.

The same reader also resolves **relative** imports against the file's own
package, so `from ..shell.tk_grid import x` inside the Domain is judged by
the same rule as the absolute spelling, and it walks the whole tree rather
than the top of the file — `tools/walking_skeleton.py`'s import of the
specimen was inside a function, which is precisely where a rule reading only
the first few lines would have missed it.

### Vacuity is baked into the report, not left to the caller

A rule that inspected nothing has not been satisfied; it has been skipped.
So `_report` inserts a violation when `inspected` is empty, and **no rule can
go green over an empty set however it is called** — not only in the one test
that remembers to check. On top of that, `test_each_rule_looked_at_a_file_it_must_have_looked_at`
names a real file each rule must have read, so a path going stale is caught
rather than quietly matching nothing.

### Rule 5 is built to the corrected wording, and says why in its docstring

Amendment 1 said the suite loads neither `tkinter` nor `_tkinter`. That was
measured true on a branch at 04:40 and became false 24 seconds later, when
WI-3 landed the test that checks the real adapter against the seam — a test
which **must** import the toolkit. A guard written to that wording would fail
the one test keeping the adapter honest.

The property that holds is stronger and is what rule 5 guards: **only
`tkinter.Tk()` reaches the window server, and it is never called.**

`test_it_does_not_fire_on_a_module_that_merely_imports_the_toolkit` asserts
both halves at once — `tkinter` **is** in `sys.modules`, and the rule is
**still** clean. That is the corrected wording pinned as a test rather than
as a comment.

**No Tk interpreter is created to check any of this.** The rule is a function
of `tkinter._default_root`; the tests hand it `None` and then a stand-in
object. Creating one is the thing it forbids.

---

## What rule 3 does not cover, stated rather than hidden

`create_window` is **not** in rule 3's forbidden set. On a Tk canvas that
method embeds a widget, but in this project it is the name of the toolkit
seam's own method for making the game's window — `Toolkit.create_window` —
and the window owner calls it on every run. Forbidding it would fail honest
work.

So rule 3 forbids the seven canvas drawing primitives and the two image
classes, and the stronger property — *the only canvas item the surface ever
creates is a `create_text`* — is owned by WI-2's own tests against the
recording double, which assert the recorded item kinds are exactly
`{"text"}`. The limitation is named in the guard's docstring so the next
person does not assume it is covered.

---

## Rule 6 did not hold when this branch started

`tools/walking_skeleton.py:208` imported `tests.specimen` — the exact case
amendment 2 names, and the only violation in the tree.

Amendment 2 had already ruled the fixture must leave `tests/` and made
**where it goes DEV-B's call**. So rather than pick a file name for another
lane or bake a silent exemption into the guard, the question went to DEV-B on
the record, as a comment on PR #45. DEV-B answered by landing it: **PR #50,
"WI-1a: the specimen fixture leaves `tests/`", moved it to
`terminal_game/presentation/specimen.py`.**

All six rules are now clean with nothing exempted, and the guard would have
caught that import the moment it landed.

---

## Proved by a double is not proved — what was exercised against the real thing

**Rule 5 was, and it is the only one that could be.** The live check runs in
the interpreter the suite is running in: every test module is imported by
name, and `tkinter._default_root` is read. That is the real toolkit's real
state, not a double's report of it.

The other five rules read the real repository's real files. There is no
double anywhere in this item — the planted trees are inputs to a checker, not
stand-ins for one.

**No window was opened by this work item.**

---

## Tests

`tests/test_house_rules.py`, 41 tests, in three groups that do three
different jobs.

1. **`ThisRepositoryObeysTheRules`** — one test per rule over the real tree,
   so a breach turns exactly one red.
2. **`ItCannotPassOverAnEmptySet`** — every rule inspected something; a report
   with nothing inspected carries its own violation; each rule looked at a
   named file it must have looked at; rule 3 reaches `tools/` as well as the
   application; rule 1 reaches neither the Shell nor the suite.
3. **One class per rule**, plus `TheRulesAreReportedSeparately` and
   `ReadingTheImports` — each rule shown an input it should reject, and
   inputs it should not.

**On that third group, because it can be misread: this is not proving a test
can fail, and no working code is broken anywhere in this branch.** The
subject under test is a *checker*. Feeding a checker an input it should
reject is how a checker is tested; the inputs are throwaway files written
into a temporary directory that nothing imports. Nothing in `terminal_game/`
or `tools/` is touched, edited or reverted at any point.

The cases that prove the rules are not merely permissive:

- `import random` for the type alone is **not** a Domain breach — the
  generator and the ghost are *handed* a `random.Random` and name that type
  in their signatures. `random.choice(...)` is.
- The forbidden `create_*` names written **in prose** are not a breach.
- A test importing the application is not a rule-6 breach; a script importing
  a test is.
- The Shell naming the toolkit is not a rule-1 breach.

**Suite**, from the repository root:

```
/usr/bin/python3 -m unittest discover -t . -s . -p "test_*.py"
574 passed, 0 failed, 0 skipped
```

533 before this branch, so 41 new.

---

## Deviations

**Additive, and it needs a ruling.** Rule 4 has a second half the plan did not
ask for: as well as counting top-level packages, it reports any first-party
import anywhere in the repository whose top-level name is a different
top-level directory holding Python. The directory count alone can be dodged
by a root spelled as a namespace package, with no `__init__.py`; the import
half cannot. Two witnesses rather than one, for about fifteen lines.

**A note, not a deviation.** DEV-B's PR #50 changed the import line in
`tests/test_wall_glyphs.py`, which is WI-8's file and DEV-C's. It is a
one-line mechanical conform to a ruling already made, it landed green, and I
raise it only so the record is straight — I have no objection and would have
made the same change.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013bXK8DegWhkVhxpUx788Bp
