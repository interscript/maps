#!/usr/bin/env node
// Cross-grammar parse parity harness (ISC-WF-1).
//
// Parses every corpus file (maps/*.isc + libs/*.isc) with TWO independent
// ISC parsers and proves (or refutes) that they agree STRUCTURALLY:
//
//   - TypeScript: parseIsc from a sibling interscript-ts checkout, run via
//     `npx -y tsx`, followed by that repo's own expandDocument() so `use`
//     directives (W1/W2) are resolved by the parser's own semantics.
//   - Python: parse_isc from ../interscript-ruby/interscript-py/src, which
//     expands `use` directives at parse time.
//
// Each parser's document is projected onto one CANONICAL JSON schema by a
// per-parser normalizer (the two IRs render the same source construct
// differently by design — e.g. the Python parser lowers `none` to an empty
// string item and lowers `to`-position function atoms to funcall-inline).
// Where a construct is representable in one parser but NOT the other, or
// renders under a different kind, the harness reports a divergence instead
// of force-passing: the first run is an AUDIT of the four hand-synced
// grammar copies.
//
// Usage:
//   node scripts/parse-parity.mjs [--json <report.json>] [--verbose]
//        [--ts-root <interscript-ts>] [--py-root <interscript-ruby>]
//        [--py-bin <python>] [--only <path-substring>] [--timeout <seconds>]
//
// Defaults: --ts-root ../interscript-ts --py-root ../interscript-ruby
// (sibling checkouts of this repository, never committed here).
// Exit code 1 on any divergence, 2 on harness setup errors.

import { spawn } from "node:child_process"
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, relative, resolve } from "node:path"
import { pathToFileURL } from "node:url"

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const repoRoot = resolve(import.meta.dirname, "..")

function argValue(flag) {
  const i = process.argv.indexOf(flag)
  return i >= 0 ? process.argv[i + 1] : undefined
}

const tsRoot = resolve(repoRoot, argValue("--ts-root") ?? "../interscript-ts")
const pyRoot = resolve(repoRoot, argValue("--py-root") ?? "../interscript-ruby")
const pyBin = argValue("--py-bin") ?? "python3"
const jsonOut = argValue("--json")
const verbose = process.argv.includes("--verbose")
const only = argValue("--only")
const timeoutMs = Number(argValue("--timeout") ?? 600) * 1000

const pySrcRoot = join(pyRoot, "interscript-py", "src")

// ---------------------------------------------------------------------------
// Corpus discovery + dependency index
// ---------------------------------------------------------------------------

// ISC dependency targets reference the corpus FILE STEM (the ts loader's
// `baseUrl + "/" + code + ".isc"` convention), not the declared systemCode.
function discoverCorpus() {
  const all = []
  const depIndex = {}
  for (const sub of ["maps", "libs"]) {
    const dir = join(repoRoot, sub)
    for (const f of readdirSync(dir).sort()) {
      if (!f.endsWith(".isc")) continue
      const abs = join(dir, f)
      all.push({ rel: `${sub}/${f}`, path: abs })
      depIndex[f.slice(0, -4)] = abs
    }
  }
  // The dependency index always covers the WHOLE corpus so a `--only`
  // filtered run can still resolve cross-file `use` directives.
  const files = only ? all.filter((f) => f.rel.includes(only)) : all
  return { files, depIndex }
}

// ---------------------------------------------------------------------------
// Driver subprocesses — one per parser, manifest on stdin, JSONL on stdout
// ---------------------------------------------------------------------------

function runProcess(cmd, args, opts) {
  const timeoutMs = opts.timeoutMs ?? 600_000
  return new Promise((resolvePromise) => {
    const child = spawn(cmd, args, { cwd: opts.cwd, env: { ...process.env, ...opts.env } })
    // Accumulate BUFFERS, decode once: per-chunk string concatenation would
    // replace a multi-byte char split across chunk boundaries with U+FFFD.
    const outChunks = []
    const errChunks = []
    let timedOut = false
    const timer = setTimeout(() => {
      timedOut = true
      child.kill("SIGKILL")
    }, timeoutMs)
    child.stdout.on("data", (d) => outChunks.push(d))
    child.stderr.on("data", (d) => errChunks.push(d))
    child.on("error", (err) => {
      clearTimeout(timer)
      resolvePromise({
        stdout: Buffer.concat(outChunks).toString("utf8"),
        stderr: Buffer.concat(errChunks).toString("utf8"),
        code: -1,
        spawnError: err,
        timedOut,
      })
    })
    child.on("close", (code) => {
      clearTimeout(timer)
      resolvePromise({
        stdout: Buffer.concat(outChunks).toString("utf8"),
        stderr: Buffer.concat(errChunks).toString("utf8"),
        code,
        timedOut,
      })
    })
    child.stdin.write(opts.input)
    child.stdin.end()
  })
}

// The TypeScript driver lives in a temp dir (never in this repository) and
// imports the parser + expander from the sibling checkout by absolute path
// (passed as argv[2]). No top-level await: the temp dir has no type:module
// package.json, so tsx transpiles the driver as CJS.
function tsDriverSource() {
  return `
import { readFileSync } from "node:fs"
import { pathToFileURL } from "node:url"

async function main() {
  const tsDir = process.argv[2]
  const { parseIsc } = await import(pathToFileURL(tsDir + "/src/isc/parser.ts").href)
  const { expandDocument } = await import(pathToFileURL(tsDir + "/src/isc/expand.ts").href)

  const manifest = JSON.parse(readFileSync(0, "utf8"))

  const cache = new Map()
  function depDoc(stem) {
    if (cache.has(stem)) return cache.get(stem)
    const entry = manifest.depIndex[stem]
    if (!entry) return undefined
    const doc = parseIsc(readFileSync(entry, "utf8"), entry)
    cache.set(stem, doc)
    return doc
  }
  const resolveDependency = (target) => depDoc(target)

  const lines = []
  for (const f of manifest.files) {
    console.error("processing " + f.rel)
    try {
      const source = readFileSync(f.path, "utf8")
      const doc = parseIsc(source, f.path)
      // Expand use directives with the parser's own W1/W2 semantics.
      const expanded = expandDocument(doc, { resolveDependency })
      // Ruleset bodies never execute, but a use directive inside them must
      // resolve the same way for the ruleset projection to be comparable.
      // Reuse the expansion machinery on a synthetic one-stage document.
      const rulesetBodies = {}
      for (const rs of doc.rulesets ?? []) {
        const synth = { ...expanded, stages: [{ name: "__ruleset__", body: rs.body }] }
        rulesetBodies[rs.name] = expandDocument(synth, { resolveDependency }).stages[0].body
      }
      lines.push(JSON.stringify({
        rel: f.rel, ok: true,
        doc: {
          systemCode: expanded.systemCode,
          metadata: expanded.metadata,
          tests: expanded.tests,
          aliases: expanded.aliases,
          dependencies: expanded.dependencies,
          languages: expanded.languages,
          stages: expanded.stages,
          rulesetBodies,
        },
      }))
    } catch (e) {
      lines.push(JSON.stringify({ rel: f.rel, ok: false, error: String(e && e.message ? e.message : e) }))
    }
  }
  console.log(lines.join("\\n"))
}

main().catch((e) => {
  console.error(String(e && e.stack ? e.stack : e))
  process.exitCode = 1
})
`
}

// The Python driver is passed via -c; the manifest arrives on stdin.
function pyDriverSource() {
  return `
import json, sys
from interscript.isc import parse_isc

manifest = json.loads(sys.stdin.read())
dep_index = manifest["depIndex"]
cache = {}

def jsonable(x):
    if hasattr(x, "__dataclass_fields__"):
        d = {"__kind__": type(x).__name__}
        for k in x.__dataclass_fields__:
            d[k] = jsonable(getattr(x, k))
        return d
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    return x

def resolver(target):
    if target in cache:
        return cache[target]
    entry = dep_index.get(target)
    if entry is None:
        return None
    with open(entry, encoding="utf-8") as fh:
        doc = parse_isc(fh.read(), entry, resolve_dependency=resolver)
    cache[target] = doc
    return doc

lines = []
for f in manifest["files"]:
    print("processing " + f["rel"], file=sys.stderr)
    try:
        with open(f["path"], encoding="utf-8") as fh:
            source = fh.read()
        doc = parse_isc(source, f["path"], resolve_dependency=resolver)
        lines.append(json.dumps({
            "rel": f["rel"], "ok": True,
            "doc": {
                "systemCode": doc.system_code,
                "metadata": jsonable(doc.metadata),
                "tests": jsonable(doc.tests),
                "aliases": jsonable(doc.aliases),
                "dependencies": jsonable(doc.dependencies),
                "languages": jsonable(doc.languages),
                "stages": jsonable(doc.stages),
                "rulesetBodies": jsonable(doc.rulesets),
            },
        }))
    except Exception as e:  # noqa: BLE001 - one bad file must not stop the audit
        lines.append(json.dumps({"rel": f["rel"], "ok": False, "error": type(e).__name__ + ": " + str(e)}))
sys.stdout.write("\\n".join(lines))
`
}

function parseJsonl(stdout) {
  const out = new Map()
  for (const line of stdout.split("\n")) {
    if (!line.trim()) continue
    const rec = JSON.parse(line)
    out.set(rec.rel, rec)
  }
  return out
}

// ---------------------------------------------------------------------------
// Canonical schema — shared target of the two per-parser normalizers
//
// Items:    {t:"s",v} | {t:"none"} | {t:"prim",name} | {t:"fn",name}
//           | {t:"alias",name} | {t:"ref",id} | {t:"cap",inner}
//           | {t:"cat",parts} | {t:"any",of} | {t:"range",lo,hi}
//           | {t:"maybe",inner} | {t:"some",inner}
// Rules:    {from, to, constraints:[{kind,item}], when?}
// Stage items: {k:"rule",rule} | {k:"parallel"|"sequence",rules}
//           | {k:"run",stage,dependency?} | {k:"separate",separator?}
//           | {k:"compose"} | {k:"decompose"} | {k:"string_case",op}
//           | {k:"funcall",name,kwargs}
// ---------------------------------------------------------------------------

// The parsers' own keyword tables (mirrored from both checkouts; identical).
const PRIMITIVES = new Set(["boundary", "line_start", "line_end", "word_boundary", "space", "non_boundary"])
const FUNCTIONS = new Set(["upcase", "downcase", "title_case", "reverse", "strip", "swapcase"])

function canonTsItem(it) {
  if (!it || typeof it !== "object") return { t: "shape", raw: String(it) }
  switch (it.type) {
    case "string": return { t: "s", v: it.value }
    case "none": return { t: "none" }
    case "primitive": return { t: "prim", name: it.name }
    case "function": return { t: "fn", name: it.name }
    case "alias_ref": return { t: "alias", name: it.name }
    case "capture": return { t: "ref", id: it.index }
    case "capture_group": return { t: "cap", inner: canonTsItem(it.inner) }
    case "concat": return { t: "cat", parts: it.parts.map(canonTsItem) }
    case "set": return { t: "any", of: it.items.map(canonTsItem) }
    case "range": return { t: "range", lo: it.lo, hi: it.hi }
    case "maybe": return { t: "maybe", inner: canonTsItem(it.inner) }
    case "some": return { t: "some", inner: canonTsItem(it.inner) }
    default: return { t: "shape", raw: JSON.stringify(it) }
  }
}

function canonPyItem(it) {
  if (!it || typeof it !== "object") return { t: "shape", raw: String(it) }
  switch (it.__kind__) {
    case "StringItem": return { t: "s", v: it.value }
    case "AliasItem":
      // The Python parser renders primitives and function keywords as alias
      // items; the canonical schema normalizes them by name.
      if (PRIMITIVES.has(it.name)) return { t: "prim", name: it.name }
      if (FUNCTIONS.has(it.name)) return { t: "fn", name: it.name }
      return { t: "alias", name: it.name }
    case "CaptureGroupItem": return { t: "cap", inner: canonPyItem(it.data) }
    case "CaptureRefItem": return { t: "ref", id: it.id }
    case "AnyItem": return { t: "any", of: it.of.map(canonPyItem) }
    case "AnyCharClassItem":
      if (it.range) return { t: "range", lo: it.range[0], hi: it.range[1] }
      if (it.chars) return { t: "any", of: it.chars.map((c) => ({ t: "s", v: c })) }
      return { t: "shape", raw: "any_char_class with neither range nor chars" }
    case "GroupItem": return { t: "cat", parts: it.items.map(canonPyItem) }
    case "RepeatItem":
      if (it.min === 0 && it.max === 1) return { t: "maybe", inner: canonPyItem(it.item) }
      if (it.min === 1 && it.max === null) return { t: "some", inner: canonPyItem(it.item) }
      return { t: "shape", raw: `repeat min=${it.min} max=${it.max}` }
    case "FuncallInline": return { t: "fn", name: it.name }
    case "StageItem": return { t: "stage_ref", name: it.name }
    default: return { t: "shape", raw: JSON.stringify(it) }
  }
}

function canonTsRule(r) {
  return {
    from: canonTsItem(r.from),
    to: canonTsItem(r.to),
    constraints: (r.constraints ?? []).map((c) => ({ kind: c.kind, item: canonTsItem(c.item) })),
    ...(r.when ? { when: [...r.when] } : {}),
  }
}

// SubRule carries constraints as four fixed fields: written ORDER between
// constraint kinds is lost, and a duplicated kind keeps only the last.
const PY_CONSTRAINT_ORDER = ["before", "after", "not_before", "not_after"]

function canonPyRule(r) {
  return {
    from: canonPyItem(r.from_),
    to: canonPyItem(r.to),
    constraints: PY_CONSTRAINT_ORDER
      .filter((k) => r[k] != null)
      .map((k) => ({ kind: k, item: canonPyItem(r[k]) })),
    ...(r.when ? { when: [...r.when] } : {}),
  }
}

function canonTsStageItem(it) {
  switch (it.kind) {
    case "bare_rule": return { k: "rule", rule: canonTsRule(it.rule) }
    case "parallel": return { k: "parallel", rules: it.rules.map(canonTsRule) }
    case "sequence": return { k: "sequence", rules: it.rules.map(canonTsRule) }
    case "run": return { k: "run", stage: it.stage, ...(it.dependency ? { dependency: it.dependency } : {}) }
    case "separate":
      return {
        k: "separate",
        ...(it.separator ? { separator: canonTsItem(it.separator) } : {}),
      }
    case "compose": return { k: "compose" }
    case "decompose": return { k: "decompose" }
    case "string_case": return { k: "string_case", op: it.op }
    case "funcall": return { k: "funcall", name: it.name, kwargs: { ...it.kwargs } }
    case "use": return { k: "shape", raw: "use item survived expansion" }
    default: return { k: "shape", raw: JSON.stringify(it) }
  }
}

function canonPyStageItem(it) {
  switch (it.__kind__) {
    case "ParsedRule": return { k: "rule", rule: canonPyRule(it.rule) }
    case "ParallelBlock": return { k: "parallel", rules: it.rules.map((r) => canonPyRule(r.rule)) }
    case "SequenceBlock": return { k: "sequence", rules: it.rules.map((r) => canonPyRule(r.rule)) }
    case "RunItem": return { k: "run", stage: it.stage, ...(it.dependency ? { dependency: it.dependency } : {}) }
    case "FuncallRule": {
      if (it.name === "separate") {
        // The Python parser lowers a string separator to a plain kwarg and
        // DROPS a non-string separator entirely.
        const sep = it.kwargs?.separator
        return { k: "separate", ...(sep != null ? { separator: { t: "s", v: sep } } : {}) }
      }
      if (it.name === "compose") return { k: "compose" }
      if (it.name === "decompose") return { k: "decompose" }
      if (FUNCTIONS.has(it.name)) return { k: "string_case", op: it.name }
      return { k: "funcall", name: it.name, kwargs: { ...it.kwargs } }
    }
    default: return { k: "shape", raw: JSON.stringify(it) }
  }
}

function canonTsDoc(doc) {
  return {
    systemCode: doc.systemCode,
    metadata: doc.metadata ?? {},
    tests: (doc.tests ?? []).map((t) => ({
      input: t.input,
      expected: t.expected,
      ...(t.note !== undefined ? { note: t.note } : {}),
    })),
    dependencies: (doc.dependencies ?? []).map((d) => ({
      target: d.target,
      ...(d.aliasName !== undefined ? { alias: d.aliasName } : {}),
    })),
    aliases: (doc.aliases ?? []).map((a) => ({ name: a.name, item: canonTsItem(a.value) })),
    ...(doc.languages ? { languages: [...doc.languages] } : {}),
    stages: (doc.stages ?? []).map((s) => ({ name: s.name, body: s.body.map(canonTsStageItem) })),
    rulesets: Object.entries(doc.rulesetBodies ?? {})
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([name, body]) => ({ name, body: body.map(canonTsStageItem) })),
  }
}

function canonPyDoc(doc) {
  return {
    systemCode: doc.systemCode,
    metadata: doc.metadata ?? {},
    tests: (doc.tests ?? []).map((t) => ({
      input: t.input,
      expected: t.expected,
      ...(t.note != null ? { note: t.note } : {}),
    })),
    dependencies: (doc.dependencies ?? []).map((d) => ({
      target: d.target,
      ...(d.alias_name != null ? { alias: d.alias_name } : {}),
    })),
    aliases: (doc.aliases ?? []).map((a) => ({ name: a[0], item: canonPyItem(a[1]) })),
    ...(doc.languages ? { languages: [...doc.languages] } : {}),
    stages: (doc.stages ?? []).map((s) => ({ name: s.name, body: s.items.map(canonPyStageItem) })),
    rulesets: Object.entries(doc.rulesetBodies ?? {})
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([name, body]) => ({ name, body: body.map(canonPyStageItem) })),
  }
}

// ---------------------------------------------------------------------------
// Structural comparison — collects divergences with kind + path + renderings
// ---------------------------------------------------------------------------

function render(x) {
  // Full fidelity for the machine-readable report: the values carry real
  // corpus text (astral chars included), so no truncation here — the
  // console printer truncates code-point-safely instead.
  return JSON.stringify(x)
}

function renderShort(x, max = 160) {
  const s = typeof x === "string" ? x : JSON.stringify(x)
  if (s.length <= max) return s
  // Slice on code POINTS so astral characters are never split (a cut
  // surrogate pair would surface as U+FFFD garbage downstream).
  const pts = Array.from(s)
  return pts.slice(0, max).join("") + `...(+${pts.length - max})`
}

// Contexts select the divergence KIND for a section-level mismatch.
function compareDocs(a, b, divergences) {
  const sections = ["systemCode", "metadata", "tests", "dependencies", "aliases", "languages", "stages", "rulesets"]
  for (const section of sections) {
    if (a[section] === undefined && b[section] === undefined) continue
    if (a[section] === undefined || b[section] === undefined) {
      divergences.push({ kind: section, path: section, ts: render(a[section]), py: render(b[section]) })
      continue
    }
    walk(a[section], b[section], section, section, divergences)
  }
}

function walk(a, b, path, section, divergences) {
  // Canonical items are tagged `t`, stage items `k`; scalars compare directly.
  const aItem = a !== null && typeof a === "object" && "t" in a
  const bItem = b !== null && typeof b === "object" && "t" in b
  const aStage = a !== null && typeof a === "object" && "k" in a
  const bStage = b !== null && typeof b === "object" && "k" in b

  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) {
      divergences.push({ kind: section, path, ts: `len=${a.length}`, py: `len=${b.length}` })
    }
    const n = Math.min(a.length, b.length)
    for (let i = 0; i < n; i++) walk(a[i], b[i], `${path}[${i}]`, section, divergences)
    return
  }
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") {
    if (a !== b) divergences.push({ kind: section, path, ts: render(a), py: render(b) })
    return
  }
  if (aItem !== bItem || aStage !== bStage) {
    divergences.push({ kind: "shape", path, ts: render(a), py: render(b) })
    return
  }
  if (aItem) {
    if (a.t !== b.t) {
      divergences.push({ kind: "item-kind", path, ts: render(a), py: render(b) })
    } else {
      walk(payloadOf(a), payloadOf(b), path, "item-value", divergences)
    }
    return
  }
  if (aStage) {
    if (a.k !== b.k) {
      divergences.push({ kind: "stage-item-kind", path, ts: render(a), py: render(b) })
    } else {
      walk(payloadOf(a), payloadOf(b), path, "stage-item-value", divergences)
    }
    return
  }
  // Plain structural object (rule, constraint, test row, metadata map, ...).
  const keys = new Set([...Object.keys(a), ...Object.keys(b)])
  for (const key of keys) {
    // A tighter KIND for the payload keys that carry structural meaning.
    const kind =
      key === "constraints" ? "constraints" : key === "rule" ? "rule-shape" : section
    if (!(key in a) || !(key in b)) {
      divergences.push({ kind, path: `${path}.${key}`, ts: render(a[key]), py: render(b[key]) })
      continue
    }
    walk(a[key], b[key], `${path}.${key}`, kind, divergences)
  }
}

function payloadOf(node) {
  const { t, k, ...rest } = node
  return rest
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const checks = [
    ["--ts-root", tsRoot, [join(tsRoot, "src", "isc", "parser.ts"), join(tsRoot, "src", "isc", "expand.ts")]],
    ["--py-root", pyRoot, [pySrcRoot]],
  ]
  for (const [label, dir, paths] of checks) {
    for (const p of paths) {
      let ok = false
      try {
        ok = statSync(p).isDirectory() || statSync(p).isFile()
      } catch {
        ok = false
      }
      if (!ok) {
        console.error(`parse-parity: ${label} ${dir} does not look like the expected checkout (${p} missing)`)
        console.error("parse-parity: clone the sibling repositories first (git clone --depth=1 <main>)")
        process.exit(2)
      }
    }
  }

  const { files, depIndex } = discoverCorpus()
  if (files.length === 0) {
    console.error("parse-parity: no corpus files found under maps/ and libs/")
    process.exit(2)
  }
  const manifest = JSON.stringify({ files, depIndex })

  const tmp = mkdtempSync(join(tmpdir(), "parity-ts-"))
  const driverPath = join(tmp, "parity-ts-driver.ts")
  writeFileSync(driverPath, tsDriverSource())

  console.error(`parse-parity: ${files.length} corpus files; ts=${relative(repoRoot, tsRoot)} py=${relative(repoRoot, pyRoot)}`)

  const [tsRun, pyRun] = await Promise.all([
    runProcess("npx", ["-y", "tsx", driverPath, tsRoot], { cwd: tsRoot, input: manifest, timeoutMs }),
    runProcess(pyBin, ["-c", pyDriverSource()], {
      cwd: repoRoot,
      env: { PYTHONPATH: pySrcRoot },
      input: manifest,
      timeoutMs,
    }),
  ])
  rmSync(tmp, { recursive: true, force: true })

  if (tsRun.spawnError) {
    console.error(`parse-parity: cannot run npx/tsx: ${tsRun.spawnError.message}`)
    process.exit(2)
  }
  if (pyRun.spawnError) {
    console.error(`parse-parity: cannot run ${pyBin}: ${pyRun.spawnError.message}`)
    process.exit(2)
  }
  for (const [side, run] of [["ts", tsRun], ["py", pyRun]]) {
    if (run.timedOut) {
      const last = run.stderr.trim().split("\n").filter((l) => l.startsWith("processing ")).pop()
      console.error(`parse-parity: ${side} driver exceeded --timeout (${timeoutMs}ms) and was killed`)
      console.error(`parse-parity: ${side} last file in progress: ${last ?? "(none recorded)"}`)
      console.error("parse-parity: a parser can spin forever on an unrecognized stage-body token that swallows its closing brace (no end-of-source guard in the body loops); flag that corpus file for the parser owners")
      process.exit(2)
    }
  }

  let tsResults, pyResults
  try {
    tsResults = parseJsonl(tsRun.stdout)
    pyResults = parseJsonl(pyRun.stdout)
  } catch (e) {
    console.error(`parse-parity: driver output was not valid JSONL: ${e.message}`)
    console.error(`parse-parity: ts stderr (tail): ${tsRun.stderr.slice(-500)}`)
    console.error(`parse-parity: py stderr (tail): ${pyRun.stderr.slice(-500)}`)
    process.exit(2)
  }

  // Driver-level failures surface as a warning plus per-file error records.
  if (tsRun.code !== 0 && tsRun.stderr.trim()) {
    console.error(`parse-parity: ts driver exit ${tsRun.code}; stderr tail: ${tsRun.stderr.slice(-400)}`)
  }
  if (pyRun.code !== 0 && pyRun.stderr.trim()) {
    console.error(`parse-parity: py driver exit ${pyRun.code}; stderr tail: ${pyRun.stderr.slice(-400)}`)
  }

  // Compare.
  const fileReports = []
  const kindCounts = new Map()
  let pass = 0

  for (const f of files) {
    const ts = tsResults.get(f.rel) ?? { ok: false, error: `ts driver produced no result (exit ${tsRun.code})` }
    const py = pyResults.get(f.rel) ?? { ok: false, error: `py driver produced no result (exit ${pyRun.code})` }
    const divergences = []

    if (!ts.ok && !py.ok) {
      divergences.push({ kind: "error-both", path: "parse", ts: ts.error, py: py.error })
    } else if (!ts.ok) {
      divergences.push({ kind: "error-ts", path: "parse", ts: ts.error, py: "ok" })
    } else if (!py.ok) {
      divergences.push({ kind: "error-py", path: "parse", ts: "ok", py: py.error })
    } else {
      compareDocs(canonTsDoc(ts.doc), canonPyDoc(py.doc), divergences)
    }

    for (const d of divergences) kindCounts.set(d.kind, (kindCounts.get(d.kind) ?? 0) + 1)
    const status = divergences.length === 0 ? "PASS" : "FAIL"
    if (status === "PASS") pass++
    fileReports.push({ path: f.rel, status, divergences })

    if (status === "PASS") {
      console.log(`${f.rel} PASS`)
    } else {
      const first = divergences[0]
      console.log(`${f.rel} FAIL ${divergences.length} divergence(s); first: ${first.kind} @ ${first.path}`)
      if (verbose) {
        for (const d of divergences) {
          console.log(`    ${d.kind} @ ${d.path}\n      ts: ${renderShort(d.ts)}\n      py: ${renderShort(d.py)}`)
        }
      }
    }
  }

  const kinds = [...kindCounts.entries()].sort((a, b) => b[1] - a[1])
  console.log(`parity: ${pass}/${files.length} files structurally identical; ${kinds.length} divergence kinds`)
  for (const [kind, count] of kinds) console.log(`  ${kind}: ${count}`)

  if (jsonOut) {
    writeFileSync(
      resolve(jsonOut),
      JSON.stringify(
        {
          harness: "scripts/parse-parity.mjs",
          corpusRoot: repoRoot,
          parsers: {
            ts: { root: tsRoot },
            py: { root: pyRoot, bin: pyBin },
          },
          totals: { files: files.length, pass, fail: files.length - pass },
          kinds: Object.fromEntries(kinds),
          files: fileReports,
        },
        null,
        2,
      ),
    )
    console.error(`parse-parity: report written to ${resolve(jsonOut)}`)
  }

  process.exitCode = pass === files.length ? 0 : 1
}

try {
  await main()
} catch (e) {
  console.error(`parse-parity: ${e && e.stack ? e.stack : e}`)
  process.exit(2)
}
