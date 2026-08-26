# nexthop-ise-devops — canonical agent rules

**This file is canonical.** `CLAUDE.md` is only a pointer. Private repo.

Cisco **ISE** export/import tooling (NextHop-era). `ise_export.py` pulls configuration
out of ISE; `ise_import.py` pushes it back.

## Configuration and credentials

`customer_config.py` is **gitignored** — it holds real ISE hostnames and credentials.
Start from `customer_config_example.py`.

Never commit real hostnames or passwords. `include_passwords` defaults to `False` in the
export config; leave it that way unless you have a specific reason and a safe destination
for the output.

## History note (2026-08-26)

Until today this repo's only committed file was `.gitattributes`. All the actual source —
`ise_export.py`, `ise_import.py`, `README.md`, `requirements.txt` — was untracked, sitting
in a cloud-synced folder whose GitHub remote had been deleted. It existed in exactly one
place and a routine "it's already in origin, delete it" would have destroyed it.

That is why the estate rule is what it is: **a working tree belongs in `~/gitsync/<repo>`
with a live remote, and untracked is not the same as backed up.**

## Estate rules

Working tree is `~/gitsync/nexthop-ise-devops`, never a cloud-synced folder.
Cross-project skills:
`git -C ~/gitsync/devwork-kit pull --ff-only && ~/gitsync/devwork-kit/sync-kit.sh`.
