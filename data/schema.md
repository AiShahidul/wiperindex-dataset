# Schema

One row per vehicle and model year. A vehicle appears once per year it was sold, so a model built 2016–2021 has six rows.

UTF-8, comma-separated, `\n` line endings, header row first. Empty means "no value", never `NULL` or `N/A`.

| Column | Type | Example | Notes |
|---|---|---|---|
| `year` | integer | `2019` | Model year, not build year. Range 1946–2026. |
| `make` | string | `Kia` | Manufacturer, in the spelling the manufacturer uses. |
| `model` | string | `Sportage` | Model name without the trim. |
| `trim` | string | `LX` | Blank where every trim of that year takes the same blades. A value here means trims differ. |
| `body_style` | string | `SUV` | Blank where not recorded. |
| `front_driver_in` | number | `26` | Driver-side front blade, inches. Halves appear as `.5`. |
| `front_passenger_in` | number | `16` | Passenger-side front blade, inches. Usually shorter than the driver side. |
| `rear_in` | number | `12` | Rear blade, inches. Blank if no rear wiper or not known — see `rear_wiper`. |
| `front_driver_mm` | integer | `650` | Same blade in millimetres, as the manufacturer specifies it. |
| `front_passenger_mm` | integer | `400` | |
| `rear_mm` | integer | `300` | |
| `rear_wiper` | enum | `yes` | `yes`, `no`, or `unknown`. See below. |
| `front_connector` | string | `J-hook` | Arm connector type. Blank where unverified. |
| `connector_confidence` | enum | `high` | `high`, `medium`, `low`, or blank. See below. |
| `drive_side` | enum | `LHD` | `LHD` or `RHD`. Matters because driver and passenger blades swap sides. |
| `market` | string | `US` | Where this configuration was sold: `US`, `EU`, `IN`, `JP`, and so on. The same model name can carry different blades in different markets. |
| `url` | string | `https://wiperindex.com/kia/sportage/2019` | Page for this vehicle. |

## `rear_wiper`

A blank `rear_in` on its own is ambiguous, so this column resolves it:

- `yes` — the vehicle has a rear wiper. `rear_in` should be filled.
- `no` — the vehicle has no rear wiper. `rear_in` is correctly blank. Most saloons and estates, many coupés.
- `unknown` — not yet verified. `rear_in` blank because the data is missing, not because the wiper is.

Do not treat `no` and `unknown` the same way in an application. Telling someone their car has no rear wiper when it does is worse than telling them you don't know.

## `front_connector` and `connector_confidence`

The connector is the fitting where the blade meets the arm. Common types:

| Value | Also called | Typical on |
|---|---|---|
| `J-hook` | hook, U-hook | most older vehicles, much of the US and Asian market |
| `Push-button` | | VW group, many modern European models |
| `Top-lock` | | Some Ford, Honda |
| `Side-pin` | pin arm | Some European models |
| `Bayonet` | | Older French and some commercial vehicles |
| `Pinch-tab` | | Various European |

`connector_confidence` says how far to trust it:

- `high` — verified against a manufacturer or supplier source. Safe to show a user as fact.
- `medium` — inferred from a rule that holds across that make and era, not individually verified.
- `low` — a guess from a weak pattern. Treat as a hint.
- blank — unknown. The `front_connector` column is blank too.

If you are building something that tells people what to buy, gate on `high` and say "connector not verified for this vehicle" otherwise. A confident wrong connector sends someone to the shop for a blade that will not fit.

## Notes on matching

- **Trim.** Match on year + make + model first. If several rows come back with different trims, the blades differ by trim and you need the user's trim to answer exactly.
- **Market.** The same model name can be a different car in a different market, with different blades. Filter on `market` when you know where the vehicle is.
- **Inches vs millimetres.** The inch and millimetre columns are both as-specified, not converted from each other, so they will not always divide to exactly 25.4. Manufacturers round.
- **Driver side.** On an `RHD` vehicle the driver-side blade is on the right. The `front_driver_in` column always means the driver's side, not a fixed side of the car.
