#!/usr/bin/env node
// Generate an ISC `tests { ... }` block body from exhaustively-extracted
// source-table rows.
//
// The corpus rule (maps CLAUDE.md): every map carries tests from its OWN
// document's examples. Most maps carry spot samples; this tool makes
// exhaustive per-row testing cheap: transcribe the source document's table
// into a JSON provenance artifact, and generate one embedded test per row.
//
// Input (a provenance artifact, e.g. scripts/row-sources/<system>.json):
//   {
//     "system": "<file stem, e.g. alalc-vai-Vaii-Latn-2010>",
//     "rows":   [["<from>", "<to>"], ...],   // transcribed from the source table
//     "note":   "<source pages / document citation>"
//   }
//
// Output: an ISC tests-block BODY (the lines that go between `tests {` and
// its closing `}`) on stdout, or `--out FILE`. The body carries a header
// comment citing the source, the generation date, and a `generated-by`
// marker so generated tests stay distinguishable from hand tests. The JSON
// artifact is the provenance record; commit it alongside the map.
//
// Validation: rows must be non-empty [from, to] string pairs with a
// non-empty `from`; duplicate `from`s are reported and abort; an empty row
// set is rejected (no output written).
//
// Usage:
//   node scripts/gen-row-tests.mjs <rows.json> [--sorted] [--out FILE]
//
//     --sorted   emit rows sorted by `from` (code-point order); default is
//                document order (the order the rows appear in the artifact)
//     --out FILE write the body to FILE instead of stdout
//
// Exit codes: 0 ok, 1 validation failure (duplicates / empty / bad rows),
// 2 usage or IO error.

import { readFileSync, writeFileSync, existsSync } from "node:fs"

const USAGE = `usage: node scripts/gen-row-tests.mjs <rows.json> [--sorted] [--out FILE]`

function fail(message, code) {
  console.error(`gen-row-tests: ${message}`)
  process.exit(code)
}

const args = process.argv.slice(2)
const positional = []
let sorted = false
let outFile = null
for (let i = 0; i < args.length; i++) {
  const a = args[i]
  if (a === "--sorted") sorted = true
  else if (a === "--out") {
    outFile = args[++i]
    if (!outFile) fail("--out requires a file path", 2)
  } else if (a === "--help" || a === "-h") {
    console.log(USAGE)
    process.exit(0)
  } else positional.push(a)
}
if (positional.length !== 1) fail(USAGE, 2)
const inputPath = positional[0]
if (!existsSync(inputPath)) fail(`input not found: ${inputPath}`, 2)

let artifact
try {
  artifact = JSON.parse(readFileSync(inputPath, "utf8"))
} catch (e) {
  fail(`cannot parse ${inputPath}: ${e.message}`, 2)
}

const system = artifact.system
if (typeof system !== "string" || !system.trim()) {
  fail(`"system" must be a non-empty string (the map file stem)`, 1)
}
const note = typeof artifact.note === "string" ? artifact.note.trim() : ""
if (!Array.isArray(artifact.rows) || artifact.rows.length === 0) {
  fail(`"rows" must be a non-empty array of [from, to] pairs`, 1)
}

// --- row validation --------------------------------------------------------

const seen = new Map() // from -> first index
const rows = []
for (let i = 0; i < artifact.rows.length; i++) {
  const row = artifact.rows[i]
  if (!Array.isArray(row) || row.length !== 2) {
    fail(`row ${i}: expected a [from, to] pair, got ${JSON.stringify(row)}`, 1)
  }
  const [from, to] = row
  if (typeof from !== "string" || !from.trim()) {
    fail(`row ${i}: "from" must be a non-empty string, got ${JSON.stringify(from)}`, 1)
  }
  if (typeof to !== "string" || !to.trim()) {
    fail(`row ${i}: "to" must be a non-empty string (an instruction row has no romanization and must not be transcribed), got ${JSON.stringify(to)}`, 1)
  }
  if (seen.has(from)) {
    fail(
      `duplicate "from" ${JSON.stringify(from)}: row ${i} repeats row ${seen.get(from)}` +
        ` — every table row must appear exactly once`,
      1,
    )
  }
  seen.set(from, i)
  rows.push([from, to])
}

if (rows.length === 0) fail(`no rows to emit; refusing to write an empty test set`, 1)

if (sorted) rows.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))

// --- emission --------------------------------------------------------------

// JSON.stringify's escaping (`\"`, `\\`, `\n`, `\uXXXX` for controls) is a
// subset of the ISC double-quoted string escapes.
const quote = (s) => JSON.stringify(s)
const date = new Date().toISOString().slice(0, 10)

// Wrap the source citation across comment lines (~74 columns).
function wrapComment(text, width = 74) {
  const out = []
  for (const paragraph of text.split("\n")) {
    let line = ""
    for (const word of paragraph.split(/\s+/).filter(Boolean)) {
      const candidate = line ? `${line} ${word}` : word
      if (candidate.length > width && line) {
        out.push(`# ${line}`)
        line = word
      } else line = candidate
    }
    if (line) out.push(`# ${line}`)
  }
  return out
}

const citation = note || "(source citation missing from the artifact)"
const header = [
  `# Exhaustive per-row tests for ${system}, generated from the source`,
  `# document's table.`,
  ...wrapComment(`Source: ${citation}`),
  `# Provenance artifact: scripts/row-sources/${system}.json (${rows.length} rows).`,
  `# generated-by: maps/scripts/gen-row-tests.mjs (${date}); regenerate from the artifact, do not hand-edit.`,
]

const lines = [...header, ...rows.map(([from, to]) => `  ${quote(from)} -> ${quote(to)}`)]

const body = lines.join("\n") + "\n"

if (outFile) {
  writeFileSync(outFile, body, "utf8")
  console.error(`gen-row-tests: wrote ${rows.length} tests (${sorted ? "sorted" : "document order"}) to ${outFile}`)
} else {
  process.stdout.write(body)
}
