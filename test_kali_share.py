#!/usr/bin/env python3
"""Tests for kali-share. Stdlib only — no live network beyond loopback."""
from __future__ import annotations

import threading
import unittest
import urllib.error
import urllib.request
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory

import kali_share


class TokenTests(unittest.TestCase):
    def test_token_is_nonempty_and_unique(self):
        a, b = kali_share.generate_token(), kali_share.generate_token()
        self.assertTrue(a)
        self.assertNotEqual(a, b)

    def test_extract_bearer(self):
        self.assertEqual(kali_share._extract_bearer("Bearer abc123"), "abc123")
        self.assertEqual(kali_share._extract_bearer("bearer xyz"), "xyz")
        self.assertIsNone(kali_share._extract_bearer("Basic abc"))
        self.assertIsNone(kali_share._extract_bearer(None))
        self.assertIsNone(kali_share._extract_bearer("Bearer"))


class ServerTestBase(unittest.TestCase):
    token: str | None = "s3cret-token"

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "hello.txt").write_text("hello lab\n")

        self.server = kali_share.build_server(str(self.root), "127.0.0.1", 0, self.token)
        self.host, self.port = self.server.server_address
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def get(self, path, token=None):
        url = f"http://{self.host}:{self.port}{path}"
        req = urllib.request.Request(url)
        if token is not None:
            req.add_header("Authorization", f"Bearer {token}")
        return urllib.request.urlopen(req, timeout=5)


class AuthEnforcedTests(ServerTestBase):
    token = "s3cret-token"

    def test_missing_token_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/hello.txt")
        self.assertEqual(ctx.exception.code, HTTPStatus.UNAUTHORIZED)

    def test_wrong_token_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/hello.txt", token="nope")
        self.assertEqual(ctx.exception.code, HTTPStatus.UNAUTHORIZED)

    def test_correct_token_serves_file(self):
        resp = self.get("/hello.txt", token=self.token)
        self.assertEqual(resp.status, HTTPStatus.OK)
        self.assertEqual(resp.read().decode(), "hello lab\n")

    def test_path_traversal_blocked(self):
        # SimpleHTTPRequestHandler normalises '..' — must not escape root.
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/../../etc/passwd", token=self.token)
        self.assertIn(ctx.exception.code, (HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN))

    def test_symlink_escape_blocked(self):
        # A symlink inside the share pointing outside must not leak the target.
        secret = Path(self.tmp.name).parent / "outside_secret.txt"
        secret.write_text("TOP SECRET\n")
        try:
            (self.root / "link.txt").symlink_to(secret)
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self.get("/link.txt", token=self.token)
            self.assertIn(ctx.exception.code,
                          (HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN))
        finally:
            secret.unlink(missing_ok=True)


class OpenShareTests(ServerTestBase):
    token = None  # --no-auth mode

    def test_no_auth_serves_without_token(self):
        resp = self.get("/hello.txt")
        self.assertEqual(resp.status, HTTPStatus.OK)
        self.assertEqual(resp.read().decode(), "hello lab\n")


class BuildServerTests(unittest.TestCase):
    def test_missing_directory_raises(self):
        with self.assertRaises(NotADirectoryError):
            kali_share.build_server("/no/such/dir/xyz", "127.0.0.1", 0, None)


if __name__ == "__main__":
    unittest.main()
