#!/usr/bin/env node
// Corpus parse timing (ts): parseIsc on all 428 corpus maps, 3 runs.
import { readFileSync, readdirSync } from "node:fs";
const { parseIsc } = await import("/Users/mulgogi/src/interscript/interscript-ts/dist/isc/index.js");

const dir = "/Users/mulgogi/src/interscript/maps/maps";
const files = readdirSync(dir).filter((f) => f.endsWith(".isc")).sort();
if (files.length === 0) throw new Error("no files");

for (let run = 0; run < 3; run++) {
  const t0 = performance.now();
  let ok = 0;
  for (const f of files) {
    try {
      parseIsc(readFileSync(`${dir}/${f}`, "utf8"), f);
      ok++;
    } catch (e) {
      console.error(`FAIL ${f}: ${String(e.message).split("\n")[0]}`);
    }
  }
  const t1 = performance.now();
  console.log(`ts parse ${ok}/${files.length} maps in ${(t1 - t0).toFixed(1)} ms`);
}
