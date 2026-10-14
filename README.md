# check-sbd

Shows how many Akamai Secure by Default (SBD) certificates each contract on an account has used, and how many are still available.

It calls the Property Manager API (PAPI) and reads the per-contract limit from the `x-limit-default-certs-per-contract-*` response headers on a property hostnames request.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- An `~/.edgerc` file with API credentials that have read access to PAPI

## Usage

```sh
uv run check_sbd.py
```

You don't need to create a virtual environment. The dependencies are declared inline in the script ([PEP 723](https://peps.python.org/pep-0723/)), and `uv run` installs them into an isolated, cached environment automatically.

### Environment variables

| Variable                    | Description                                   | Default   |
| --------------------------- | --------------------------------------------- | --------- |
| `AKAMAI_EDGEGRID_SECTION`   | `.edgerc` section to use                      | `default` |
| `AKAMAI_ACCOUNT_SWITCH_KEY` | Account switch key (for multi-account access) | unset     |

Example:

```sh
AKAMAI_EDGEGRID_SECTION=papi AKAMAI_ACCOUNT_SWITCH_KEY=1-ABCDE uv run check_sbd.py
```

## Example output

```
Account: Example Corp (act_1-ABCDE)

Contract               Used  Available  Limit
---------------------------------------------
ctr_1-ABCDE              12        988   1000
ctr_1-FGHIJ          n/a (no properties found)
```

A contract shows `n/a` when none of its groups has a property. The script needs at least one property to read the limit headers from.
