# WI-14b — the acceptance run

**Branch:** `wi-14b-acceptance-run`, cut from `main` at `84e09be`
**Lane:** DEV-B, iteration M3 — **the last item in the plan**
**Mode:** local — this file stands in for the pull request. Nothing was pushed; no `gh` was used; the branch is not merged.
**Suite:** `python3 -m unittest discover` from the repository root — **737 passed, 0 failed, 0 skipped** (9.7 s). `main` was 732.
**Windows opened: 7. All 7 closed. Census returned to its starting value every time. No modal sheet.**

---

## This item cannot finish without the user, and that is not a failure of it

What an agent could take to the end has been taken to the end. What is left needs a person in front of
the screen. **The deliverable is the list of what they must do**, and it is in
`docs/findings/WI-14b-what-the-machine-could-not-settle.md` and in
`python3 -m acceptance --list`.

## What this branch changes in the code

One thing: `tests/test_layering.py` gains **`AcceptancePackTest`**, 5 tests, making the WI-14a ruling
into a mechanism. The pack may import the launcher, must import nothing from the game, and nothing
that ships may import the pack — enumerated with `ast` and each import judged, like the launcher half,
rather than scanned for names.

**Added rather than left as a ruling in prose**, because a new category with rules nobody enforces is a
guard waiting to have never been exercised — which is a mistake this project has now made twice, once
by me and once by DEV-A.

## What was settled on the real thing

**The whole join, against the real wired game** — the pack's first run with a real game to exercise,
since WI-14a wrote it against M0's skeleton:

| | |
| --- | --- |
| window created / configured / game running | +0.12 s / +0.32 s / +0.39 s |
| picture drawn | +0.65 s |
| `q` sent → **game gone** | +0.88 s → **+0.96 s (0.08 s)** |
| window closed, `visible=false` | +1.20 s |
| visible windows before / after | **1 / 1** |

**The picture read back from the live tab is the specification's** — 30 rows, widest 37, three margin
columns; joined-up walls, a dot on every corridor square, the player near the middle, the ghost across
the maze, two lone blocks, and ` score 0    arrows, q quits`.

**And it closes an open thread from WI-5a.** A `╬` crossing appears in the live picture. That is the
one entry in the glyph table with **no worked example behind it** — the specification's picture never
contains a four-way crossing, and the entry was inferred from SCRN-3's word *"crossings"*. It is now
observed in a real maze on a real screen.

**GHOST-1's rate, measured live rather than against an injected clock:** 78 samples over 5.97 s, 43
distinct ghost positions, **7.0 moves per second**. In the same run the player occupied exactly one
position for six seconds with nobody pressing anything.

**The game is unbounded, as §11.15 says:** still running at +6.0 s unattended, and ended by the pack's
`q` in 0.08 s. My WI-13 timing measurement — session length against a hold — is superseded, because the
hold it measured against no longer exists.

## The arrow keys: three attempts, no answer, and two false findings caught

**This is the gap nobody has closed, and I did not close it.** The sequence is in the finding in full;
the short version, because the shape matters more than the result:

1. Six arrows via `do script`: **0 of 6 moved the player.** Not reported — I had not checked which
   directions were walls, and an arrow into a wall correctly changes nothing.
2. A hypothesis with a named mechanism — ncurses' 1000 ms `ESCDELAY` against the loop's 143 ms
   timeout. Both arms measured: **as shipped 2 of 6, with `ESCDELAY=25` 1 of 6.** Hypothesis wrong,
   and attempt 1's result dead with it.
3. Press only into a way the picture says is open, watch continuously: **10 presses, 0 moves**, while
   `q` on the same channel worked immediately.
4. A pseudo-terminal, no window, exact arrow bytes. The player did not move — **and then the probe had
   to `SIGTERM` the child, meaning `q` had not worked either.** Re-run with `q` as the control first:
   input is not reaching the game through that harness at all. **The conclusion was my instrument, not
   the game, and it is withdrawn.**

**I cannot distinguish "the game drops arrow keys" from "`do script` does not reliably deliver an
escape sequence."** Nothing above is evidence of a defect and nothing above is evidence against one.

This makes the human check stronger, not weaker: three automated attempts, two of which produced
confident wrong answers before being caught.

## What must not be recorded as met, and is not

- **Every colour in this game is unverified.** `contents of selected tab` returns text. There is no
  path by which any automated check here could read a cell's colour. SCRN-3, SCRN-4, SCRN-5 and
  SCRN-6 rest entirely on a person looking.
- **Nobody has pressed a key on a real keyboard.** Every session that has ever ended on this project
  ended on a timer or a scripted `q`.
- **WIN-3 is NOT MET.** The bar reads `rodneybailey — Terminal Game — Python -m
  terminalgame.game_main`; two components are outside Terminal's dictionary and governed by the
  player's profile, which A3 forbids changing.
- **Q2 was granted before this project began.** The first-run behaviour without the Automation
  permission is completely untested and no agent can test it.
- **Q1 and Q3** remain assumptions.
- **SCRN-7** (flicker, cursor), **WIN-2**'s legibility and **WIN-4**'s visible placement are
  unsettled.
- **GHOST-1's confinement** — 8 games in 500 — is a human judgement about feel.

## §11.11 — two lines, not one

| | mechanism | purpose clause |
| --- | --- | --- |
| WIN-2 | 357 × 558 for 40 × 30 at Menlo 14 — **measured, met** | *"legible"* — unsettled |
| WIN-3 | custom title set on the captured window — **met** | *"reads Terminal Game"* — **NOT MET** |
| START-2 | greatest straight-line distance — **tested** | *"well apart"* — the metric is an assumption |
| GHOST-1 | **7.0 moves/s measured live**, player-independent | *"roams the maze"* — 1.6 % confined |

## Deviations, for a ruling

**1. I did not add the maze sweep to this item**, per §11.17 — WI-4's 20 000-seed sweep already
discharges it, in the unit suite where it belongs. Recording that I read the ruling and followed it.

**2. The probes live in the scratchpad, not the repository.** They are measurements, not machinery:
the machinery is `acceptance/`, and each probe existed to answer one question and is described in the
finding. If the technical lead would rather the arrow-key probe were kept so somebody can re-run it
when the question is reopened, say so and I will add it to the pack — but it currently proves nothing,
and a probe that proves nothing is a trap in a repository.

**3. The five stale root executables were not read, not used and not resurrected.**

## Contradictions found

**None new.** The arrow-key result is an *open question*, not a contradiction: it may yet be a defect
in the game, a limitation of `do script`, or both, and the evidence does not choose.

## What needs a human

**All of it is in `python3 -m acceptance --list`** — 12 checks, 21 requirement codes, none recorded as
verified. The report to the conductor carries the ordered version, with what a wrong answer looks like.

## Windows

**Opened 7, closed 7** — one pack run, one ghost-rate run, one arrow run, two `ESCDELAY` arms, one
open-way run, one decisive run. Every id captured at creation and only that id ever named; every close
confirmed with `visible`; every reap in a `finally`. **Census returned to 1 every time and no modal
sheet was raised.** The two pseudo-terminal probes opened **no window at all**.

## Commits

| | |
| --- | --- |
| `38926b1` | WI-14b: the acceptance-pack boundary, guarded rather than ruled |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
