#!/usr/bin/env node
// Parity battery driver (ts leg).
// Usage: node driver.mjs <maps_dir> <map_id> <input> [--stage S] [--lang L] [--async]
// Prints:  OK<TAB>result   or   ERR<TAB>Class<TAB>message
import { readFileSync } from "node:fs";
import { parseIsc, iscToCompiledMap, expandDocument } from "/Users/mulgogi/src/interscript/interscript-ts/dist/isc/index.js";
import { normaliseMap, bundledStrategy } from "/Users/mulgogi/src/interscript/interscript-ts/dist/loaders.js";
import { MapLoader } from "/Users/mulgogi/src/interscript/interscript-ts/dist/loader.js";
import { executeStage, executeStageAsync } from "/Users/mulgogi/src/interscript/interscript-ts/dist/runtime/interpreter.js";
import { readdirSync } from "node:fs";

// Loader = bundledStrategy over IR JSONs in <maps_dir>/_ir (production shape).
function makeLoader(mapsDir) {
  const irDir = `${mapsDir}/_ir`;
  const maps = {};
  try {
    for (const f of readdirSync(irDir)) {
      if (!f.endsWith(".json")) continue;
      maps[f.replace(/\.json$/, "")] = JSON.parse(readFileSync(`${irDir}/${f}`, "utf8"));
    }
  } catch { /* no _ir dir -> empty loader */ }
  return new MapLoader([bundledStrategy(maps)]);
}

const [mapsDir, mapId, input] = process.argv.slice(2);
const rest = process.argv.slice(5);
let stage = "main";
let language;
let asyncMode = false;
let reverseMode = false;
while (rest.length) {
  const a = rest.shift();
  if (a === "--stage") stage = rest.shift();
  else if (a === "--lang") language = rest.shift();
  else if (a === "--async") asyncMode = true;
  else if (a === "--reverse") reverseMode = true;
  else { console.error(`unknown flag ${a}`); process.exit(2); }
}
if (reverseMode) {
  console.log("ERR\tUnsupported\treverse not implemented in ts runtime (no reverse module in src/)");
  process.exit(0);
}

function fail(e) {
  const name = e && e.name ? e.name : "Error";
  const msg = String(e && e.message ? e.message : e).split("\n")[0];
  console.log(`ERR\t${name}\t${msg}`);
  process.exit(0);
}

try {
  let source;
  try {
    source = readFileSync(`${mapsDir}/${mapId}.isc`, "utf8");
  } catch (e) {
    // production ts consumers resolve maps through loaders, not direct
    // file reads — surface the loader's own error for missing maps.
    throw makeLoader(mapsDir).load(mapId);
  }
  const doc = parseIsc(source, `${mapId}.isc`);
  // dependency docs come from the same dir
  const resolver = (code) => {
    try {
      const src = readFileSync(`${mapsDir}/${code}.isc`, "utf8");
      return parseIsc(src, `${code}.isc`);
    } catch {
      return undefined;
    }
  };
  const expanded = expandDocument(doc, { resolveDependency: resolver });
  const map = normaliseMap(iscToCompiledMap(expanded));
  const loader = makeLoader(mapsDir);
  const p = asyncMode
    ? executeStageAsync(map, stage, input, undefined, language)
    : Promise.resolve(executeStage(map, stage, input, loader, language));
  p.then((out) => { console.log(`OK\t${out}`); process.exit(0); }, fail);
} catch (e) {
  fail(e);
}
