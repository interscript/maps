#!/usr/bin/env node
// Build the deployable JSON-IR map artifact from this repository's .isc corpus.
//
// Usage:
//   node scripts/build-json-ir-artifact.mjs <interscript-ts-dir> <out-dir>
//
// Output directory layout:
//   manifest.json
//   SHA256SUMS
//   maps/<system>.json

import { createHash } from "node:crypto"
import { mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs"
import { basename, join, relative, resolve } from "node:path"
import { pathToFileURL } from "node:url"

const [tsDir, outDir] = process.argv.slice(2)
if (!tsDir || !outDir) {
  console.error("usage: build-json-ir-artifact.mjs <interscript-ts-dir> <out-dir>")
  process.exit(2)
}

const repoRoot = resolve(import.meta.dirname, "..")
const mapsDir = join(repoRoot, "maps")
const outputRoot = resolve(outDir)
const outputMaps = join(outputRoot, "maps")

const { parseIsc } = await import(pathToFileURL(resolve(tsDir, "src/isc/parser.ts")))
const { iscToCompiledMap } = await import(pathToFileURL(resolve(tsDir, "src/isc/converter.ts")))

rmSync(outputRoot, { recursive: true, force: true })
mkdirSync(outputMaps, { recursive: true })

const files = readdirSync(mapsDir)
  .filter((file) => file.endsWith(".isc"))
  .sort()

const systems = []
for (const file of files) {
  const code = basename(file, ".isc")
  const source = readFileSync(join(mapsDir, file), "utf8")
  const doc = parseIsc(source, file)
  const compiled = iscToCompiledMap(doc)
  writeFileSync(join(outputMaps, `${code}.json`), `${JSON.stringify(compiled)}\n`)
  systems.push(code)
}

const manifest = {
  schema: "interscript.maps.ir.v1",
  source: "interscript/maps",
  generatedAt: new Date().toISOString(),
  count: systems.length,
  systems,
}
writeFileSync(join(outputRoot, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`)

const artifactFiles = []
function walk(dir) {
  for (const name of readdirSync(dir).sort()) {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) walk(path)
    else artifactFiles.push(path)
  }
}
walk(outputRoot)

const checksums = artifactFiles
  .filter((path) => basename(path) !== "SHA256SUMS")
  .map((path) => {
    const sha = createHash("sha256").update(readFileSync(path)).digest("hex")
    return `${sha}  ${relative(outputRoot, path)}`
  })
  .join("\n")
writeFileSync(join(outputRoot, "SHA256SUMS"), `${checksums}\n`)

console.log(`compiled ${systems.length} maps to ${outputRoot}`)
