// Shared utilities for the ISC differential fuzz harness (WO20, maps#284).
// Deterministic PRNG, corpus listing, case/test-input extraction, driver
// invocation. Drivers are discovered from ./drivers and parameterized by
// environment (RUBY_LIB, TS_DIST, PY_SRC, ISCRS_BIN) so the harness is
// portable — no absolute paths are baked in.

import { readdirSync, readFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const FUZZ_DIR = dirname(fileURLToPath(import.meta.url));

export const RUNTIMES = ["ruby", "ts", "py", "rs"];

export const DRIVER_ENV = {
  ruby: { RUBY_LIB: "../../../interscript-ruby/lib" },
  ts: { TS_DIST: "../../../interscript-ts/dist" },
  py: { PY_SRC: "../../../interscript-py/src" },
  rs: { ISCRS_BIN: "../../../interscript-rs/target/release/iscrs" },
};
// Defaults assume the runtime repos are checked out as SIBLINGS of the maps
// clone (the layout maps-CI creates). Any location can be injected via the
// RUBY_LIB / TS_DIST / PY_SRC / ISCRS_BIN environment variables.

// ---------------------------------------------------------------------------
// Deterministic PRNG (mulberry32). Every generator output is reproducible
// from a single 32-bit seed.
// ---------------------------------------------------------------------------

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeRng(seed) {
  const next = mulberry32(seed);
  return {
    next,
    int: (lo, hi) => lo + Math.floor(next() * (hi - lo + 1)),
    pick: (arr) => arr[Math.floor(next() * arr.length)],
    chance: (p) => next() < p,
    shuffle(arr) {
      const a = arr.slice();
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(next() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    },
    // weighted pick: items = [{item, weight}]
    weighted(items) {
      const total = items.reduce((s, it) => s + it.weight, 0);
      let r = next() * total;
      for (const it of items) {
        r -= it.weight;
        if (r <= 0) return it.item;
      }
      return items[items.length - 1].item;
    },
  };
}

// ---------------------------------------------------------------------------
// Corpus access
// ---------------------------------------------------------------------------

const DEFAULT_CORPUS_ROOT = resolve(FUZZ_DIR, "..", "..");

export function listCorpus(corpusRoot = DEFAULT_CORPUS_ROOT) {
  const out = [];
  for (const sub of ["maps", "libs", join("maps-staging", "maps")]) {
    const dir = join(corpusRoot, sub);
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir)) {
      if (!f.endsWith(".isc")) continue;
      const path = join(dir, f);
      try {
        const buf = readFileSync(path);
        out.push({ name: f, path, bytes: buf.byteLength });
      } catch {
        /* unreadable seed: skip */
      }
    }
  }
  return out;
}

// Size-weighted seed selection: prefer small maps (fast drivers), keep some
// large ones in rotation, skip giants that dominate runtime budgets.
export function pickSeedMap(rng, corpus, maxSeedBytes = 250_000) {
  const pool = corpus.filter((m) => m.bytes <= maxSeedBytes);
  const items = pool.map((m) => ({ item: m, weight: 1 / Math.sqrt(m.bytes) }));
  return rng.weighted(items);
}

// ---------------------------------------------------------------------------
// Case / test-input extraction
// ---------------------------------------------------------------------------

// ISC string literal body -> JS string. Handles the escapes the ISC grammar
// knows (\n \t \r \" \' \\ \u{...} \uXXXX \xXX) and passes anything else
// through verbatim.
export function unescapeIsc(body) {
  let out = "";
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (c !== "\\") {
      out += c;
      continue;
    }
    const n = body[++i];
    if (n === undefined) break;
    switch (n) {
      case "n": out += "\n"; break;
      case "t": out += "\t"; break;
      case "r": out += "\r"; break;
      case '"': out += '"'; break;
      case "'": out += "'"; break;
      case "\\": out += "\\"; break;
      case "u": {
        if (body[i + 1] === "{") {
          const end = body.indexOf("}", i + 2);
          if (end < 0) { out += "u"; break; }
          const hex = body.slice(i + 2, end);
          const cp = parseInt(hex, 16);
          i = end;
          if (Number.isFinite(cp) && cp >= 0 && cp <= 0x10ffff) {
            try { out += String.fromCodePoint(cp); } catch { /* keep raw */ }
          }
        } else {
          const hex = body.slice(i + 1, i + 5);
          const cp = parseInt(hex, 16);
          if (Number.isFinite(cp) && hex.length === 4) {
            out += String.fromCodePoint(cp);
            i += 4;
          } else out += "u";
        }
        break;
      }
      case "x": {
        const hex = body.slice(i + 1, i + 3);
        const cp = parseInt(hex, 16);
        if (Number.isFinite(cp) && hex.length === 2) {
          out += String.fromCodePoint(cp);
          i += 2;
        } else out += "x";
        break;
      }
      default: out += n;
    }
  }
  return out;
}

// Extract test inputs from a case source: the bare `"in" -> "out"` rows of a
// `tests { }` block. Returns up to `limit` inputs, each truncated to `maxLen`
// characters and flattened to single lines (argv-safe, deterministic across
// all four drivers).
export function extractTestInputs(src, limit = 3, maxLen = 40) {
  const inputs = [];
  const lines = src.split("\n");
  let inTests = false;
  for (const line of lines) {
    const t = line.trim();
    if (t === "tests {") { inTests = true; continue; }
    if (inTests && t === "}") { inTests = false; continue; }
    if (!inTests) continue;
    const m = t.match(/^"((?:[^"\\]|\\.)*)"\s*->/);
    if (!m) continue;
    let input = unescapeIsc(m[1]);
    if (input.includes("\n")) input = input.split("\n")[0];
    if (input.length > maxLen) input = input.slice(0, maxLen);
    inputs.push(input);
    if (inputs.length >= limit) break;
  }
  if (inputs.length === 0) inputs.push("ab");
  return inputs;
}

// ---------------------------------------------------------------------------
// Driver invocation contract
// ---------------------------------------------------------------------------
// Driver spawning lives in run.mjs (campaign) and minimize.mjs (reducer);
// both honor the same contract: driver argv = [<case.isc>, <inputs-json>],
// one JSON line on stdout, exit 0. See DRIVER_ENV above for the runtime
// location env vars (RUBY_LIB / TS_DIST / PY_SRC / ISCRS_BIN).

export function ensureDir(p) {
  mkdirSync(p, { recursive: true });
}
