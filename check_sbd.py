# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "edgegrid-python",
#     "requests",
# ]
# ///
"""Show used/available Secure by Default (default) certificates per contract.

Env vars:
  AKAMAI_EDGEGRID_SECTION     .edgerc section to use (default: "default")
  AKAMAI_ACCOUNT_SWITCH_KEY   optional account switch key

Usage:
  uv run check_sbd.py
"""

import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc

LIMIT_HEADER = "x-limit-default-certs-per-contract-limit"
REMAINING_HEADER = "x-limit-default-certs-per-contract-remaining"


def make_client():
    section = os.environ.get("AKAMAI_EDGEGRID_SECTION", "default")
    edgerc = EdgeRc(str(Path.home() / ".edgerc"))
    base_url = f"https://{edgerc.get(section, 'host')}"
    session = requests.Session()
    session.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    account_switch_key = os.environ.get("AKAMAI_ACCOUNT_SWITCH_KEY")

    def get(path, **params):
        if account_switch_key:
            params["accountSwitchKey"] = account_switch_key
        resp = session.get(urljoin(base_url, path), params=params)
        resp.raise_for_status()
        return resp

    return get


def sbd_limits(get, contract_id, group_id):
    """Return (limit, remaining) from the first property with a version, or None."""
    props = get("/papi/v1/properties", contractId=contract_id, groupId=group_id).json()
    for prop in props["properties"]["items"]:
        resp = get(
            f"/papi/v1/properties/{prop['propertyId']}/versions/{prop['latestVersion']}/hostnames",
            contractId=contract_id,
            groupId=group_id,
            includeCertStatus="true",
        )
        if LIMIT_HEADER in resp.headers:
            return int(resp.headers[LIMIT_HEADER]), int(resp.headers[REMAINING_HEADER])
    return None


def main():
    get = make_client()
    data = get("/papi/v1/groups").json()

    # First group seen per contract; keep the rest as fallbacks for empty groups.
    groups_per_contract = {}
    for group in data["groups"]["items"]:
        for contract_id in group.get("contractIds", []):
            groups_per_contract.setdefault(contract_id, []).append(group["groupId"])

    print(f"Account: {data.get('accountName')} ({data.get('accountId')})\n")
    print(f"{'Contract':<20} {'Used':>6} {'Available':>10} {'Limit':>6}")
    print("-" * 45)
    for contract_id, group_ids in groups_per_contract.items():
        result = None
        for group_id in group_ids:
            result = sbd_limits(get, contract_id, group_id)
            if result:
                break
        if result is None:
            print(f"{contract_id:<20} {'n/a (no properties found)':>24}")
            continue
        limit, remaining = result
        print(f"{contract_id:<20} {limit - remaining:>6} {remaining:>10} {limit:>6}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        sys.exit(f"API error: {e}\n{e.response.text}")
