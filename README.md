# KaliShare

Kali Linux home lab — bootable USB, AI tools, pentest automation.

## `kali-share` — token-authenticated lab file share

A zero-dependency (Python 3 stdlib only) helper for moving tools, wordlists,
and loot around an **isolated lab network** — e.g. staging a payload onto a
target VM or pulling scan output back to an analysis host.

Every request must present a bearer token by default, so the share is not left
wide open on the segment.

> **Authorized lab / engagement use only.** Do not expose this on untrusted
> networks. `--no-auth` disables the token check and should only be used on a
> fully isolated segment.

### Usage

```bash
# Generate a token
python3 kali_share.py token

# Serve ./share with an auto-generated token (printed on start)
python3 kali_share.py serve --dir ./share

# Serve with a fixed token and port
python3 kali_share.py serve --dir ./share --port 8000 --token "$KALI_SHARE_TOKEN"

# Open share on an isolated lab segment (no auth)
python3 kali_share.py serve --dir ./share --no-auth
```

Fetch a file from a client:

```bash
curl -H "Authorization: Bearer $KALI_SHARE_TOKEN" http://<kali>:8000/tool.sh -O
```

### Options (`serve`)

| Flag | Default | Description |
|------|---------|-------------|
| `--dir` | `.` | Directory to share |
| `--host` | `0.0.0.0` | Bind address |
| `--port` | `8000` | Bind port (`0` = random) |
| `--token` | env `KALI_SHARE_TOKEN`, else random | Bearer token |
| `--no-auth` | off | Disable authentication (isolated lab only) |

### Security notes

- Bearer token compared in constant time (`hmac.compare_digest`).
- Directory traversal (`..`) is normalised and confined to the served root.
- Symlinks are resolved to their real path and rejected if they escape the
  share root (defeats symlink-based escapes, CWE-59).
- Read-only: only `GET` / `HEAD` are handled — no uploads.

## Development

```bash
make test     # run the unit tests
make lint     # py_compile syntax check
make serve    # serve ./ on :8000 with a random token
```

Requires only Python 3.8+ (standard library). CI runs the test suite on every
push and pull request (`.github/workflows/ci.yml`).
