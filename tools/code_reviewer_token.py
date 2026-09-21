"""Mint a GitHub App installation token for the code reviewer.

The code reviewer approves pull requests that the developers opened, and GitHub
refuses both --approve and --request-changes from an author.  Every other agent
on this project acts as the repository owner, who is also that author, so the
reviewer needs an identity of its own.  It gets one from a GitHub App, and its
approvals are attributed to `<app-slug>[bot]`.

An App authenticates in two steps: a short-lived JWT signed with the App's
private key proves which App you are, and that JWT buys an installation token
which proves which repository you may act on.  The installation token is what
`gh` wants, and **it expires after one hour**, which is why this is a script and
not a value somebody exports once.

Standard library only.  The signing is done by /usr/bin/openssl rather than by
PyJWT or cryptography, so that requirements.txt stays as it is -- see the
comment at the top of that file for why it is kept to pytest alone.

Configuration, from the environment:

    CODE_REVIEWER_APP_ID        the App's numeric id (its settings page)
    CODE_REVIEWER_PRIVATE_KEY   path to the .pem the App issued

Usage:

    eval "$(.venv/bin/python tools/code_reviewer_token.py replicant1/NewTerminalGame)"
    GH_TOKEN="$CODE_REVIEWER_GH_TOKEN" gh pr review 12 --approve --body-file ...

With no argument the repository is taken from the `origin` remote.  On success
it prints three shell assignments and nothing else; on failure it explains what
is wrong on stderr and exits non-zero, printing nothing eval could swallow.

The login is discovered rather than assumed.  GitHub App names are unique across
all of GitHub, so "Code Reviewer" may already be taken and the slug you end up
with decides the bot's login.  Nothing in this project hardcodes it.
"""

from __future__ import annotations

import base64
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"

# A conductor blocked on a hung socket looks exactly like a conductor thinking.
# Ten seconds is far longer than any of these three calls has ever taken.
TIMEOUT_SECONDS = 10


class Failed(Exception):
    """Something the operator has to fix, described in the message."""


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def make_jwt(app_id, key_path):
    """Sign a ten-minute JWT with the App's private key, via openssl."""
    if not os.path.exists(key_path):
        raise Failed("no private key at %s -- set CODE_REVIEWER_PRIVATE_KEY to "
                     "the .pem the GitHub App issued" % key_path)
    now = int(time.time())
    # 60 seconds of backdating absorbs clock skew between here and GitHub;
    # GitHub rejects any JWT whose lifetime exceeds ten minutes.
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iat": now - 60, "exp": now + 540, "iss": str(app_id)}
    signing_input = b".".join([
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ])
    proc = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", key_path],
        input=signing_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise Failed("openssl could not sign with %s: %s"
                     % (key_path, proc.stderr.decode().strip()))
    return (signing_input + b"." + b64url(proc.stdout)).decode()


def call(method, path, token, scheme="Bearer"):
    request = urllib.request.Request(API + path, method=method)
    request.add_header("Authorization", "%s %s" % (scheme, token))
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode().strip()
        raise Failed("%s %s -> %s %s\n%s"
                     % (method, path, error.code, error.reason, detail))
    except urllib.error.URLError as error:
        # DNS, TLS and connection failures arrive here rather than as HTTPError.
        # They must become Failed like everything else: the caller's contract is
        # that a failed mint explains itself and prints nothing to stdout, and a
        # traceback escaping to the shell satisfies neither half of that.
        raise Failed("%s %s -> could not reach GitHub: %s" % (method, path, error.reason))
    except (socket.timeout, TimeoutError) as error:
        raise Failed("%s %s -> timed out after %ss (%s)"
                     % (method, path, TIMEOUT_SECONDS, error))


def repo_from_origin():
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], stderr=subprocess.PIPE
        ).decode().strip()
    except (subprocess.CalledProcessError, OSError):
        raise Failed("no origin remote; name the repository as OWNER/NAME")
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise Failed("cannot read a repository out of origin (%s)" % url)
    return match.group(1)


def main(argv):
    app_id = os.environ.get("CODE_REVIEWER_APP_ID")
    key_path = os.environ.get("CODE_REVIEWER_PRIVATE_KEY")
    if not app_id or not key_path:
        raise Failed("set CODE_REVIEWER_APP_ID and CODE_REVIEWER_PRIVATE_KEY; "
                     "both come from the GitHub App's settings page")

    repo = argv[1] if len(argv) > 1 else repo_from_origin()
    jwt = make_jwt(app_id, key_path)

    # The App's own record carries the slug, which is what the bot's login is
    # built from.  Asking beats assuming: the name may not have been available.
    slug = call("GET", "/app", jwt)["slug"]
    installation = call("GET", "/repos/%s/installation" % repo, jwt)["id"]
    minted = call("POST", "/app/installations/%s/access_tokens" % installation, jwt)

    print('CODE_REVIEWER_GH_TOKEN=%s; export CODE_REVIEWER_GH_TOKEN'
          % minted["token"])
    print("CODE_REVIEWER_LOGIN='%s[bot]'; export CODE_REVIEWER_LOGIN" % slug)
    print('CODE_REVIEWER_TOKEN_EXPIRES=%s; export CODE_REVIEWER_TOKEN_EXPIRES'
          % minted["expires_at"])
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Failed as failure:
        sys.stderr.write("code_reviewer_token: %s\n" % failure)
        sys.exit(1)
