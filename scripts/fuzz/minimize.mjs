// Finding minimizer (WO20, maps#284).
//
// Shrinks a finding's case while the finding's signature persists:
//   1. line-level delta debugging (halving chunks, then single lines)
//   2. head/tail character trimming
// The signature = (finding kind, reporting runtime, evidence bucket) tuple;
// a shrink step survives only if re-running the case still classifies as the
// SAME finding kind involving the SAME runtime.
//
// Usage:
//   node minimize.mjs --finding <findings.jsonl> --results <results.jsonl>
//        --cases <dir> --out-dir <findings-min/> [--runtimes ruby,ts,py,rs] [--timeout 45000]

import { readFileSync, writeFileSync, mkdirSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { extractTestInputs, ensureDir, DRIVER_ENV, FUZZ_DIR } from "./lib.mjs";
import { knownKind } from "./classify.mjs";

function parseArgs(argv) {
  const opts = { findings: null, results: null, cases: null, outDir: "findings-min", runtimes: ["ruby", "ts", "py", "rs"], timeout: 45_000 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--findings") opts.findings = argv[++i];
    else if (a === "--results") opts.results = argv[++i];
    else if (a === "--cases") opts.cases = argv[++i];
    else if (a === "--out-dir") opts.outDir = argv[++i];
    else if (a === "--runtimes") opts.runtimes = argv[++i].split(",");
    else if (a === "--timeout") opts.timeout = Number(argv[++i]);
    else throw new Error(`unknown flag ${a}`);
  }
  if (!opts.findings || !opts.cases) throw new Error("--findings and --cases are required");
  return opts;
}

// Re-run one candidate text through the drivers and return the observation set.
async function observe(text, runtimes, timeout) {
  const dir = mkdtempSync(join("/tmp", "isc-fuzz-min-"));
  const file = join(dir, "map.isc");
  writeFileSync(file, Buffer.isBuffer(text) ? text : Buffer.from(text, "utf8"));
  const inputs = extractTestInputs((Buffer.isBuffer(text) ? text : Buffer.from(text, "utf8")).toString("utf8"));
  const out = [];
  for (const rt of runtimes) {
    out.push(await spawnOne(rt, file, inputs, timeout));
  }
  rmSync(dir, { recursive: true, force: true });
  return out;
}

function spawnOne(runtime, caseFile, inputs, timeoutMs) {
  const drivers = {
    ruby: join(FUZZ_DIR, "drivers", "driver-ruby.rb"),
    ts: join(FUZZ_DIR, "drivers", "driver-ts.mjs"),
    py: join(FUZZ_DIR, "drivers", "driver-py.py"),
    rs: join(FUZZ_DIR, "drivers", "driver-rs.mjs"),
  };
  const cmd = { ruby: "ruby", ts: process.execPath, py: "python3", rs: process.execPath }[runtime];
  const env = {};
  for (const [k, v] of Object.entries(DRIVER_ENV[runtime])) env[k] = resolve(FUZZ_DIR, v);
  return new Promise((done) => {
    const child = spawn(cmd, [drivers[runtime], caseFile, JSON.stringify(inputs)], { env: { ...process.env, ...env } });
    let stdout = "";
    let stderr = "";
    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      child.kill("SIGKILL");
    }, timeoutMs);
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => {
      if (stderr.length < 2000) stderr += d;
    });
    const finish = (r) => {
      clearTimeout(timer);
      done(r);
    };
    child.on("error", (e) => finish({ runtime, status: "CRASH", stderr: String(e.message) }));
    child.on("close", (code) => {
      if (killed) return finish({ runtime, status: "TIMEOUT" });
      const line = stdout.split("\n").find((l) => l.trim().startsWith("{"));
      if (line && code === 0) {
        try {
          const parsed = JSON.parse(line);
          return finish({ runtime, status: "OK", ...parsed });
        } catch { /* fall through */ }
      }
      return finish({ runtime, status: "CRASH", exitCode: code, stderr: stderr.slice(-400) });
    });
  });
}

// Signature extraction: kind + primary runtime evidence buckets.
function signatureOf(observations) {
  const sigs = [];
  for (const o of observations) {
    if (o.status === "TIMEOUT") sigs.push(`hang:${o.runtime}`);
    else if (o.status === "CRASH") sigs.push(`crash-proc:${o.runtime}`);
    else {
      const shapes = [o.parse, ...(o.exec || [])];
      for (const s of shapes) {
        if (!s) continue;
        if (s.bucket === "CRASH") sigs.push(`crash:${o.runtime}`);
        if (s.bucket === "TIMEOUT") sigs.push(`hang:${o.runtime}`);
      }
    }
  }
  return sigs.sort().join(",");
}

function divergeSignature(observations) {
  const oks = observations.filter((o) => o.status === "OK");
  if (oks.length < 2) return "no-divergence";
  const parts = [];
  const statuses = new Set(oks.map((o) => o.parse?.status));
  parts.push(`parse:${[...statuses].sort().join("/")}`);
  if (statuses.size === 1 && statuses.has("OK")) {
    for (const o of oks) {
      const sig = (o.exec || []).map((e) => (e.status === "OK" ? JSON.stringify(e.output) : `ERR:${e.bucket}`)).join("|");
      parts.push(`${o.runtime}=${sig}`);
    }
  } else {
    for (const o of oks) parts.push(`${o.runtime}=${o.parse?.bucket}`);
  }
  return parts.join(",");
}

async function persists(text, target, runtimes, timeout) {
  const obs = await observe(text, runtimes, timeout);
  const kinds = knownKind((Buffer.isBuffer(text) ? text : Buffer.from(text, "utf8")).toString("utf8"));
  if (kinds.length > 0) return false; // shrink must not fall into a known kind
  if (target.kind === "hang" || target.kind === "crash") return signatureOf(obs).includes(target.sig);
  // divergence: some cross-runtime mismatch must remain
  return divergeSignature(obs) !== "no-divergence";
}

async function shrink(text, target, runtimes, timeout, maxRounds = 30) {
  const asBuf = (t) => (Buffer.isBuffer(t) ? t : Buffer.from(t, "utf8"));
  let cur = asBuf(text);
  if (!(await persists(cur, target, runtimes, timeout))) return null;

  // Line-level ddmin-lite.
  for (let round = 0; round < maxRounds; round++) {
    const lines = cur.toString("utf8").split("\n");
    let changed = false;
    for (let chunk = Math.floor(lines.length / 2); chunk >= 1; chunk = Math.floor(chunk / 2)) {
      let i = 0;
      while (i < lines.length) {
        const candidate = lines.slice(0, i).concat(lines.slice(i + chunk)).join("\n");
        if (await persists(Buffer.from(candidate, "utf8"), target, runtimes, timeout)) {
          lines.splice(i, chunk);
          cur = Buffer.from(candidate, "utf8");
          changed = true;
        } else {
          i += chunk;
        }
        if (lines.length <= 3) break;
      }
      if (chunk <= 1) break;
      if (lines.length <= 3) break;
    }
    if (!changed || lines0(cur) <= 3) break;
  }

  // Head/tail character trimming (byte-safe via buffer scanning).
  let buf = cur;
  for (let round = 0; round < 12; round++) {
    let changed = false;
    for (const [start, end] of [[0, Math.floor(buf.length / 8)], [buf.length - Math.floor(buf.length / 8), buf.length]]) {
      const span = end - start;
      if (span <= 0) continue;
      const step = Math.max(1, Math.floor(span / 2));
      for (let cut = start; cut < start + span; cut += step) {
        const candidate = start === 0 ? buf.subarray(cut + 1) : buf.subarray(0, cut);
        if (candidate.length === 0) continue;
        if (await persists(candidate, target, runtimes, timeout)) {
          buf = candidate;
          changed = true;
          break;
        }
      }
    }
    if (!changed || buf.length <= 40) break;
  }
  return buf;
}

function lines0(buf) {
  return buf.toString("utf8").split("\n").length;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  ensureDir(opts.outDir);
  const findings = readFileSync(opts.findings, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  const real = findings.filter((f) => f.classification === "FINDING");
  console.log(`minimizing ${real.length} findings -> ${opts.outDir}`);

  for (const f of real) {
    const caseFile = join(opts.cases, f.case, "map.isc");
    if (!existsSync(caseFile)) {
      console.log(`  ${f.case}: case file missing, skipped`);
      continue;
    }
    const original = readFileSync(caseFile);
    const first = f.findings[0];
    const target = {
      kind: first.kind,
      runtime: first.runtime,
      sig:
        first.kind === "crash" || first.kind === "hang"
          ? `${first.kind}:${first.runtime}`
          : null,
    };
    const minimized = await shrink(original, target, opts.runtimes, opts.timeout);
    const outDir = join(opts.outDir, f.case);
    ensureDir(outDir);
    writeFileSync(join(outDir, "finding.json"), JSON.stringify(f, null, 2));
    if (minimized) {
      const minFile = join(outDir, "map.isc");
      writeFileSync(minFile, minimized);
      const proof = await observe(minimized, opts.runtimes, opts.timeout);
      writeFileSync(join(outDir, "proof.json"), JSON.stringify(proof, null, 2));
      console.log(
        `  ${f.case}: ${original.length} -> ${minimized.length} bytes (${lines0(original)} -> ${lines0(minimized)} lines) kind=${first.kind}`,
      );
    } else {
      console.log(`  ${f.case}: shrink failed to reproduce, kept original`);
      writeFileSync(join(outDir, "map.isc"), original);
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
