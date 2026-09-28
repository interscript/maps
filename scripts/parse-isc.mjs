// Parse every maps/*.isc and libs/*.isc with the interscript-ts ISC parser.
// Usage: node scripts/parse-isc.mjs <path-to-interscript-ts-checkout>
import { readdirSync, readFileSync } from "node:fs"
import { pathToFileURL } from "node:url"
import { basename, join, resolve } from "node:path"

const tsDir = process.argv[2]
if (!tsDir) {
  console.error("usage: node scripts/parse-isc.mjs <interscript-ts checkout>")
  process.exit(2)
}

const mod = await import(pathToFileURL(resolve(tsDir, "src/isc/parser.ts")))
const parseIsc = mod.parseIsc

const roots = ["../maps/", "../libs/"].map((r) => new URL(r, import.meta.url).pathname)
const files = roots.flatMap((dir) => readdirSync(dir).filter((f) => f.endsWith(".isc")).map((f) => join(dir, f)))
let ok = 0
const failures = []
for (const path of files.sort()) {
  try {
    parseIsc(readFileSync(path, "utf8"), basename(path))
    ok++
  } catch (e) {
    failures.push(`${basename(path)}: ${e.message.slice(0, 120)}`)
  }
}
console.log(`Parsed ${ok}/${files.length} .isc files`)
if (failures.length) {
  for (const f of failures) console.error(`  ${f}`)
  process.exit(1)
}
