# ISE Audit Scripts

Read-only collection helpers for Cisco ISE assessments. Credentials are prompted
or taken from environment variables — nothing is hard-coded.

**Never commit script output.** Exports contain customer policy, dACLs, and
identity-group names.

## Prerequisites

| Requirement | Notes |
|---|---|
| PowerShell 5.1+ (Windows) or PowerShell 7+ | Native `Invoke-WebRequest` |
| Python 3.7+ + `requests` | For `ise_policy_export.py` |
| ISE ERS (Read) and/or OpenAPI enabled | Admin → System → Settings → API Settings |
| Account with API RBAC | ERS Admin or Super Admin |

Scripts accept self-signed PAN certificates (lab-friendly). Prefer proper TLS
validation in production when you can.

## Recommended order

```text
1. ers_diag.ps1              # which port / URL shape works?
2. ise_policy_export.py      # policy sets (OpenAPI) → CSV + JSON
3. pull_ise_objects.ps1      # dACLs, endpoint groups, ID sequences, NDGs
4. fetch_auth_profiles.ps1   # full authorization-profile bodies
5. pull_policy_meta.ps1      # condition libraries + dictionaries
6. pull_profiling.ps1        # profiler name↔id index + logical profiles
7. resolve_profiling_guids.ps1  # map EndPointPolicy GUIDs from your CSV
```

Run each script from a **working directory outside this repo** (or a gitignored
`workdir/`) so JSON lands somewhere you will not accidentally `git add`.

## Scripts

### `ers_diag.ps1`

Connectivity smoke test. Hits ERS on 443 and 9060, with and without `size=`
paging. Use this when collections mysteriously 404 — some ISE builds reject
`?size=` on certain resources.

```powershell
powershell -ExecutionPolicy Bypass -File .\ers_diag.ps1 -Pan ise-pan.example.com
```

### `pull_ise_objects.ps1`

Bulk ERS pull for objects needed in a policy cross-reference:

- `dacls/*.json` — downloadable ACL bodies
- `endpointgroups.json`
- `idstoresequences.json`
- `networkdevicegroups.json`

Uses `?page=N` without `size=` (the pattern that survived real ISE 3.x audits).

```powershell
powershell -ExecutionPolicy Bypass -File .\pull_ise_objects.ps1 -Pan ise-pan.example.com
```

### `fetch_auth_profiles.ps1`

Lists every authorization profile, then downloads each body to `profiles/`.
Profile **content** is ERS-only (`/ers/config/authorizationprofile/{id}`), not
OpenAPI.

```powershell
powershell -ExecutionPolicy Bypass -File .\fetch_auth_profiles.ps1 -Pan ise-pan.example.com
```

### `pull_policy_meta.ps1`

OpenAPI condition libraries + dictionaries, then probes profiling endpoints and
prints HTTP status only (so you know what this build supports).

```powershell
powershell -ExecutionPolicy Bypass -File .\pull_policy_meta.ps1 -Pan ise-pan.example.com
```

### `pull_profiling.ps1`

Profiler policy name↔id index (`profilerprofiles_index.json`) and logical
profiles when ERS exposes them.

```powershell
powershell -ExecutionPolicy Bypass -File .\pull_profiling.ps1 -Pan ise-pan.example.com
```

### `resolve_profiling_guids.ps1`

AuthZ rules often store `EndPointPolicy` as GUIDs. Feed a CSV of IDs (column
`id`) and get `profiling_guid_names.json`.

```powershell
# copy examples/profiling_guids_sample.csv → profiling_guids.csv and fill real IDs
powershell -ExecutionPolicy Bypass -File .\resolve_profiling_guids.ps1 `
  -Pan ise-pan.example.com -GuidCsv .\profiling_guids.csv
```

### `ise_policy_export.py`

OpenAPI export of network-access and device-admin policy sets, flattened to CSV
with resolved profile/condition names.

```bash
export ISE_HOST=ise-pan.example.com
export ISE_USER=apiadmin
export ISE_PASS='...'
python3 ise_policy_export.py --outdir ./ise_export --insecure
```

## What is intentionally not here

Customer-specific report builders, branded HTML/XLSX templates, switch running
configs, and live JSON exports stay in the engagement folder (OneDrive), not in
this repository.
