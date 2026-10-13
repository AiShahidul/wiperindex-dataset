#!/usr/bin/env node
/**
 * Look up a vehicle's wiper blade sizes in the sample CSV.
 *
 *   node examples/lookup.js 2023 Honda CR-V
 *   node examples/lookup.js 2010 Hyundai Veracruz
 *
 * No dependencies. Full dataset and API: https://wiperindex.com
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const CSV_PATH = join(dirname(fileURLToPath(import.meta.url)), "..", "data", "wiper-sizes-sample.csv");

function load(path) {
  const [header, ...lines] = readFileSync(path, "utf8").trim().split("\n");
  const columns = header.split(",");
  return lines.map((line) =>
    Object.fromEntries(line.split(",").map((value, i) => [columns[i], value]))
  );
}

function find(rows, year, make, model, trim) {
  return rows.filter(
    (row) =>
      row.year === String(year) &&
      row.make.toLowerCase() === make.toLowerCase() &&
      row.model.toLowerCase() === model.toLowerCase() &&
      (!trim || row.trim.toLowerCase() === trim.toLowerCase())
  );
}

function describe(row) {
  const name = [row.year, row.make, row.model, row.trim].filter(Boolean).join(" ");
  const lines = [name];

  const size = (label, inches, mm) => {
    if (!inches) return;
    lines.push(`  ${label.padEnd(10)} ${inches}"${mm ? ` (${mm} mm)` : ""}`);
  };

  size("Driver", row.front_driver_in, row.front_driver_mm);
  size("Passenger", row.front_passenger_in, row.front_passenger_mm);

  if (row.rear_in) size("Rear", row.rear_in, row.rear_mm);
  else if (row.rear_wiper === "no") lines.push("  Rear       none fitted");
  else lines.push("  Rear       not known");

  // Only state the connector when it has been verified. A confident wrong
  // answer sends someone to the shop for a blade that will not clip on.
  if (row.front_connector && row.connector_confidence === "high") {
    lines.push(`  Connector  ${row.front_connector}`);
  } else {
    lines.push("  Connector  not verified for this vehicle");
  }

  return lines.join("\n");
}

const [year, make, model, trim] = process.argv.slice(2);

if (!year || !make || !model) {
  console.error("Usage: node examples/lookup.js YEAR MAKE MODEL [TRIM]");
  process.exit(1);
}

const matches = find(load(CSV_PATH), year, make, model, trim);

if (matches.length === 0) {
  console.log(`No match in the sample for ${year} ${make} ${model}.`);
  console.log("The sample covers 500 of 46,119 vehicles — try https://wiperindex.com");
} else {
  if (matches.length > 1 && !trim) console.log(`${year} ${make} ${model} differs by trim:\n`);
  console.log(matches.map(describe).join("\n\n"));
}
