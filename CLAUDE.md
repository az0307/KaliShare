# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KaliShare** is a small, standalone repo containing `kali-share`: a zero-dependency
(Python 3 stdlib only) token-authenticated file share for a Kali Linux home lab. It's
used to move tools, wordlists, and loot around an *isolated lab network* — e.g. staging
a payload onto a target VM or pulling scan output back to an analysis host.

This repo is a public stub/landing repo related to the much larger `kali-backup-system`
toolkit, but it stands entirely on its own: one Python module, one test file, a
Makefile, and CI. There is no build step, no package manager, no external dependencies.

> Authorized lab / engagement use only. `--no-auth` disables the bearer-token check and
> should only be used on a fully isolated segment.

## Commands

```bash
make test     # python3 -m unittest -v test_kali_share
make lint     # python3 -m py_compile kali_share.py test_kali_share.py (syntax check only)
make serve    # serve ./ on :8000 with a random token

# Run a single test
python3 -m unittest -v test_kali_share.AuthEnforcedTests.test_correct_token_serves_file

# CLI usage
python3 kali_share.py token                                   # print a fresh bearer token
python3 kali_share.py serve --dir ./share                     # serve with auth required
python3 kali_share.py serve --dir ./share --port 8000 --token "$KALI_SHARE_TOKEN"
python3 kali_share.py serve --dir ./share --no-auth           # open share, lab-only
```

Requires only Python 3.8+ (standard library — no `pip install` needed). CI
(`.github/workflows/ci.yml`) runs `py_compile` + the unittest suite on Python 3.9 and
3.12 for every push/PR to `main`.

## Architecture

Everything lives in `kali_share.py` (~185 lines), structured as:

- **`TokenAuthHandler`** — subclasses `http.server.SimpleHTTPRequestHandler`.
  - `_authorized()` — constant-time bearer-token check via `hmac.compare_digest`
    (avoids timing attacks); when `token` is `None` the share is open.
  - `translate_path()` — the key security override. The stdlib handler normalises `..`
    but still follows symlinks, so it resolves the requested path with
    `os.path.realpath()` and confines it to `share_root` via `os.path.commonpath()`,
    rejecting anything that would escape the served directory (defeats symlink-based
    escapes, CWE-59). Only `GET`/`HEAD` are handled — read-only, no uploads.
- **`build_server(directory, host, port, token)`** — validates the directory exists,
  computes the canonical `share_root`, and dynamically subclasses `TokenAuthHandler`
  (via `type(...)`) binding `token` and `share_root` as class attributes before handing
  it to a `ThreadingHTTPServer`.
- **`cmd_serve` / `cmd_token`** — argparse subcommand handlers (`serve`, `token`).
  `cmd_serve` resolves the token from `--token` → `$KALI_SHARE_TOKEN` env var →
  auto-generated, unless `--no-auth` is set.
- **`main(argv)`** — thin argparse entry point; `if __name__ == "__main__"` calls it.

`test_kali_share.py` spins up a real `ThreadingHTTPServer` on `127.0.0.1:0` (random
port) in a background thread per test class (`ServerTestBase.setUp`/`tearDown`) and
exercises it over loopback HTTP via `urllib.request` — no mocks, no live network beyond
loopback. Covers: token generation/uniqueness, `Authorization` header parsing, missing/
wrong/correct token responses, path-traversal rejection, and symlink-escape rejection.

## Conventions

- Keep `kali_share.py` dependency-free (stdlib only) — that's the point of the tool.
- Any change to path handling or auth in `TokenAuthHandler` needs a corresponding test
  in `test_kali_share.py` (the existing traversal/symlink tests are the pattern to
  follow).
- `.gitignore` excludes `share/`, `loot/`, `*.iso`, `*.img`, and anything matching
  `*_token*` / `.env` / `*.pem` / `*.key` — never commit lab contents or secrets.
