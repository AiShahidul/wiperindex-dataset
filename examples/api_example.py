#!/usr/bin/env python3
"""
Query the WiperIndex API for a vehicle not in the sample CSV.

    python3 examples/api_example.py 2023 Honda CR-V

The sample in this repo is 500 of 46,119 vehicles. The API covers all of them.
Endpoints, rate limits and terms: https://wiperindex.com/developers
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://wiperindex.com/api/v1/fitment"
TIMEOUT = 10


# Send a real User-Agent. The default "Python-urllib/x.y" is a common scraper
# signature and the site's edge blocks it with a 403; any descriptive agent is
# fine (python-requests, Node fetch and browsers all pass as-is).
USER_AGENT = "wiperindex-api-example/1.0 (+https://github.com/wiperindex/wiperindex-dataset)"


def fetch(year, make, model):
    params = {"make": make, "model": model, "year": year}
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )

    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def describe(item):
    """One fitment entry from the `data` array -> readable block."""
    name = " ".join(str(item.get(key, "")) for key in ("year", "make", "model")).strip()
    front = item.get("front") or {}
    rear = item.get("rear") or {}

    lines = [name]
    if front.get("driver_in"):
        lines.append(f'  Driver     {front["driver_in"]}"')
    if front.get("passenger_in"):
        lines.append(f'  Passenger  {front["passenger_in"]}"')
    if rear.get("size_in"):
        lines.append(f'  Rear       {rear["size_in"]}"')
    # The API returns this as `arm`; it carries the connector where known, or a
    # blade type ("Beam blade") otherwise.
    if front.get("arm"):
        lines.append(f'  Arm        {front["arm"]}')
    return "\n".join(lines)


def unique(items):
    """Collapse identical entries the sample tier can return for one vehicle."""
    seen, out = set(), []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def main():
    if len(sys.argv) < 4:
        sys.exit(f"Usage: {sys.argv[0]} YEAR MAKE MODEL")

    year, make, model = sys.argv[1:4]

    try:
        payload = fetch(year, make, model)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            sys.exit(f"No fitment data for {year} {make} {model}.")
        if error.code == 429:
            sys.exit("Rate limited. See https://wiperindex.com/developers for the limits.")
        sys.exit(f"API returned {error.code}: {error.reason}")
    except urllib.error.URLError as error:
        sys.exit(f"Could not reach the API: {error.reason}")

    if not payload.get("ok"):
        sys.exit(payload.get("error", "Request failed."))

    items = unique(payload.get("data") or [])
    if not items:
        sys.exit(f"No fitment data for {year} {make} {model}.")

    print("\n\n".join(describe(item) for item in items))


if __name__ == "__main__":
    main()
