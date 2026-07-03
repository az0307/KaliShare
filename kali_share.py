#!/usr/bin/env python3
"""
kali-share — token-authenticated file share for a Kali home lab.

A zero-dependency helper (Python 3 stdlib only) for moving tools, wordlists,
and loot around an *isolated lab network* — e.g. staging a payload onto a
target VM or pulling scan output back to an analysis host.

By default every request must present a bearer token, so the share is not
wide open on the segment. Intended for authorized lab / engagement use only.

Usage:
    kali-share token                       # print a fresh token
    kali-share serve --dir ./share         # serve ./share (auth required)
    kali-share serve --dir ./share --port 8000 --token "$TOK"
    kali-share serve --dir ./share --no-auth   # open share (lab only!)

Client:
    curl -H "Authorization: Bearer $TOK" http://<kali>:8000/tool.sh -O
"""
from __future__ import annotations

import argparse
import hmac
import os
import secrets
import sys
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
TOKEN_ENV = "KALI_SHARE_TOKEN"


def generate_token(nbytes: int = 32) -> str:
    """Return a URL-safe random token suitable for a bearer credential."""
    return secrets.token_urlsafe(nbytes)


def _extract_bearer(header: str | None) -> str | None:
    """Parse a value out of an ``Authorization: Bearer <value>`` header."""
    if not header:
        return None
    parts = header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


class TokenAuthHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that requires a bearer token (unless disabled).

    ``token`` is the expected credential; when ``None`` the share is open.
    Path confinement to the served directory is handled by the base class,
    which normalises ``..`` and refuses to escape the root.
    """

    token: str | None = None

    def _authorized(self) -> bool:
        if self.token is None:
            return True
        supplied = _extract_bearer(self.headers.get("Authorization"))
        if supplied is None:
            return False
        # Constant-time compare to avoid leaking the token via timing.
        return hmac.compare_digest(supplied, self.token)

    def _reject(self) -> None:
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Bearer realm="kali-share"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        if not self._authorized():
            self._reject()
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._authorized():
            self._reject()
            return
        super().do_HEAD()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("[kali-share] %s - %s\n" % (self.address_string(), fmt % args))


def build_server(directory: str, host: str, port: int,
                 token: str | None) -> ThreadingHTTPServer:
    """Construct (but do not start) a ThreadingHTTPServer for ``directory``."""
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"share directory does not exist: {directory}")

    handler_cls = type("BoundTokenAuthHandler", (TokenAuthHandler,), {"token": token})
    handler = partial(handler_cls, directory=directory)
    return ThreadingHTTPServer((host, port), handler)


def cmd_serve(args: argparse.Namespace) -> int:
    if args.no_auth:
        token = None
    else:
        token = args.token or os.environ.get(TOKEN_ENV) or generate_token()

    server = build_server(args.dir, args.host, args.port, token)
    host, port = server.server_address[0], server.server_address[1]

    print(f"[kali-share] serving {os.path.abspath(args.dir)} on http://{host}:{port}")
    if token is None:
        print("[kali-share] WARNING: authentication disabled (--no-auth) — lab use only")
    else:
        print(f"[kali-share] bearer token: {token}")
        print(f'[kali-share] client: curl -H "Authorization: Bearer {token}" '
              f"http://{host}:{port}/<file> -O")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[kali-share] shutting down")
    finally:
        server.server_close()
    return 0


def cmd_token(_args: argparse.Namespace) -> int:
    print(generate_token())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kali-share",
        description="Token-authenticated file share for a Kali home lab.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="serve a directory over HTTP")
    p_serve.add_argument("--dir", default=".", help="directory to share (default: .)")
    p_serve.add_argument("--host", default=DEFAULT_HOST, help=f"bind host (default: {DEFAULT_HOST})")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT,
                         help=f"bind port (default: {DEFAULT_PORT}, 0 = random)")
    p_serve.add_argument("--token", help=f"bearer token (or set ${TOKEN_ENV}); auto-generated if unset")
    p_serve.add_argument("--no-auth", action="store_true",
                         help="disable authentication (isolated lab only)")
    p_serve.set_defaults(func=cmd_serve)

    p_token = sub.add_parser("token", help="generate a random bearer token")
    p_token.set_defaults(func=cmd_token)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
