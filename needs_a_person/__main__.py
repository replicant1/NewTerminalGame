"""``python3 -m needs_a_person`` — print the register, and open nothing.

It takes no arguments deliberately. There is nothing to configure about a list
of things a person has to look at, and a flag would only invite somebody to
ask this half of the job to do something it cannot.
"""

from __future__ import annotations

import sys

from needs_a_person import checks

EXIT_OK = 0


def main(argv=None):
    # Read the real command line when called as a module. Without this the
    # argument check below is dead at the one place it matters: `main()` gets
    # argv=None from `__main__`, and a test calling `main(["--run"])` passes
    # while the actual command silently ignores it. Same shape as
    # `launcher/__main__.py`.
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv:
        sys.stderr.write(
            "usage: python3 -m needs_a_person   (no arguments)\n"
            "to run the machine's half instead: python3 -m smoketest\n")
        return 2
    print(checks.render())
    print("None of the above is recorded as verified anywhere, and none of it")
    print("can be. `python3 -m smoketest` is the half a machine can do.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
