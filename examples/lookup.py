#!/usr/bin/env python3
"""
Look up a vehicle's wiper blade sizes in the sample CSV.

    python3 examples/lookup.py 2023 Honda CR-V
    python3 examples/lookup.py 2010 Hyundai Veracruz

No dependencies. Full dataset and API: https://wiperindex.com
"""

import csv
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "wiper-sizes-sample.csv"


def load(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find(rows, year, make, model, trim=None):
    matches = [
        row for row in rows
        if row["year"] == str(year)
        and row["make"].lower() == make.lower()
        and row["model"].lower() == model.lower()
    ]
    if trim:
        matches = [r for r in matches if r["trim"].lower() == trim.lower()]
    return matches


def describe(row):
    name = " ".join(filter(None, [row["year"], row["make"], row["model"], row["trim"]]))
    lines = [name]

    def size(label, inches, mm):
        if not inches:
            return
        measurement = f'{inches}"' + (f" ({mm} mm)" if mm else "")
        lines.append(f"  {label:<10} {measurement}")

    size("Driver", row["front_driver_in"], row["front_driver_mm"])
    size("Passenger", row["front_passenger_in"], row["front_passenger_mm"])

    if row["rear_in"]:
        size("Rear", row["rear_in"], row["rear_mm"])
    elif row["rear_wiper"] == "no":
        lines.append("  Rear       none fitted")
    else:
        lines.append("  Rear       not known")

    # Only state the connector when it has been verified. A confident wrong
    # answer sends someone to the shop for a blade that will not clip on.
    if row["front_connector"] and row["connector_confidence"] == "high":
        lines.append(f'  Connector  {row["front_connector"]}')
    else:
        lines.append("  Connector  not verified for this vehicle")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 4:
        sys.exit(f"Usage: {sys.argv[0]} YEAR MAKE MODEL [TRIM]")

    year, make, model = sys.argv[1:4]
    trim = sys.argv[4] if len(sys.argv) > 4 else None

    rows = load(CSV_PATH)
    matches = find(rows, year, make, model, trim)

    if not matches:
        print(f"No match in the sample for {year} {make} {model}.")
        print(f"The sample covers 500 of 46,119 vehicles — try https://wiperindex.com")
        return

    if len(matches) > 1 and not trim:
        print(f"{year} {make} {model} differs by trim:\n")

    print("\n\n".join(describe(row) for row in matches))


if __name__ == "__main__":
    main()
