#!/usr/bin/env node
// Build JSON IR for every probe map into maps/_ir/<code>.json (the shared
// artifact form consumed by ts bundledStrategy and py MapLoader).
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { parseIsc, iscToCompiledMap, expandDocument } from "/Users/mulgogi/src/interscript/interscript-ts/dist/isc/index.js";

import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
const dir = `${dirname(fileURLToPath(import.meta.url))}/maps`;
const irDir = `${dir}/_ir`;
mkdirSync(irDir, { recursive: true });

const files = readdirSync(dir).filter((f) => f.endsWith(".isc"));
const docs = {};
for (const f of files) {
  const code = f.replace(/\.isc$/, "");
  try {
    docs[code] = parseIsc(readFileSync(`${dir}/${f}`, "utf8"), f);
  } catch (e) {
    console.log(`skip ${code} (parse: ${String(e.message).split("\n")[0]})`);
  }
}
for (const [code, doc] of Object.entries(docs)) {
  const resolver = (target) => docs[target];
  try {
    const json = iscToCompiledMap(expandDocument(doc, { resolveDependency: resolver }));
    writeFileSync(`${irDir}/${code}.json`, JSON.stringify(json, null, 1));
    console.log(`wrote _ir/${code}.json`);
  } catch (e) {
    console.log(`skip ${code} (expand: ${String(e.message).split("\n")[0]})`);
  }
}
