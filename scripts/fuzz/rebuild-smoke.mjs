// Rebuilds the committed smoke corpus (scripts/fuzz/smoke-cases/).
//
// Generates a seeded candidate pool, runs it through every AVAILABLE
// runtime, and keeps the first N cases that classify agree-or-known — the
// committed green baseline smoke.mjs enforces. Re-run whenever the runtime
// set changes materially (e.g. after a parity fix lands) to refresh the
// baseline; any case that regresses afterwards turns smoke red.
//
// Usage: node rebuild-smoke.mjs [--want 200] [--pool 420] [--seed 20261120]

import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync, readdirSync, cpSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { ensureDir, FUZZ_DIR } from "./lib.mjs";
import { classify } from "./classify.mjs";

const HERE = fileURLToPath(new URL(".", import.meta.url));

function parseArgs(argv) {
  const opts = { want: 200, pool: 420, seed: 20261120 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--want") opts.want = Number(argv[++i]);
    else if (a === "--pool") opts.pool = Number(argv[++i]);
    else if (a === "--seed") opts.seed = Number(argv[++i]);
    else throw new Error(`unknown flag ${a}`);
  }
  return opts;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const work = "/tmp/isc-fuzz-smoke-rebuild";
  rmSync(work, { recursive: true, force: true });
  ensureDir(work);

  // 1. Generate the candidate pool (mutation + grammar mix).
  const gen = spawnSync(process.execPath, [
    join(FUZZ_DIR, "generate.mjs"),
    "--out", work,
    "--seed", String(opts.seed),
    "--mutation", String(Math.round(opts.pool * 0.75)),
    "--grammar", String(opts.pool - Math.round(opts.pool * 0.75)),
  ], { stdio: "inherit" });
  if (gen.status !== 0) process.exit(2);

  // 2. Run all available runtimes over the pool.
  const resultsPath = join(work, "results.jsonl");
  const run = spawnSync(process.execPath, [
    join(FUZZ_DIR, "run.mjs"),
    "--cases", join(work, "cases"),
    "--out", resultsPath,
    "--timeout", "45000",
    "--jobs", "6",
  ], { stdio: "inherit", env: { ...process.env } });
  if (run.status !== 0) process.exit(2);

  // 3. Keep agree/known cases in generation order until want is reached.
  const { findings } = classify(resultsPath, join(work, "cases"));
  const bad = new Set(findings.filter((f) => f.classification === "FINDING").map((f) => f.case));
  const manifest = JSON.parse(readFileSync(join(work, "manifest.json"), "utf8"));
  const keep = manifest.cases.map((c) => c.id).filter((id) => !bad.has(id)).slice(0, opts.want);
  console.log(`pool=${manifest.cases.length} findings=${bad.size} kept=${keep.length}`);

  // 4. Rewrite the committed smoke-cases dir.
  const outDir = join(FUZZ_DIR, "smoke-cases");
  if (existsSync(outDir)) rmSync(outDir, { recursive: true });
  mkdirSync(outDir, { recursive: true });
  for (const id of keep) {
    cpSync(join(work, "cases", id), join(outDir, id), { recursive: true });
  }
  writeFileSync(
    join(outDir, "manifest.json"),
    JSON.stringify({ seed: opts.seed, pool: opts.pool, want: opts.want, kept: keep, rebuiltWith: "rebuild-smoke.mjs" }, null, 2) + "\n",
  );
  rmSync(work, { recursive: true, force: true });
  console.log(`smoke corpus rebuilt: ${keep.length} cases -> ${outDir}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
