#!/usr/bin/python3
"""Run ONE `gh` command as the verifier's GitHub App, without `eval`.

Why this exists: verifiers run in isolated worktrees, where a guard refuses
`eval "$(... code_reviewer_token.py)"` chained with the `gh` call that needs the
token. The user approved this tool, on 2026-09-23 during run 8, as the
sanctioned route. It lives outside the repository on purpose. It always imports
the token tool from the primary checkout's `main` copy, never from the
worktree, so a pull request under review cannot change how its own reviewer
signs.

Usage (the only form a permission rule allows):

    /usr/bin/python3 ~/.config/newterminalgame/verifier_gh.py --login
    /usr/bin/python3 ~/.config/newterminalgame/verifier_gh.py gh <args...>

`--login` prints the bot's login and nothing else. Otherwise the token is
minted in memory, checked to be non-empty, and handed to `gh` only through the
child process's environment. It is never printed, logged or written to disk.
The exit status is gh's own.
"""
import importlib.util
import os
import subprocess
import sys

PRIMARY = "/Users/rodneybailey/CursesProjects/NewTerminalGame"
REPO = "replicant1/NewTerminalGame"


def load_token_tool():
    # Read the token tool from main as git holds it, not from any working tree,
    # so no uncommitted or branch-local edit can reach it.
    source = subprocess.check_output(
        ["git", "-C", PRIMARY, "show", "origin/main:tools/code_reviewer_token.py"])
    spec = importlib.util.spec_from_loader("code_reviewer_token", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, "code_reviewer_token.py(origin/main)", "exec"), module.__dict__)
    return module


def mint(tool):
    app_id = os.environ.get("CODE_REVIEWER_APP_ID")
    key_path = os.environ.get("CODE_REVIEWER_PRIVATE_KEY")
    if not app_id or not key_path:
        raise tool.Failed("CODE_REVIEWER_APP_ID / CODE_REVIEWER_PRIVATE_KEY not set")
    jwt = tool.make_jwt(app_id, key_path)
    slug = tool.call("GET", "/app", jwt)["slug"]
    installation = tool.call("GET", "/repos/%s/installation" % REPO, jwt)["id"]
    token = tool.call("POST", "/app/installations/%s/access_tokens" % installation, jwt)["token"]
    if not token:
        raise tool.Failed("GitHub returned an empty token")
    return token, "%s[bot]" % slug


def main(argv):
    if argv[1:] == ["--login"]:
        tool = load_token_tool()
        print(mint(tool)[1])
        return 0
    if len(argv) < 3 or argv[1] != "gh":
        sys.stderr.write("usage: verifier_gh.py --login | verifier_gh.py gh <args...>\n")
        return 2
    tool = load_token_tool()
    try:
        token, _ = mint(tool)
    except tool.Failed as failure:
        sys.stderr.write("verifier_gh: mint failed: %s\n" % failure)
        return 1
    env = dict(os.environ, GH_TOKEN=token)
    env.pop("GITHUB_TOKEN", None)
    return subprocess.call(["gh"] + argv[2:], env=env)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
