# WiperIndex Sample Dataset

A free sample of windscreen wiper blade fitment data: which blade lengths fit which vehicles, by make, model and year.

This repository holds **500 sample vehicles** from the [WiperIndex](https://wiperindex.com) database, released so developers can try the data before wiring up the API. The full index covers 46,119 vehicles across 328 makes, model years 1946–2026.

- **Browse the data as a website:** [wiperindex.com](https://wiperindex.com)
- **Full dataset and API:** [wiperindex.com/developers](https://wiperindex.com/developers)

## What's in here

```
data/
  wiper-sizes-sample.csv      500 vehicles, one row per vehicle/year
  schema.md                   what each column means
examples/
  lookup.py                   look up a vehicle in the CSV (Python, no dependencies)
  lookup.js                   the same in Node.js
  api_example.py              query the WiperIndex API instead of the CSV
```

## Quick look

| year | make | model | front_driver_in | front_passenger_in | rear_in | front_connector |
|------|------|-------|-----------------|--------------------|---------|-----------------|
| 2023 | Honda | CR-V | 24 | 19 | 10 | Push-button |
| 2010 | Hyundai | Veracruz | 24 | 20 | | Push-button |

Two things people get wrong when buying blades:

1. **The two front blades are usually different lengths.** Buying a matched pair is the most common mistake.
2. **Length alone does not mean it fits.** The wiper arm ends in a connector — J-hook, push-button, top-lock, side-pin, bayonet — and a blade has to match it. A 26" blade with the wrong connector will not clip on.

Both are why this dataset carries connector information alongside the lengths, and why the connector column has a confidence flag rather than a guess.

## Using the CSV

```bash
python3 examples/lookup.py 2023 Honda CR-V
```

```
2023 Honda CR-V
  Driver     24" (610 mm)
  Passenger  19" (483 mm)
  Rear       10" (254 mm)
  Connector  Push-button
```

Or load it with whatever you normally use:

```python
import csv

with open("data/wiper-sizes-sample.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

crv = [r for r in rows if r["make"] == "Honda" and r["model"] == "CR-V"]
```

```javascript
import { readFileSync } from "node:fs";

const [header, ...lines] = readFileSync("data/wiper-sizes-sample.csv", "utf8").trim().split("\n");
const cols = header.split(",");
const rows = lines.map((line) => Object.fromEntries(line.split(",").map((v, i) => [cols[i], v])));
```

## Columns

Full definitions are in [`data/schema.md`](data/schema.md). The short version:

| Column | Meaning |
|---|---|
| `year`, `make`, `model`, `trim` | the vehicle; trim is blank where every trim takes the same blades |
| `front_driver_in`, `front_passenger_in`, `rear_in` | blade lengths in inches |
| `front_driver_mm`, `front_passenger_mm`, `rear_mm` | the same lengths in millimetres |
| `rear_wiper` | `yes`, `no`, or `unknown` — a blank `rear_in` is not the same as no rear wiper |
| `front_connector` | arm connector type, where known |
| `connector_confidence` | `high`, `medium`, `low`, or blank |
| `url` | the page for this vehicle on wiperindex.com |

`rear_wiper` and `connector_confidence` exist because unknown and absent are different answers. Where the connector could not be verified, the field is blank rather than filled with a likely-looking value.

## Full dataset and API

The sample is a slice, picked to cover a spread of makes, years and connector types. For the whole index:

**API** — free sample tier, no key needed for light use (60 requests a minute, 2,000 a day per IP):

```bash
curl "https://wiperindex.com/api/v1/fitment?make=Honda&model=CR-V&year=2023"
```

```json
{
  "ok": true,
  "data": [
    {
      "make": "Honda",
      "model": "CR-V",
      "year": 2023,
      "size_key": "24+19",
      "front": { "driver_in": "24", "passenger_in": "19", "arm": "Push-button" },
      "rear": { "size_in": "10" }
    }
  ],
  "meta": { "version": "v1-sample", "sample": true, "count": 1 }
}
```

`data` is an array — one entry per distinct configuration for that vehicle and year, with lengths as strings. The sample tier returns the fields above; trim, generation and the rear arm come back on keyed requests. Other endpoints include `/api/v1/makes`, `/models?make=`, `/years?make=&model=`, `/search/by-size?size=26+20`, `/search/by-rear?size=14` and `/stats`.

See [wiperindex.com/developers](https://wiperindex.com/developers) for the full endpoint list, pricing and terms.

## Accuracy and corrections

Sizes are compiled per model year and cross-checked against neighbouring years, but no fitment database is perfect — manufacturers change blade lengths mid-generation, and regional variants of the same model name can differ.

Found a row that looks wrong? Open an issue with the year, make, model and trim, and what your car actually takes. Corrections get looked at first, and fixes flow back into the main database.

## Licence

The sample data is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — use it commercially, modify it, redistribute it, with attribution to [WiperIndex](https://wiperindex.com).

The example code is MIT.
