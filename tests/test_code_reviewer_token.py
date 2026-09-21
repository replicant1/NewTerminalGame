"""``tools.code_reviewer_token``, the code reviewer's GitHub App token.

The tool constructs the identity that signs approvals, and the developers'
merge gate is opened by an ``APPROVED`` review from that identity -- so a
defect here either stops every review or, worse, lets the gate be opened by
something that is not the reviewer.

Nothing here touches the network.  The three API calls are exercised against
the real App elsewhere (``docs/findings/AMEND-2-review-permissions.md``); what
is pinned here is everything around them:

* the JWT claims, which GitHub rejects outright if the lifetime is wrong;
* that the signature verifies, checked by ``openssl`` against the public half;
* that a connection failure becomes ``Failed`` rather than a traceback;
* that a failed mint writes **nothing** to stdout, because the call site is
  ``eval "$(...)"`` and a partial line would be eval'd as a success.

The last of those is the one worth having.  It is not visible by reading the
happy path, and the cost of getting it wrong is a token-shaped hole in the
review gate rather than an error anybody sees.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.error

import pytest

from tools import code_reviewer_token as tool


@pytest.fixture(scope="module")
def keypair(tmp_path_factory):
    """A throwaway RSA key, and the public half to verify signatures with."""
    directory = tmp_path_factory.mktemp("appkey")
    private = directory / "private.pem"
    public = directory / "public.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(private), "2048"],
                   check=True, capture_output=True)
    subprocess.run(["openssl", "rsa", "-in", str(private), "-pubout",
                    "-out", str(public)], check=True, capture_output=True)
    return private, public


def _segment(part: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


class TestTheJwt:
    def test_it_has_three_unpadded_segments(self, keypair):
        token = tool.make_jwt("5016462", str(keypair[0]))
        assert token.count(".") == 2
        assert "=" not in token, "base64url padding must be stripped"

    def test_the_header_names_rs256(self, keypair):
        header, _, _ = tool.make_jwt("5016462", str(keypair[0])).split(".")
        assert _segment(header) == {"alg": "RS256", "typ": "JWT"}

    def test_the_lifetime_is_within_githubs_ten_minute_ceiling(self, keypair):
        _, payload, _ = tool.make_jwt("5016462", str(keypair[0])).split(".")
        claims = _segment(payload)
        # GitHub rejects a JWT whose lifetime exceeds ten minutes, and rejects
        # one whose `iat` is in its future -- hence the backdating.
        assert claims["exp"] - claims["iat"] <= 600
        assert claims["exp"] > claims["iat"]

    def test_the_issuer_is_the_app_id_as_a_string(self, keypair):
        _, payload, _ = tool.make_jwt(5016462, str(keypair[0])).split(".")
        assert _segment(payload)["iss"] == "5016462"

    def test_the_signature_verifies_against_the_public_key(self, keypair, tmp_path):
        private, public = keypair
        header, payload, signature = tool.make_jwt("5016462", str(private)).split(".")
        signed = tmp_path / "signed"
        signed.write_bytes(("%s.%s" % (header, payload)).encode())
        raw = tmp_path / "sig.bin"
        raw.write_bytes(base64.urlsafe_b64decode(
            signature + "=" * (-len(signature) % 4)))
        done = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public),
             "-signature", str(raw), str(signed)],
            capture_output=True,
        )
        assert done.returncode == 0, done.stderr.decode()
        assert b"Verified OK" in done.stdout

    def test_a_missing_key_is_named_rather_than_raised_at(self, tmp_path):
        with pytest.raises(tool.Failed) as failure:
            tool.make_jwt("5016462", str(tmp_path / "absent.pem"))
        assert "absent.pem" in str(failure.value)


class TestReadingTheRepositoryFromOrigin:
    @pytest.mark.parametrize("url", [
        "git@github.com:replicant1/NewTerminalGame.git",
        "https://github.com/replicant1/NewTerminalGame.git",
        "https://github.com/replicant1/NewTerminalGame",
        "ssh://git@github.com/replicant1/NewTerminalGame.git",
    ])
    def test_every_spelling_of_the_remote_gives_the_same_answer(self, url, monkeypatch):
        monkeypatch.setattr(tool.subprocess, "check_output",
                            lambda *a, **k: (url + "\n").encode())
        assert tool.repo_from_origin() == "replicant1/NewTerminalGame"

    def test_no_remote_is_explained(self, monkeypatch):
        def absent(*args, **kwargs):
            raise OSError("no git here")
        monkeypatch.setattr(tool.subprocess, "check_output", absent)
        with pytest.raises(tool.Failed) as failure:
            tool.repo_from_origin()
        assert "origin" in str(failure.value)


class TestUnreachableGithub:
    def test_a_connection_failure_becomes_Failed(self, monkeypatch):
        def refuses(*args, **kwargs):
            raise urllib.error.URLError("Name or service not known")
        monkeypatch.setattr(tool.urllib.request, "urlopen", refuses)
        with pytest.raises(tool.Failed) as failure:
            tool.call("GET", "/app", "jwt")
        assert "could not reach GitHub" in str(failure.value)

    def test_a_timeout_becomes_Failed(self, monkeypatch):
        def hangs(*args, **kwargs):
            raise TimeoutError("timed out")
        monkeypatch.setattr(tool.urllib.request, "urlopen", hangs)
        with pytest.raises(tool.Failed) as failure:
            tool.call("GET", "/app", "jwt")
        assert "timed out" in str(failure.value)

    def test_the_calls_carry_a_timeout_at_all(self, monkeypatch):
        seen = {}

        def record(request, **kwargs):
            seen.update(kwargs)
            raise urllib.error.URLError("stop here")
        monkeypatch.setattr(tool.urllib.request, "urlopen", record)
        with pytest.raises(tool.Failed):
            tool.call("GET", "/app", "jwt")
        assert seen.get("timeout") == tool.TIMEOUT_SECONDS


class TestAFailedMintPrintsNothing:
    """The call site is ``eval "$(...)"``.  Half a line would be eval'd."""

    @pytest.mark.parametrize("environment", [
        {},
        {"CODE_REVIEWER_APP_ID": "5016462"},
        {"CODE_REVIEWER_PRIVATE_KEY": "/nowhere.pem"},
    ])
    def test_missing_configuration_is_refused_before_anything_is_printed(
            self, environment, monkeypatch, capsys):
        for name in ("CODE_REVIEWER_APP_ID", "CODE_REVIEWER_PRIVATE_KEY"):
            monkeypatch.delenv(name, raising=False)
        for name, value in environment.items():
            monkeypatch.setenv(name, value)
        with pytest.raises(tool.Failed):
            tool.main(["code_reviewer_token.py"])
        assert capsys.readouterr().out == ""

    def test_the_command_line_exits_non_zero_and_stays_silent(self, monkeypatch):
        done = subprocess.run(
            [sys.executable, "tools/code_reviewer_token.py"],
            capture_output=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        assert done.returncode != 0
        assert done.stdout == b""
        assert b"CODE_REVIEWER_APP_ID" in done.stderr
