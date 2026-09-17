"""The audit's own guard: every requirement code is accounted for.

`docs/findings/WI-18-coverage-audit.md` is a statement about a moment. This
is the part of it that can outlive the moment.

It pins two things and deliberately not a third.

**It pins that the specification still has 49 codes**, so that a requirement
added or removed after the audit cannot slip past unaudited. That is the
failure the audit itself cannot see: it is a document, and documents do not
notice when the thing they describe changes.

**It pins that every code appears in the audit**, so the audit cannot fall
out of step with the specification.

**It does not pin that every code has a test.** It cannot: one code —
GAME-1 — genuinely has none, four more are reported NOT MET, and a guard
asserting full coverage would have to carry an allowlist of the gaps. That
allowlist would grow every time somebody wanted their gap excused, which is
the failure mode the audit describes in its own section 3. **A count that
must be looked at beats an allowlist that can be appended to.**
"""

from __future__ import annotations

import os
import re
from typing import List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIFICATION = os.path.join(REPO_ROOT, "docs", "FUNCTIONAL_REQUIREMENTS.md")
AUDIT = os.path.join(REPO_ROOT, "docs", "findings", "WI-18-coverage-audit.md")

#: The specification had this many requirement codes when WI-18 audited it.
#: If this number changes, the audit is out of date — that is the point.
CODES_AUDITED = 49


def codes_in(path: str) -> List[str]:
    """Every requirement code named in a document, in order, without repeats."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    found = []  # type: List[str]
    for code in re.findall(r"\b([A-Z]{3,5}-\d+)\b", text):
        if code not in found:
            found.append(code)
    return found


def specification_codes() -> List[str]:
    """The codes the specification defines, in its own bold-faced form."""
    with open(SPECIFICATION, encoding="utf-8") as handle:
        text = handle.read()
    found = []  # type: List[str]
    for code in re.findall(r"\*\*([A-Z]{3,5}-\d+)\*\*", text):
        if code not in found:
            found.append(code)
    return found


def test_the_specification_still_defines_forty_nine_requirements() -> None:
    """The audit is a statement about 49 codes. If there are more, it is stale.

    This is the guard the audit could not write about itself. A requirement
    added next week would be unaudited and nothing else in the project would
    notice.
    """
    defined = specification_codes()
    assert len(defined) == CODES_AUDITED, (
        "the specification now defines {} requirement codes, not the {} that "
        "docs/findings/WI-18-coverage-audit.md audited. The new or removed "
        "codes are {}. Re-run the audit and update CODES_AUDITED.".format(
            len(defined),
            CODES_AUDITED,
            sorted(set(defined) ^ set(codes_in(AUDIT)) & set(defined)),
        )
    )


def test_every_requirement_code_appears_in_the_audit() -> None:
    """The audit covers the specification, not a subset of it.

    Named individually in the failure message, because "the audit is
    incomplete" is not actionable and "GHOST-2 is missing from it" is.
    """
    audited = set(codes_in(AUDIT))
    missing = [code for code in specification_codes() if code not in audited]
    assert missing == [], (
        "these requirement codes are in the specification but not in "
        "docs/findings/WI-18-coverage-audit.md: {}".format(missing)
    )


def test_the_audit_invents_no_requirements_of_its_own() -> None:
    """The other direction: a typo in a code would silently audit nothing.

    ``SCRN-8`` in the audit would look like coverage of a requirement that
    does not exist, and the test above would not catch it.
    """
    defined = set(specification_codes())
    invented = [
        code
        for code in codes_in(AUDIT)
        if code not in defined and not code.startswith(("WI-", "S-"))
    ]
    assert invented == [], (
        "these codes appear in the audit but are in no requirement: "
        "{}".format(invented)
    )


def test_the_audit_names_every_code_it_reports_as_not_met() -> None:
    """The five gaps are named in the prose, not only in the table.

    A gap that appears only as a row is a gap somebody scrolls past. These
    are the rows the audit says a green suite most misleads about, and each
    has a section of its own.
    """
    with open(AUDIT, encoding="utf-8") as handle:
        text = handle.read()
    for code in ("GAME-1", "WIN-2", "WIN-4", "WIN-5", "END-5", "END-6"):
        assert text.count(code) >= 2, (
            "{} is reported as not met but is named only once in the audit; "
            "it needs prose, not just a table row".format(code)
        )
