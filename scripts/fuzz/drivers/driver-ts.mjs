#!/usr/bin/env node
// Fuzz driver (ts leg). Usage: node driver-ts.mjs <case.isc> <inputs-json>
// Production path: parseIsc -> expandDocument -> iscToCompiledMap ->
// normaliseMap -> executeStage. Single JSON line on stdout, exit 0 unless
// the VM dies (which the runner records as a crash finding).
import { readFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";

const TS_DIST = process.env.TS_DIST || resolve(import.meta.dirname, "../../interscript-ts/dist");
const { parseIsc, iscToCompiledMap, expandDocument } = await import(
  `file://${resolve(TS_DIST, "isc/index.js")}`
);
const { normaliseMap } = await import(`file://${resolve(TS_DIST, "loaders.js")}`);
const { executeStage } = await import(`file://${resolve(TS_DIST, "runtime/interpreter.js")}`);

const CRASH_CLASSES = new Set([
  "TypeError", "RangeError", "ReferenceError", "EvalError", "URIError",
]);

function bucket(e) {
  const name = e && e.name ? e.name : "Error";
  switch (name) {
    case "IscParseError": return "PARSE";
    case "IscLoadError": return "LOAD";
    case "MapLogicError":
    case "SystemConversionError":
    case "DependencyMissingError": return "LOGIC";
    case "MapNotFoundError": return "LOAD";
    default: return CRASH_CLASSES.has(name) ? "CRASH" : "OTHER";
  }
}

function fail(e) {
  return {
    status: "ERR",
    class: e && e.name ? e.name : "Error",
    bucket: bucket(e),
    message: String(e && e.message ? e.message : e).split("\n")[0].slice(0, 200),
  };
}

const caseFile = process.argv[2];
const inputs = JSON.parse(process.argv[3] || "[]");
const stem = basename(caseFile, ".isc");
const dir = dirname(caseFile);
const result = { runtime: "ts", exec: [] };

try {
  // Harness-boundary normalization: invalid UTF-8 becomes U+FFFD for every
  // runtime identically (the runner pre-sanitizes when needed).
  const src = readFileSync(caseFile, "utf8");
  const resolver = (code) => {
    try {
      return parseIsc(readFileSync(`${dir}/${code}.isc`, "utf8"), `${code}.isc`);
    } catch {
      return undefined;
    }
  };
  const doc = parseIsc(src, `${stem}.isc`);
  const expanded = expandDocument(doc, { resolveDependency: resolver });
  const map = normaliseMap(iscToCompiledMap(expanded));
  result.parse = { status: "OK" };
  for (const input of inputs) {
    try {
      result.exec.push({ input, status: "OK", output: executeStage(map, "main", input) });
    } catch (e) {
      result.exec.push({ input, ...fail(e) });
    }
  }
} catch (e) {
  result.parse = fail(e);
}

console.log(JSON.stringify(result));
