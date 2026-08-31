# nexthop-ise-devops — canonical agent rules

**This file is canonical.** `CLAUDE.md` is only a pointer.

Public-facing Cisco **ISE** toolkit: read-only audit pulls under `audit/`, plus
`ise_export.py` / `ise_import.py` for config management.

## Configuration and credentials

`customer_config.py` is **gitignored** — it holds real ISE hostnames and credentials.
Start from `customer_config_example.py`.

Never commit real hostnames, passwords, or export JSON/CSV. `.gitignore` blocks
common audit output filenames; still run pulls from a directory outside the repo
when practical.

Before making the repo public (or opening a PR), search the tree for customer
names, FQDNs, and GUIDs from live deployments.

## Estate rules

Working tree is `~/gitsync/nexthop-ise-devops`, never a cloud-synced folder.
Customer engagement artifacts (reports, live exports, switch configs) stay in
OneDrive under the VAR/client tree — not here.

Cross-project skills:
`git -C ~/gitsync/devwork-kit pull --ff-only && ~/gitsync/devwork-kit/sync-kit.sh`.
