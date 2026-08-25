// Parse every maps/*.isc with the interscript-ts ISC parser.
// Usage: node scripts/parse-isc.mjs <path-to-interscript-ts-checkout>
import { readdirSync, readFileSync } from "node:fs"
import { pathToFileURL } from "node:url"
import { resolve } from "node:path"

const tsDir = process.argv[2]
if (!tsDir) {
  console.error("usage: node scripts/parse-isc.mjs <interscript-ts checkout>")
  process.exit(2)
}

const mod = await import(pathToFileURL(resolve(tsDir, "src/isc/parser.ts")))
const parseIsc = mod.parseIsc

const dir = new URL("../maps/", import.meta.url).pathname
const files = readdirSync(dir).filter((f) => f.endsWith(".isc"))
let ok = 0
const failures = []
for (const f of files.sort()) {
  try {
    parseIsc(readFileSync(resolve(dir, f), "utf8"), f)
    ok++
  } catch (e) {
    failures.push(`${f}: ${e.message.slice(0, 120)}`)
  }
}
console.log(`Parsed ${ok}/${files.length} .isc files`)
if (failures.length) {
  for (const f of failures) console.error(`  ${f}`)
  process.exit(1)
}
