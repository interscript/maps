// Finding classifier for the ISC differential fuzz harness (WO20, maps#284).
//
// Reads a results.jsonl produced by run.mjs, groups observations by case,
// and emits findings classified as:
//   crash       — any runtime hit the CRASH bucket (parse or exec) or died
//                 at the process level, not covered by a known-kind signature
//   hang        — any runtime hit a TIMEOUT
//   divergence  — cross-runtime mismatch in accept/reject, canonical error
//                 bucket, or exec output, not covered by a known-kind signature
//
// Known-kind signatures come from docs/parity/README.md (audit G1-G12 plus
// the battery rows); those divergences are documented design facts, not
// findings. Every classification records WHY (kind + signature) so triage
// can re-audit.
//
// Usage: node classify.mjs --results results.jsonl --cases <dir> --out findings.jsonl [--summary summary.md]

import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

function parseArgs(argv) {
  const opts = { results: null, cases: null, out: "findings.jsonl", summary: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--results") opts.results = argv[++i];
    else if (a === "--cases") opts.cases = argv[++i];
    else if (a === "--out") opts.out = argv[++i];
    else if (a === "--summary") opts.summary = argv[++i];
    else throw new Error(`unknown flag ${a}`);
  }
  if (!opts.results || !opts.cases) throw new Error("--results and --cases are required");
  return opts;
}

// ---------------------------------------------------------------------------
// Known-kind signatures (docs/parity/README.md). Each detector inspects the
// case source and returns a G-number when the case exercises a documented
// design divergence. Signature matching is on case CONTENT, not on which
// runtime did what, so it stays valid as runtimes move.
// ---------------------------------------------------------------------------

export function knownKind(src) {
  const kinds = [];

  // G1 — capture/ref inside parallel blocks (corrupt output ts/py, ruby crash).
  if (captureInParallel(src)) kinds.push("G1");

  // G3 — unresolved alias compiles to empty matcher in ts/py (audit version);
  // treated as known regardless of current per-runtime behavior.
  if (hasUnresolvedAliasRef(src)) kinds.push("G3");

  // G4 — missing main stage (ruby accidental crash vs silent no-op vs named).
  if (missingMainStage(src)) kinds.push("G4");

  // G5 — `use` inside sequence/parallel blocks (only rs implements spec 3.2).
  if (useInsideBlock(src)) kinds.push("G5");

  // G6 — fn-literal keyword in from position (three-way).
  if (fnLiteralInFrom(src)) kinds.push("G6");

  // G7 — duplicate ruleset definitions (only py rejects; rs merge semantics).
  if (duplicateRuleset(src)) kinds.push("G7");

  // G8 — fn literals upcase/reverse/strip/swapcase as directives (ruby gap).
  if (fnLiteralDirective(src)) kinds.push("G8");

  // G9 — ruleset cycle error-class surface (all reject; classes differ).
  if (looksLikeRulesetCycle(src)) kinds.push("G9");

  // ML funcalls (rababa/secryst) — env-dependent battery rows (ml-*).
  if (/\b(rababa|secryst)\b/.test(src)) kinds.push("ML");

  // G12 — dependency loader asymmetry: the harness never provides the
  // dependency document, so dependency-bearing cases exercise the
  // documented loader-surface differences (ruby/rs reject at load, ts at
  // expansion, py folds at parse), not new divergences.
  if (hasDependencyDecl(src)) kinds.push("G12");

  return kinds;
}

function hasDependencyDecl(src) {
  return /^dependency\s+/m.test(src);
}

function captureInParallel(src) {
  const lines = src.split("\n");
  let depth = 0;
  let inParallel = 0;
  for (const line of lines) {
    const t = line.trim();
    if (t === "parallel {") inParallel += 1;
    else if (t === "}" && inParallel > 0 && depth === 0) inParallel -= 1;
    if (inParallel > 0 && /\b(capture|ref)\s*\(/.test(t)) return true;
    // crude brace depth tracking for nested blocks inside parallel
    for (const ch of t) {
      if (ch === "{") depth += 1;
      else if (ch === "}") depth = Math.max(0, depth - 1);
    }
  }
  return false;
}

function aliasDecls(src) {
  const names = new Set();
  // alias declarations live in `aliases { name = expr }` blocks
  let inAliases = false;
  for (const line of src.split("\n")) {
    const t = line.trim();
    if (t === "aliases {") { inAliases = true; continue; }
    if (inAliases && t === "}") { inAliases = false; continue; }
    if (inAliases) {
      const m = t.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=/);
      if (m) names.add(m[1]);
    }
  }
  return names;
}

const FN_KEYWORDS = new Set(["upcase", "downcase", "title_case", "reverse", "strip", "swapcase"]);

function hasUnresolvedAliasRef(src) {
  const decls = aliasDecls(src);
  for (const line of src.split("\n")) {
    const m = line.trim().match(/^sub\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:"|ref\(|\{)/);
    if (!m) continue;
    const name = m[1];
    if (FN_KEYWORDS.has(name)) continue; // fn literal (G6), not an alias
    if (!decls.has(name)) return true;
  }
  return false;
}

function stageDecls(src) {
  const names = [];
  for (const line of src.split("\n")) {
    const m = line.trim().match(/^stage\s+([A-Za-z_][A-Za-z0-9_]*)/);
    if (m) names.push(m[1]);
  }
  return names;
}

function missingMainStage(src) {
  const stages = stageDecls(src);
  if (stages.length === 0) return false; // no stage decls at all — different surface
  return !stages.includes("main");
}

function useInsideBlock(src) {
  const lines = src.split("\n");
  let depth = 0;
  for (const line of lines) {
    const t = line.trim();
    if (depth > 0 && /^use\s+[A-Za-z_]/.test(t)) return true;
    for (const ch of t) {
      if (ch === "{") depth += 1;
      else if (ch === "}") depth = Math.max(0, depth - 1);
    }
  }
  return false;
}

function fnLiteralInFrom(src) {
  return /^\s*sub\s+(upcase|downcase|title_case|reverse|strip|swapcase)(\s|$)/m.test(src);
}

function fnLiteralDirective(src) {
  const lines = src.split("\n");
  for (const line of lines) {
    const t = line.trim();
    if (/^(upcase|reverse|strip|swapcase)(\s|$)/.test(t) && !/^sub\b/.test(t) && !t.startsWith("#")) return true;
    // to-funcall position: `sub "a" <fn>`
    if (/^sub\s+"(?:[^"\\]|\\.)*"\s+(upcase|reverse|strip|swapcase)(\s|$)/.test(t)) return true;
  }
  return false;
}

function duplicateRuleset(src) {
  const seen = new Map();
  for (const line of src.split("\n")) {
    const m = line.trim().match(/^ruleset\s+([A-Za-z_][A-Za-z0-9_]*)/);
    if (!m) continue;
    seen.set(m[1], (seen.get(m[1]) || 0) + 1);
  }
  for (const n of seen.values()) if (n > 1) return true;
  return false;
}

function looksLikeRulesetCycle(src) {
  // ruleset X whose body uses X (self), or use chain a->b->a — the corpus
  // cases we generate are small; self-use is the common mutation artifact.
  const uses = new Map();
  let current = null;
  for (const line of src.split("\n")) {
    const decl = line.trim().match(/^ruleset\s+([A-Za-z_][A-Za-z0-9_]*)/);
    if (decl) { current = decl[1]; uses.set(current, []); continue; }
    if (current === null) continue;
    const use = line.trim().match(/^stage\b/);
    if (use) { current = null; continue; }
    const u = line.trim().match(/^use\s+([A-Za-z_][A-Za-z0-9_]*)/);
    if (u && !/override/.test(line)) uses.get(current)?.push(u[1]);
  }
  for (const [from, tos] of uses) {
    for (const to of tos) {
      if (uses.has(to) && uses.get(to).includes(from)) return true;
      if (to === from) return true;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Comparison
// ---------------------------------------------------------------------------

function execSignature(obs) {
  if (!obs.exec || obs.exec.length === 0) return "no-exec";
  return obs.exec
    .map((e) => (e.status === "OK" ? `OK:${JSON.stringify(e.output)}` : `ERR:${e.bucket}`))
    .join("|");
}

function compareCase(observations, kinds) {
  const oks = observations.filter((o) => o.status === "OK");
  const findings = [];

  for (const o of observations) {
    if (o.status === "TIMEOUT") findings.push({ kind: "hang", runtime: o.runtime, detail: "driver exceeded per-case timeout" });
    if (o.status === "CRASH") {
      findings.push({
        kind: "crash",
        runtime: o.runtime,
        detail: `process-level crash: exit=${o.exitCode} signal=${o.signal || ""} ${o.stderr || ""}`.slice(0, 400),
      });
    }
    if (o.status === "OK") {
      for (const leg of ["parse", ...(o.exec || [])]) {
        const shape = leg === "parse" ? o.parse : leg;
        if (shape && shape.bucket === "CRASH") {
          findings.push({
            kind: "crash",
            runtime: o.runtime,
            detail: `${leg === "parse" ? "parse" : `exec(${shape.input})`} CRASH bucket: ${shape.class}: ${shape.message}`.slice(0, 400),
          });
        }
        if (shape && shape.bucket === "TIMEOUT") {
          findings.push({ kind: "hang", runtime: o.runtime, detail: `${leg === "parse" ? "parse" : `exec(${shape.input})`} TIMEOUT`.slice(0, 400) });
        }
      }
    }
  }

  // Cross-runtime comparison (only meaningful with >=2 usable observations).
  if (oks.length >= 2) {
    const parseShapes = oks.map((o) => ({ rt: o.runtime, s: o.parse }));
    const statuses = new Set(parseShapes.map((p) => p.s?.status));
    if (statuses.size > 1) {
      findings.push({
        kind: "divergence",
        runtime: "*",
        detail: `accept/reject differs: ${parseShapes.map((p) => `${p.rt}=${p.s?.status}(${p.s?.bucket})`).join(" ")}`,
      });
    } else if (oks.every((o) => o.parse?.status === "OK")) {
      const buckets = new Set(oks.map((o) => execSignature(o)));
      if (buckets.size > 1) {
        const detail = oks.map((o) => `${o.runtime}: ${execSignature(o).slice(0, 150)}`).join(" || ");
        findings.push({ kind: "divergence", runtime: "*", detail: `exec/parse-output differs: ${detail}`.slice(0, 500) });
      }
    } else {
      // all reject: bucket agreement required (error-class divergence)
      const buck = new Set(parseShapes.map((p) => `${p.s?.bucket}`));
      if (buck.size > 1) {
        const detail = parseShapes.map((p) => `${p.rt}=${p.s?.bucket}(${p.s?.class})`).join(" ");
        findings.push({ kind: "divergence", runtime: "*", detail: `reject-class differs: ${detail}` });
      }
    }
  }

  // Filter known kinds.
  const unexplained = [];
  const explained = [];
  for (const f of findings) {
    if (kinds.length > 0) explained.push({ ...f, known: kinds });
    else unexplained.push(f);
  }
  return { unexplained, explained };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function classify(resultsPath, casesDir) {
  const lines = readFileSync(resultsPath, "utf8").split("\n").filter(Boolean);
  const byCase = new Map();
  for (const line of lines) {
    const obs = JSON.parse(line);
    if (!byCase.has(obs.case)) byCase.set(obs.case, []);
    byCase.get(obs.case).push(obs);
  }

  const findings = [];
  const stats = {
    cases: byCase.size,
    agree: 0,
    known: 0,
    findings: 0,
    byKind: { crash: 0, hang: 0, divergence: 0 },
    byRuntime: {},
    timeouts: 0,
  };

  for (const [caseId, observations] of byCase) {
    let src = "";
    try {
      src = readFileSync(join(casesDir, caseId, "map.isc"), "utf8");
    } catch {
      src = "";
    }
    const kinds = knownKind(src);
    const { unexplained, explained } = compareCase(observations, kinds);
    if (unexplained.length === 0 && explained.length === 0) {
      stats.agree += 1;
      continue;
    }
    if (unexplained.length === 0) {
      stats.known += 1;
      findings.push({ case: caseId, classification: "known", kinds, findings: explained });
      continue;
    }
    stats.findings += 1;
    const kindsSet = new Set();
    for (const f of unexplained) {
      stats.byKind[f.kind] = (stats.byKind[f.kind] || 0) + 1;
      kindsSet.add(f.kind);
      if (f.runtime !== "*") stats.byRuntime[f.runtime] = (stats.byRuntime[f.runtime] || 0) + 1;
    }
    findings.push({
      case: caseId,
      classification: "FINDING",
      kinds: [...kindsSet],
      findings: unexplained,
      alsoKnown: explained.length > 0 ? explained : undefined,
    });
  }

  // Timeouts counted regardless of known-status
  for (const [, observations] of byCase) {
    for (const o of observations) if (o.status === "TIMEOUT") stats.timeouts += 1;
  }
  return { findings, stats };
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const { findings, stats } = classify(opts.results, opts.cases);
  writeFileSync(opts.out, findings.map((f) => JSON.stringify(f)).join("\n") + "\n");

  const findingList = findings.filter((f) => f.classification === "FINDING");
  console.log(`cases: ${stats.cases}  agree: ${stats.agree}  known: ${stats.known}  FINDINGS: ${stats.findings}`);
  console.log(`finding kinds: ${JSON.stringify(stats.byKind)}`);
  console.log(`by runtime: ${JSON.stringify(stats.byRuntime)}`);

  if (opts.summary) {
    const rows = findingList
      .map((f) => `| ${f.case} | ${f.kinds.join(",")} | ${f.findings.map((x) => `${x.kind}[${x.runtime}]`).join(", ")} | ${f.findings[0].detail.slice(0, 120).replace(/\|/g, "\\|")} |`)
      .join("\n");
    const head = `# Fuzz triage (results=${opts.results})\n\ncases ${stats.cases} | agree ${stats.agree} | known ${stats.known} | findings ${stats.findings}\n\nkinds: ${JSON.stringify(stats.byKind)}\n\n| case | finding kinds | evidence | detail |\n|---|---|---|---|\n${rows}\n`;
    writeFileSync(opts.summary, head);
  }
  for (const f of findingList.slice(0, 40)) {
    console.log(`  ${f.case}: ${f.kinds.join(",")} — ${f.findings.map((x) => x.kind).join(",")}`);
  }
  if (findingList.length > 40) console.log(`  ... and ${findingList.length - 40} more (see ${opts.out})`);
}

const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].split("/").pop());
if (isMain) main();
