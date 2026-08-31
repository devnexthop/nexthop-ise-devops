#!/usr/bin/env python3
"""
ise_policy_export.py — Export ISE Policy Sets (authentication + authorization)
via the ISE OpenAPI (/api/v1/policy/...). Read-only; GETs only.

Covers network-access (RADIUS: wired/wireless/VPN) and device-admin (TACACS+).
Resolves authorization-profile and condition references to human-readable names.

Prereqs on ISE:
  - Administration > System > Settings > API Settings > OpenAPI = ENABLED
  - Account with ERS Admin / Super Admin RBAC
  - Reach PAN on TCP 443

Usage:
  export ISE_HOST=ise-pan.example.com
  export ISE_USER=apiadmin
  export ISE_PASS='...'          # not stored; read at runtime
  python3 ise_policy_export.py --outdir ./ise_export [--insecure]

Outputs (in --outdir):
  network-access_policysets.json   device-admin_policysets.json
  network-access_policy.csv        device-admin_policy.csv
  authorization_profiles.json      conditions.json

Do not commit export output — it is customer policy data.

Tested shape against ISE 3.3 OpenAPI. Requires: requests
"""
from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()  # noqa: E402


def make_session(insecure: bool) -> requests.Session:
    s = requests.Session()
    user = os.environ.get("ISE_USER") or input("ISE_USER: ")
    pw = os.environ.get("ISE_PASS") or getpass.getpass("ISE_PASS: ")
    s.auth = HTTPBasicAuth(user, pw)
    s.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    s.verify = not insecure
    return s


def get(s: requests.Session, base: str, path: str):
    url = f"{base}{path}"
    r = s.get(url, timeout=30)
    if r.status_code == 401:
        sys.exit("401 Unauthorized — check creds and that the account has API RBAC.")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def unwrap(payload):
    """OpenAPI returns either a bare list or {'response': [...]}. Normalize to list."""
    if payload is None:
        return []
    if isinstance(payload, dict) and "response" in payload:
        return payload["response"]
    if isinstance(payload, list):
        return payload
    return [payload]


def build_lookup(items, id_key="id", name_key="name"):
    out = {}
    for it in items:
        if isinstance(it, dict) and id_key in it:
            out[it[id_key]] = it.get(name_key, it[id_key])
    return out


def _cond_name(cond, cond_lookup):
    if not cond:
        return ""
    if isinstance(cond, dict):
        if cond.get("conditionType") == "ConditionReference":
            cid = cond.get("id")
            return cond_lookup.get(cid, cond.get("name", cid))
        return cond.get("name") or cond.get("conditionType", "inline-condition")
    return str(cond)


def export_domain(s, base, domain, outdir, prof_lookup, cond_lookup):
    root = f"/api/v1/policy/{domain}"
    sets = unwrap(get(s, base, f"{root}/policy-set"))
    full = []
    rows = []
    for ps in sets:
        psid = ps.get("id")
        psname = ps.get("name", psid)
        authn = unwrap(get(s, base, f"{root}/policy-set/{psid}/authentication"))
        authz = unwrap(get(s, base, f"{root}/policy-set/{psid}/authorization"))
        full.append({"policySet": ps, "authentication": authn, "authorization": authz})

        for r in authn:
            rule = r.get("rule", r)
            identity = r.get("identitySourceName", "")
            if not isinstance(identity, str):
                identity = ", ".join(filter(None, identity or []))
            rows.append(
                {
                    "policy_set": psname,
                    "stage": "authentication",
                    "rule": rule.get("name", ""),
                    "state": rule.get("state", ""),
                    "condition": _cond_name(rule.get("condition"), cond_lookup),
                    "result": identity,
                }
            )
        for r in authz:
            rule = r.get("rule", r)
            profs = r.get("profile", []) or []
            sgts = r.get("securityGroup", "")
            rows.append(
                {
                    "policy_set": psname,
                    "stage": "authorization",
                    "rule": rule.get("name", ""),
                    "state": rule.get("state", ""),
                    "condition": _cond_name(rule.get("condition"), cond_lookup),
                    "result": ", ".join([prof_lookup.get(p, p) for p in profs])
                    + (f" | SGT:{sgts}" if sgts else ""),
                }
            )

    with open(os.path.join(outdir, f"{domain}_policysets.json"), "w", encoding="utf-8") as f:
        json.dump(full, f, indent=2)
    with open(os.path.join(outdir, f"{domain}_policy.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["policy_set", "stage", "rule", "state", "condition", "result"],
        )
        w.writeheader()
        w.writerows(rows)
    print(f"  {domain}: {len(sets)} policy sets, {len(rows)} rules")


def main():
    ap = argparse.ArgumentParser(description="Export ISE policy sets via OpenAPI (read-only).")
    ap.add_argument("--outdir", default="./ise_export")
    ap.add_argument("--host", default=os.environ.get("ISE_HOST"))
    ap.add_argument(
        "--insecure",
        action="store_true",
        help="skip TLS verify (lab / self-signed PAN cert)",
    )
    args = ap.parse_args()
    if not args.host:
        sys.exit("Set ISE_HOST env var or pass --host (PAN FQDN/IP).")
    os.makedirs(args.outdir, exist_ok=True)
    base = f"https://{args.host}"
    s = make_session(args.insecure)

    print(f"Connecting to {base} ...")
    profs = unwrap(get(s, base, "/api/v1/policy/network-access/authorization-profiles"))
    conds = unwrap(get(s, base, "/api/v1/policy/network-access/condition"))
    with open(os.path.join(args.outdir, "authorization_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f, indent=2)
    with open(os.path.join(args.outdir, "conditions.json"), "w", encoding="utf-8") as f:
        json.dump(conds, f, indent=2)
    prof_lookup = build_lookup(profs)
    cond_lookup = build_lookup(conds)

    for domain in ("network-access", "device-admin"):
        try:
            export_domain(s, base, domain, args.outdir, prof_lookup, cond_lookup)
        except requests.HTTPError as e:
            print(f"  {domain}: skipped ({e})")

    print(f"Done. Files in {args.outdir} — do not commit customer exports.")


if __name__ == "__main__":
    main()
