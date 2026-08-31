# Cisco ISE DevOps + Audit Toolkit

Public collection of **read-only** Cisco ISE helpers used for assessments and
config management. Credentials are never committed; script output is customer
data and must stay local.

| Area | What |
|---|---|
| [`audit/`](audit/) | Assessment pull scripts (PowerShell + OpenAPI policy export) |
| Root `ise_export.py` / `ise_import.py` | Broader ERS export/import tooling |

Start with the [audit workflow](audit/README.md) if you are documenting an
existing ISE deployment.

## Security rules (read before cloning into a shared tree)

1. **Do not commit exports.** JSON/CSV from these scripts contains policy names,
   dACLs, identity groups, and sometimes hostnames.
2. **`customer_config.py` is gitignored.** Copy from `customer_config_example.py`.
3. **No real customer hostnames or passwords** in examples, comments, or docs.
4. Run pulls from a directory **outside** the git working tree when possible.

## Prerequisites

- Python 3.7+
- Cisco ISE with ERS and/or OpenAPI enabled
- PowerShell 5.1+ for the `audit/*.ps1` scripts (Windows or PowerShell 7)

```bash
git clone https://github.com/devnexthop/nexthop-ise-devops.git
cd nexthop-ise-devops
pip install -r requirements.txt
cp customer_config_example.py customer_config.py   # edit locally; never commit
```

## Audit scripts (quick start)

```powershell
cd audit
powershell -ExecutionPolicy Bypass -File .\ers_diag.ps1 -Pan ise-pan.example.com
powershell -ExecutionPolicy Bypass -File .\pull_ise_objects.ps1 -Pan ise-pan.example.com
```

```bash
cd audit
export ISE_HOST=ise-pan.example.com ISE_USER=apiadmin
python3 ise_policy_export.py --outdir /tmp/ise_export --insecure
```

Full explanations: [`audit/README.md`](audit/README.md).

## Config export / import

```bash
cp customer_config_example.py customer_config.py
# edit ise_nodes hostnames/credentials locally
python ise_export.py
python ise_import.py /path/to/export.json
```

See comments in `customer_config_example.py` for knobs (what to export, logging,
backup directory).

## Repository layout

```text
nexthop-ise-devops/
├── audit/                      # ISE assessment / documentation pulls
│   ├── README.md               # workflow + per-script docs
│   ├── ers_diag.ps1
│   ├── pull_ise_objects.ps1
│   ├── pull_policy_meta.ps1
│   ├── pull_profiling.ps1
│   ├── fetch_auth_profiles.ps1
│   ├── resolve_profiling_guids.ps1
│   ├── ise_policy_export.py
│   └── examples/
├── ise_export.py               # multi-node ERS export
├── ise_import.py               # multi-node ERS import
├── customer_config_example.py  # template only
├── requirements.txt
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
