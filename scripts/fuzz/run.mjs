// Differential-fuzz runner (WO20, maps#284).
//
// Runs every case through every requested runtime driver with a per-case
// timeout, applying the harness-boundary UTF-8 normalization, and writes
// one JSON line per (case, runtime) observation:
//   {"case":id,"runtime":rt,"status":...,"parse":{...},"exec":[...]}
//
// Usage:
//   node run.mjs --cases <dir> --out <results.jsonl> [--runtimes ruby,ts,py,rs]
//        [--jobs 6] [--timeout 45000] [--limit N] [--case ID]

import { readdirSync, readFileSync, statSync, existsSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { spawn } from "node:child_process";
import { extractTestInputs, ensureDir, DRIVER_ENV, FUZZ_DIR } from "./lib.mjs";

function parseArgs(argv) {
  const opts = {
    cases: null,
    out: "results.jsonl",
    runtimes: ["ruby", "ts", "py", "rs"],
    jobs: 6,
    timeout: 45_000,
    limit: 0,
    caseId: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--cases") opts.cases = argv[++i];
    else if (a === "--out") opts.out = argv[++i];
    else if (a === "--runtimes") opts.runtimes = argv[++i].split(",");
    else if (a === "--jobs") opts.jobs = Number(argv[++i]);
    else if (a === "--timeout") opts.timeout = Number(argv[++i]);
    else if (a === "--limit") opts.limit = Number(argv[++i]);
    else if (a === "--case") opts.caseId = argv[++i];
    else throw new Error(`unknown flag ${a}`);
  }
  if (!opts.cases) throw new Error("--cases is required");
  return opts;
}

function discoverCases(casesDir) {
  const out = [];
  for (const e of readdirSync(casesDir)) {
    const p = join(casesDir, e);
    try {
      if (statSync(p).isDirectory() && existsSync(join(p, "map.isc"))) {
        out.push({ id: e, file: join(p, "map.isc") });
      }
    } catch { /* not a dir */ }
  }
  out.sort((a, b) => a.id.localeCompare(b.id));
  return out;
}

// ---------------------------------------------------------------------------
// Driver spawn (async). Contract: driver prints one JSON line; exit 0.
// Anything else is a hard result recorded by the runner:
//   TIMEOUT — driver exceeded the per-case wall clock (a hang finding)
//   CRASH   — nonzero exit / no JSON line / signal
// ---------------------------------------------------------------------------

function spawnDriver(runtime, caseFile, inputs, timeoutMs) {
  const drivers = {
    ruby: join(FUZZ_DIR, "drivers", "driver-ruby.rb"),
    ts: join(FUZZ_DIR, "drivers", "driver-ts.mjs"),
    py: join(FUZZ_DIR, "drivers", "driver-py.py"),
    rs: join(FUZZ_DIR, "drivers", "driver-rs.mjs"),
  };
  const cmd = { ruby: "ruby", ts: process.execPath, py: "python3", rs: process.execPath }[runtime];
  const args = [drivers[runtime], caseFile, JSON.stringify(inputs)];
  const env = {};
  for (const [k, v] of Object.entries(DRIVER_ENV[runtime])) env[k] = process.env[k] || resolve(FUZZ_DIR, v);

  return new Promise((done) => {
    const started = Date.now();
    const child = spawn(cmd, args, { env: { ...process.env, ...env } });
    let stdout = "";
    let stderr = "";
    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      child.kill("SIGKILL");
    }, timeoutMs);
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => {
      if (stderr.length < 4000) stderr += d;
    });
    const finish = (result) => {
      clearTimeout(timer);
      done(result);
    };
    child.on("error", (e) => finish({ runtime, status: "CRASH", ms: Date.now() - started, stderr: String(e.message) }));
    child.on("close", (code, signal) => {
      const ms = Date.now() - started;
      if (killed) return finish({ runtime, status: "TIMEOUT", ms });
      const line = stdout.split("\n").find((l) => l.trim().startsWith("{"));
      if (line) {
        try {
          const parsed = JSON.parse(line);
          if (code === 0) return finish({ runtime, status: "OK", ms, ...parsed });
        } catch { /* fall through */ }
      }
      return finish({
        runtime,
        status: "CRASH",
        ms,
        exitCode: code,
        signal,
        stderr: stderr.slice(-600),
      });
    });
  });
}

// Harness-boundary normalization: cases may contain invalid UTF-8 (byte-flip
// mutations). Every driver must see the IDENTICAL string, so invalid cases
// get a sanitized copy in a scratch dir; valid cases pass through as-is.
function makeNormalizer() {
  const scratch = mkdtempSync(join("/tmp", "isc-fuzz-run-"));
  const cache = new Map();
  function caseFileFor(c) {
    if (cache.has(c.id)) return cache.get(c.id);
    const buf = readFileSync(c.file);
    let file = c.file;
    if (!Buffer.from(buf.toString("utf8"), "utf8").equals(buf)) {
      const dir = join(scratch, c.id);
      ensureDir(dir);
      file = join(dir, "map.isc");
      writeFileSync(file, Buffer.from(buf.toString("utf8"), "utf8"));
    }
    cache.set(c.id, file);
    return file;
  }
  caseFileFor.cleanup = () => rmSync(scratch, { recursive: true, force: true });
  return caseFileFor;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  let cases = discoverCases(opts.cases);
  if (opts.caseId) cases = cases.filter((c) => c.id === opts.caseId);
  if (opts.limit > 0) cases = cases.slice(0, opts.limit);
  if (cases.length === 0) {
    console.error("no cases found");
    process.exit(2);
  }
  ensureDir(dirname(resolve(opts.out)));
  const outPath = resolve(opts.out);
  const caseFileFor = makeNormalizer();
  const inputsCache = new Map();
  const inputsFor = (c) => {
    if (!inputsCache.has(c.id)) inputsCache.set(c.id, extractTestInputs(readFileSync(c.file, "utf8")));
    return inputsCache.get(c.id);
  };

  const results = [];
  const total = cases.length * opts.runtimes.length;
  let done = 0;
  const t0 = Date.now();
  let next = 0;

  async function worker() {
    while (next < cases.length) {
      const i = next++;
      const c = cases[i];
      const file = caseFileFor(c);
      const inputs = inputsFor(c);
      for (const rt of opts.runtimes) {
        const r = await spawnDriver(rt, file, inputs, opts.timeout);
        results.push({ case: c.id, ...r });
        done++;
        if (done % 200 === 0 || done === total) {
          const rate = done / ((Date.now() - t0) / 1000);
          console.error(`[run] ${done}/${total} (${rate.toFixed(1)}/s)`);
        }
      }
    }
  }

  await Promise.all(Array.from({ length: Math.max(1, opts.jobs) }, () => worker()));
  results.sort((a, b) => (a.case === b.case ? a.runtime.localeCompare(b.runtime) : a.case.localeCompare(b.case)));
  writeFileSync(outPath, results.map((r) => JSON.stringify(r)).join("\n") + "\n");
  caseFileFor.cleanup();

  const byStatus = {};
  for (const r of results) byStatus[r.status] = (byStatus[r.status] || 0) + 1;
  console.log(`ran ${total} observations over ${cases.length} cases -> ${outPath}`);
  console.log(`statuses: ${JSON.stringify(byStatus)}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
