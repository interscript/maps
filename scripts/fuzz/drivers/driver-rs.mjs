#!/usr/bin/env node
// Fuzz driver (rs leg). Usage: node driver-rs.mjs <case.isc> <inputs-json>
// Wraps the iscrs binary: `parse <file>` for accept/reject (rc stays 0 on
// parse failure — the OK/FAIL line is the signal), `transliterate <stem> ...
// --maps <dir>` per input. Panics (exit 101) and signals map to CRASH.
// An internal per-exec kill switch surfaces as bucket TIMEOUT without
// taking the whole driver down.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";

const ISCRS = process.env.ISCRS_BIN || resolve(import.meta.dirname, "../../../interscript-rs/target/release/iscrs");
const EXEC_KILL_MS = Number(process.env.FUZZ_RS_EXEC_KILL_MS || 20000);

function bucketFor(stderr, exitCode, signal) {
  // iscrs prefixes errors with "error: " (e.g. "error: map logic error: …")
  const s = (stderr || "").replace(/^error: /, "");
  if (/panicked at/.test(stderr || "")) return "CRASH";
  if (signal) return "CRASH";
  if (exitCode === 101 || exitCode === 134 || exitCode === 139) return "CRASH";
  if (s.startsWith("map logic error:")) return "LOGIC";
  if (s.startsWith("dependency cycle:")) return "LOGIC";
  if (s.startsWith("unsupported:")) return "UNSUPPORTED";
  if (/^couldn't locate map/.test(s)) return "LOAD";
  if (s.startsWith("parse failed in") || s.startsWith("FAIL")) return "PARSE";
  return "OTHER";
}

function runIscrs(args) {
  const res = spawnSync(ISCRS, args, {
    timeout: EXEC_KILL_MS,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
    killSignal: "SIGKILL",
  });
  if (res.error && res.error.code === "ENOENT") {
    return { timedOut: false, spawnError: `iscrs binary not found: ${ISCRS}`, stdout: "", stderr: "" };
  }
  if (res.error && res.error.code === "ETIMEDOUT") {
    return { timedOut: true, stderr: "", stdout: "" };
  }
  return { timedOut: false, stdout: res.stdout || "", stderr: res.stderr || "", status: res.status, signal: res.signal };
}

const caseFile = process.argv[2];
const inputs = JSON.parse(process.argv[3] || "[]");
const stem = basename(caseFile, ".isc");
const dir = dirname(caseFile);
const result = { runtime: "rs", exec: [] };

// Parse leg. `iscrs parse` exits 0 on accept, 1 on reject (FAIL line), and
// crashes with a panic (101/signal) — the output line is the primary signal.
const p = runIscrs(["parse", caseFile, "--maps", dir]);
if (p.spawnError) {
  result.parse = { status: "ERR", class: "DriverMisconfig", bucket: "OTHER", message: p.spawnError };
} else if (p.timedOut) {
  result.parse = { status: "ERR", class: "Timeout", bucket: "TIMEOUT", message: "iscrs parse exceeded internal kill switch" };
} else if (/^OK\b/m.test(p.stdout)) {
  result.parse = { status: "OK" };
} else if (/^FAIL\b/m.test(p.stdout)) {
  result.parse = { status: "ERR", class: "ParseError", bucket: "PARSE", message: p.stdout.split("\n")[0].slice(0, 200) };
} else if ((p.status === 0 || p.status === 1) && !p.signal) {
  result.parse = { status: "ERR", class: "ParseError", bucket: "PARSE", message: (p.stderr || p.stdout).split("\n")[0].slice(0, 200) || `parse exit ${p.status}` };
} else {
  result.parse = {
    status: "ERR", class: "ProcessCrash", bucket: bucketFor(p.stderr, p.status, p.signal),
    message: (p.stderr || `exit ${p.status}`).split("\n")[0].slice(0, 200),
  };
}

// Exec leg (only when parse accepted).
if (result.parse.status === "OK") {
  for (const input of inputs) {
    const e = runIscrs(["transliterate", stem, input, "--maps", dir, "--stage", "main"]);
    if (e.spawnError) {
      result.exec.push({ input, status: "ERR", class: "DriverMisconfig", bucket: "OTHER", message: e.spawnError });
    } else if (e.timedOut) {
      result.exec.push({ input, status: "ERR", class: "Timeout", bucket: "TIMEOUT", message: "exec exceeded internal kill switch" });
    } else if (e.status === 0) {
      result.exec.push({ input, status: "OK", output: e.stdout.replace(/\n$/, "") });
    } else {
      result.exec.push({
        input,
        status: "ERR",
        class: e.stderr.includes("panicked at") ? "Panic" : "IscrsError",
        bucket: bucketFor(e.stderr, e.status, e.signal),
        message: (e.stderr || `exit ${e.status}`).split("\n")[0].replace(/^error: /, "").slice(0, 200),
      });
    }
  }
}

console.log(JSON.stringify(result));
