// CI-able seeded smoke mode (WO20, maps#284).
//
// The committed smoke-cases/ directory holds a small seeded corpus (~200
// cases). Smoke green = every case classifies as agree or known-kind across
// every AVAILABLE runtime; any crash / hang / unexplained divergence fails
// the run (exit 1). Runtimes that lack a locally-built engine are skipped
// with a notice, so maps-CI (ruby + ts only) stays green while local runs
// cover all four.
//
// Usage:
//   node smoke.mjs [--cases smoke-cases] [--runtimes ruby,ts,py,rs]
//        [--timeout 45000] [--jobs 6]

import { existsSync, readdirSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { classify } from "./classify.mjs";

const FUZZ_DIR = fileURLToPath(new URL(".", import.meta.url));

function parseArgs(argv) {
  const opts = { cases: join(FUZZ_DIR, "smoke-cases"), runtimes: ["ruby", "ts", "py", "rs"], timeout: 45_000, jobs: 6 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--cases") opts.cases = argv[++i];
    else if (a === "--runtimes") opts.runtimes = argv[++i].split(",");
    else if (a === "--timeout") opts.timeout = Number(argv[++i]);
    else if (a === "--jobs") opts.jobs = Number(argv[++i]);
    else throw new Error(`unknown flag ${a}`);
  }
  return opts;
}

// Runtime availability probing (cheap): can the driver command even start?
function available(runtimes) {
  const envPaths = {
    ruby: process.env.RUBY_LIB || resolve(FUZZ_DIR, "../../../interscript-ruby/lib"),
    ts: process.env.TS_DIST || resolve(FUZZ_DIR, "../../../interscript-ts/dist"),
    py: process.env.PY_SRC || resolve(FUZZ_DIR, "../../../interscript-py/src"),
    rs: process.env.ISCRS_BIN || resolve(FUZZ_DIR, "../../../interscript-rs/target/release/iscrs"),
  };
  const out = [];
  for (const rt of runtimes) {
    const p = envPaths[rt];
    const ok = rt === "rs" ? existsSync(p) : existsSync(p);
    if (!ok) console.error(`[smoke] ${rt} unavailable (missing ${p}) — skipping`);
    else out.push(rt);
  }
  return out;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const runtimes = available(opts.runtimes);
  if (runtimes.length < 2) {
    console.error("[smoke] fewer than two runtimes available — nothing to compare");
    process.exit(2);
  }
  console.error(`[smoke] runtimes: ${runtimes.join(",")}`);

  const casesDir = opts.cases;
  if (!existsSync(casesDir)) {
    console.error(`[smoke] cases dir missing: ${casesDir}`);
    process.exit(2);
  }
  const nCases = readdirSync(casesDir).filter((e) => existsSync(join(casesDir, e, "map.isc"))).length;

  const resultsPath = join("/tmp", `isc-fuzz-smoke-${process.pid}.jsonl`);
  const run = spawnSync(process.execPath, [
    join(FUZZ_DIR, "run.mjs"),
    "--cases", casesDir,
    "--out", resultsPath,
    "--runtimes", runtimes.join(","),
    "--timeout", String(opts.timeout),
    "--jobs", String(opts.jobs),
  ], { stdio: "inherit" });
  if (run.status !== 0) {
    console.error("[smoke] runner failed");
    process.exit(2);
  }

  const { findings, stats } = classify(resultsPath, casesDir);
  const real = findings.filter((f) => f.classification === "FINDING");
  console.log(`[smoke] cases=${stats.cases} agree=${stats.agree} known=${stats.known} findings=${stats.findings}`);
  if (real.length > 0) {
    console.log(`[smoke] FAIL — unexplained findings:`);
    for (const f of real) {
      console.log(`  ${f.case}: ${f.kinds.join(",")} — ${f.findings.map((x) => `${x.kind}[${x.runtime}]: ${x.detail.slice(0, 120)}`).join("; ")}`);
    }
    rmSync(resultsPath, { force: true });
    process.exit(1);
  }
  rmSync(resultsPath, { force: true });
  console.log("[smoke] PASS");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
