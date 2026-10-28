# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KaliShare** is a Kali Linux home-lab project: a bootable USB setup with AI tooling and pentest automation for authorized security learning and testing. This repository is currently a **stub** — it contains only a `README.md`. The full toolkit (bootable USB contents, agent definitions, red/blue-team "bibles", automation chains) lives in the related `kali-backup-system` repo.

> Authorized security testing and education only.

## Current State

```text
README.md    # one-line project description
```

There is no code, build system, or tests in this repo yet. Treat it as the public landing/description for the KaliShare home lab.

## Working On This Repo

- Until content lands, changes are documentation edits to `README.md`.
- If populating this repo, mirror the conventions of `kali-backup-system`: scoped directories for `agents/`, `bibles/`, `chains/`, `automation/`, and keep all offensive tooling framed for authorized use.
- Never commit secrets, credentials, keys, or captured engagement data.

## Related Repos

- `kali-backup-system` — the full Kali USB toolkit (agents, bibles, chains, automation; ~900+ files).
- `specter` — production-hardened Kali 2026 overlay (shell tooling + AI wrappers).
- `april-redteam-2026` — the red-team MCP stack and playbook index.
