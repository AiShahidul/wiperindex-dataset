#!/usr/bin/env python3
"""
Build data/wiper-sizes-sample.csv from the master WiperIndex export.

This script is for maintaining the repo, not for people using the data.
It takes the full specs export, maps its columns onto the published schema,
and picks a spread of vehicles across makes, years and connector types.

    python3 build_sample.py /path/to/master_specs.csv
    python3 build_sample.py /path/to/master_specs.csv --rows 500

Edit COLUMN_MAP below so the keys match the column names in the export.
Anything left as None is written blank.
"""

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

OUT_PATH = Path(__file__).parent / "data" / "wiper-sizes-sample.csv"

FIELDS = [
    "year", "make", "model", "trim", "body_style",
    "front_driver_in", "front_passenger_in", "rear_in",
    "front_driver_mm", "front_passenger_mm", "rear_mm",
    "rear_wiper", "front_connector", "connector_confidence",
    "drive_side", "market", "url",
]

# published column -> column name in the master export (None = leave blank)
COLUMN_MAP = {
    "year": "year",
    "make": "make",
    "model": "model",
    "trim": "trim",
    "body_style": None,          # not in the master export
    "front_driver_in": "driver",
    "front_passenger_in": "passenger",
    "rear_in": "rear",
    "front_driver_mm": None,
    "front_passenger_mm": None,
    "rear_mm": None,
    "rear_wiper": None,
    # front_arm mixes real connectors ("Push-button", "J-hook", "Bayonet") with
    # blade types ("Beam blade") and stray numbers. normalize_connector() keeps
    # only recognised connector types and blanks the rest.
    "front_connector": "front_arm",
    "connector_confidence": None,  # derived in build_row, not a source column
    "drive_side": None,
    "market": None,
    "url": None,
}

# Recognised wiper-arm connectors, matched as a substring of the raw front_arm
# value (lowercased). First match wins, so order the more specific needles
# first. Anything that matches nothing — "Beam blade", stray sizes, "0" — is
# treated as unknown and the connector is left blank, per data/schema.md.
CONNECTOR_PATTERNS = [
    ("push", "Push-button"),
    ("bayonet", "Bayonet"),
    ("top-lock", "Top-lock"),
    ("top lock", "Top-lock"),
    ("side-pin", "Side-pin"),
    ("side pin", "Side-pin"),
    ("pin arm", "Side-pin"),
    ("pinch", "Pinch-tab"),
    ("j-hook", "J-hook"),
    ("hook", "J-hook"),
]

MM_PER_INCH = 25.4
# A value above this in an inch column is a millimetre value in the wrong place.
INCH_CEILING = 40


def clean(value):
    return (value or "").strip()


def to_number(value):
    """Parse a length. Returns (inches, millimetres), either may be None."""
    text = clean(value).lower().replace('"', "").replace("″", "")
    if not text:
        return None, None
    text = text.replace("inch", "").replace("in", "").strip()
    is_mm = "mm" in text
    text = text.replace("mm", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None, None
    number = float(match.group())
    if is_mm or number > INCH_CEILING:
        return round(number / MM_PER_INCH * 2) / 2, int(round(number))
    return number, int(round(number * MM_PER_INCH))


def fmt_in(value):
    if value is None:
        return ""
    return str(int(value)) if value == int(value) else str(value)


def normalize_connector(raw):
    """Raw front_arm value -> (connector, confidence).

    Only recognised connector types survive, and they come straight from the
    production spec table that the live site serves, so they are rated "high".
    Everything else (blade types, stray sizes, blanks) -> ("", "")."""
    text = clean(raw).lower()
    if not text:
        return "", ""
    for needle, label in CONNECTOR_PATTERNS:
        if needle in text:
            return label, "high"
    return "", ""


def build_row(source, slug):
    def get(field):
        column = COLUMN_MAP.get(field)
        return clean(source.get(column)) if column else ""

    row = {field: get(field) for field in FIELDS}

    for inches_field, mm_field in (
        ("front_driver_in", "front_driver_mm"),
        ("front_passenger_in", "front_passenger_mm"),
        ("rear_in", "rear_mm"),
    ):
        inches, mm = to_number(row[inches_field])
        row[inches_field] = fmt_in(inches)
        if not row[mm_field]:
            row[mm_field] = str(mm) if mm else ""

    # rear_wiper: only claim "no" when the export says so explicitly.
    if not row["rear_wiper"]:
        row["rear_wiper"] = "yes" if row["rear_in"] else "unknown"

    # A connector and its confidence travel together: an unrated connector is
    # a guess dressed as a fact, and a rating with no connector says nothing.
    # front_arm is noisy, so keep only recognised connector types.
    row["front_connector"], row["connector_confidence"] = normalize_connector(
        row["front_connector"]
    )

    if not row["url"]:
        row["url"] = f"https://wiperindex.com/make/{slug(row['make'])}/{slug(row['model'])}/{row['year']}"

    return row


def slugify(text):
    # Mirror the site's toSlug: strip accents, "&" -> "and", non-alphanumeric
    # -> "-", so the url column lands on the real canonical page.
    t = unicodedata.normalize("NFKD", clean(text))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# A sample is meant to show the data off, not to mirror the long tail of
# obscure makes. Keep it to recognisable brands, and inside each brand surface
# the rows that actually fill the interesting columns.
MAKE_CAP = 50       # how many makes may appear at all
PER_MAKE_CAP = 15   # no single make dominates the sample
PER_MODEL_CAP = 3   # a few years of a model, not twenty


def _richness(row):
    """Sort key: connector first, then a rear wiper, then the newest year."""
    return (
        1 if row["front_connector"] else 0,
        1 if row["rear_in"] else 0,
        int(row["year"]) if row["year"].isdigit() else 0,
    )


def pick(rows, target):
    """Spread across the best-covered makes, richest rows first.

    Makes are ranked by how many vehicles we hold for them, which puts the
    mainstream consumer brands ahead of one-off commercial entries. Within a
    make the rows with a connector and a rear length come first, so those
    columns are populated rather than empty across the whole sample.
    """
    by_make = defaultdict(list)
    for row in rows:
        by_make[row["make"]].append(row)

    makes = sorted(by_make, key=lambda m: len(by_make[m]), reverse=True)[:MAKE_CAP]
    for make in makes:
        by_make[make].sort(key=_richness, reverse=True)

    chosen = []
    used = set()
    make_count = defaultdict(int)
    model_count = defaultdict(int)

    progressed = True
    while len(chosen) < target and progressed:
        progressed = False
        for make in makes:
            if len(chosen) >= target:
                break
            if make_count[make] >= PER_MAKE_CAP:
                continue
            for i, row in enumerate(by_make[make]):
                mkey = (make, i)
                if mkey in used:
                    continue
                model_key = (make, row["model"])
                if model_count[model_key] >= PER_MODEL_CAP:
                    continue
                used.add(mkey)
                chosen.append(row)
                make_count[make] += 1
                model_count[model_key] += 1
                progressed = True
                break  # one row per make per pass keeps makes interleaved

    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="master specs CSV export")
    parser.add_argument("--rows", type=int, default=500, help="how many rows to publish")
    args = parser.parse_args()

    if not args.source.exists():
        sys.exit(f"No such file: {args.source}")

    with args.source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [
            column for column in COLUMN_MAP.values()
            if column and column not in reader.fieldnames
        ]
        if missing:
            sys.exit(
                "These columns are in COLUMN_MAP but not in the export:\n  "
                + "\n  ".join(missing)
                + "\n\nColumns found in the export:\n  "
                + "\n  ".join(reader.fieldnames)
            )
        source_rows = [build_row(r, slugify) for r in reader]

    # Drop rows with no front sizes. Also drop the rare row whose make, model
    # or trim contains a comma: keeping the CSV comma-free means no field ever
    # needs quoting, so the zero-dependency split-on-comma parser in
    # examples/lookup.js stays correct on every row.
    with_sizes = [
        row for row in source_rows
        if row["front_driver_in"] and row["front_passenger_in"]
        and not any("," in (row[field] or "") for field in ("make", "model", "trim"))
    ]

    # Collapse to one row per vehicle + year. The master export carries a row
    # per engine/variant, but the published grain is the blade set: if every
    # variant of a year takes the same blades, emit one row with trim blank
    # (schema.md); only where the blades actually differ do we keep a row per
    # distinct set, with the trim that distinguishes it.
    def blade_sig(r):
        return (
            r["front_driver_in"], r["front_passenger_in"], r["rear_in"],
            r["rear_wiper"], r["front_connector"], r["connector_confidence"],
        )

    groups = defaultdict(list)
    for row in with_sizes:
        groups[(row["year"], row["make"], row["model"])].append(row)

    usable = []
    for variants in groups.values():
        sigs = {blade_sig(r): r for r in variants}
        if len(sigs) == 1:
            row = dict(next(iter(sigs.values())))
            row["trim"] = ""  # blades are identical across trims
            usable.append(row)
        else:
            usable.extend(dict(r) for r in sigs.values())  # trims genuinely differ

    chosen = pick(usable, args.rows)
    chosen.sort(key=lambda r: (r["make"], r["model"], r["year"], r["trim"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(chosen)

    makes = len({r["make"] for r in chosen})
    years = sorted({int(r["year"]) for r in chosen if r["year"].isdigit()})
    verified = sum(1 for r in chosen if r["connector_confidence"] == "high")
    print(f"Wrote {len(chosen)} rows to {OUT_PATH}")
    print(f"  {makes} makes, model years {years[0]}-{years[-1]}")
    print(f"  {verified} rows with a verified connector")


if __name__ == "__main__":
    main()
