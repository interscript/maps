// ISC differential-fuzz case generator (WO20, maps#284).
//
// Two families:
//   mutation — byte/line/structure mutations over the 428-map corpus:
//     truncate, byte-flip, line delete/dup/swap, cross-map rule splices,
//     WF-1 construct injection (ruleset/use/override/languages/when,
//     targeting the documented G5/G7 surfaces), keyword/fn-literal
//     injection (G6/G8), malformed escapes/editions, unicode edge literals.
//   grammar  — VALID but unusual maps from templates: nested any/capture/
//     maybe, constraint combos, alias chains, duplicate-from blocks,
//     unicode edge literals, empty-string rules, self-runs (bounded).
//
// Every case is reproducible: the manifest records seed + index per case.
// Output layout: <out>/cases/<caseid>/map.isc  (+ <out>/manifest.json)

import { writeFileSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { makeRng, listCorpus, pickSeedMap, ensureDir } from "./lib.mjs";

// ---------------------------------------------------------------------------
// Atom pools (grammar-aware content)
// ---------------------------------------------------------------------------

const ASCII_STRINGS = ["a", "b", "k", "q", "x", "z", "ab", "kh", "kk", "xy", "1", "3", "-", " ", "."];
const UNICODE_LITERALS = [
  // valid ISC escapes: \\uXXXX (exactly 4 hex) and \\U+4-8 hex (isc.parg esc_uni4/esc_uni)
  "\\u00E9", // é
  "\\u0301", // combining acute
  "\\u200D", // ZWJ
  "\\u200F", // RTL mark
  "\\u00A0", // NBSP
  "\\U01F600", // emoji (U-form, 4..8 hex)
  "\\U10FFFF", // max plane (U-form)
  "\\u0646", // arabic noon
  "\\u0E01", // thai ko kai
  "\\u010C", // D with caron
];
const ESCAPE_EDGE_CASES = [
  "\\u{110000}", // braced form (not in the grammar) + out of range
  "\\uD800", // lone surrogate (valid shape, invalid scalar)
  "\\u{}", // empty hex
  "\\uZZZZ", // bad hex
  "\\x", // incomplete
  "\\q", // unknown escape
  "\\", // trailing backslash
  "\\u00E", // short hex (grammar wants exactly 4)
  "\\U01F6", // U-form with 3 hex (grammar wants 4..8)
];
const FN_KEYWORDS = ["upcase", "downcase", "title_case", "reverse", "strip", "swapcase"];
const ZERO_WIDTH = ["boundary", "line_start", "line_end", "word_boundary", "space", "non_boundary"];
const FUNCALL_DIRECTIVES = ["upcase", "downcase", "title_case"];

// ---------------------------------------------------------------------------
// Mutation operators
// ---------------------------------------------------------------------------

function opTruncate(rng, src) {
  const frac = 0.05 + rng.next() * 0.85;
  const pos = Math.max(1, Math.min(src.length - 1, Math.floor(src.length * frac)));
  return src.slice(0, pos);
}

function opByteFlip(rng, src) {
  const buf = Buffer.from(src, "utf8");
  const n = rng.int(1, 8);
  for (let i = 0; i < n; i++) {
    const pos = rng.int(0, buf.length - 1);
    buf[pos] = rng.chance(0.3) ? rng.int(0x00, 0x1f) : rng.int(0x20, 0xff);
  }
  return buf; // raw bytes preserved (may be invalid UTF-8, by design)
}

function opLineDelete(rng, src) {
  const lines = src.split("\n");
  if (lines.length < 3) return src;
  lines.splice(rng.int(0, lines.length - 1), 1);
  return lines.join("\n");
}

function opLineDuplicate(rng, src) {
  const lines = src.split("\n");
  const i = rng.int(0, lines.length - 1);
  lines.splice(i, 0, lines[i]);
  return lines.join("\n");
}

function opLineSwap(rng, src) {
  const lines = src.split("\n");
  if (lines.length < 3) return src;
  const i = rng.int(0, lines.length - 2);
  const j = rng.int(i + 1, Math.min(i + 40, lines.length - 1));
  [lines[i], lines[j]] = [lines[j], lines[i]];
  return lines.join("\n");
}

// Extract a random run of rule-ish lines from a donor map and splice it in.
function opSpliceRules(rng, src, donorPool) {
  const donor = rng.pick(donorPool);
  const lines = donor.text.split("\n");
  const ruleIdx = [];
  lines.forEach((l, i) => {
    if (/^\s*(sub|use|parallel|sequence|stage)\b/.test(l)) ruleIdx.push(i);
  });
  if (ruleIdx.length === 0) return src;
  const start = rng.pick(ruleIdx);
  const count = rng.int(1, Math.min(15, lines.length - start));
  const block = lines.slice(start, start + count).join("\n");
  const target = src.split("\n");
  const at = rng.int(1, Math.max(1, target.length - 1));
  target.splice(at, 0, block);
  return target.join("\n");
}

// WF-1 construct injection (ruleset/use/override/languages/when).
function opInjectWF1(rng, src) {
  const snippets = [
    // stage-level use of a declared ruleset
    `  ruleset fr${rng.int(0, 9)} {\n    parallel { sub "a" "b" }\n  }`,
    // use inside a block (G5 surface)
    `    sequence {\n      sub "x" "y"\n      use inner${rng.int(0, 9)}\n    }`,
    // duplicate ruleset declaration (G7 surface)
    `  ruleset dup${rng.int(0, 9)} {\n    parallel { sub "p" "Q" }\n  }\n  ruleset dup${rng.int(0, 9)} {\n    parallel { sub "r" "S" }\n  }`,
    // use with override
    `  stage ov${rng.int(0, 9)} {\n    use base override {\n      sub "c" "C"\n    }\n  }`,
    // languages + when guards
    `  languages kur chv ev${rng.int(0, 9)}`,
    `      sub "k" "K" when kur`,
    `      sub "k" "Q" when undeclared${rng.int(0, 9)}`,
    // dependency-qualified ruleset use
    `    use ${rng.pick(["nonexistent-dep", "acadsin-zho-hani"])}:rs${rng.int(0, 9)}`,
  ];
  const snippet = rng.pick(snippets);
  const lines = src.split("\n");
  const at = rng.int(1, Math.max(1, lines.length - 1));
  lines.splice(at, 0, snippet);
  return lines.join("\n");
}

// Keyword-table / fn-literal injection (G6/G8 surfaces).
function opInjectKeyword(rng, src) {
  const kw = rng.pick(FN_KEYWORDS);
  const snippets = [
    `    sub ${kw} "X"`, // fn literal in from position (G6)
    `  alias_decl = any("a")\n  ${kw}2 = any("b")`, // keyword-named alias
    `    ${kw}`, // fn literal as stage directive (G8)
    `    sub "a" "b"\n    ${kw}`, // directive after rule
  ];
  const snippet = rng.pick(snippets);
  const lines = src.split("\n");
  const at = rng.int(1, Math.max(1, lines.length - 1));
  lines.splice(at, 0, snippet);
  return lines.join("\n");
}

function opInjectEscape(rng, src) {
  const lit = rng.pick(ESCAPE_EDGE_CASES);
  const forms = [
    `    sub "${lit}" "X"`,
    `    sub "a" "${lit}"`,
    `    sub "${lit}" "X" before "q" after "z"`,
    `    sub "a" "z"`,
  ];
  const snippet = rng.pick(forms.slice(0, 3));
  const lines = src.split("\n");
  const at = rng.int(1, Math.max(1, lines.length - 1));
  lines.splice(at, 0, snippet);
  return lines.join("\n");
}

function opCorruptMetadata(rng, src) {
  const ops = [
    (s) => s.replace(/^system ".*" \{/, `system "FZ${rng.int(0, 9999)}" {`),
    (s) => s.replace(/^  authority_id .*$/m, ""),
    (s) => s.replace(/^  id .*$/m, `  id ${rng.int(0, 9999)}`),
    (s) => s.replace(/^  source_script .*$/m, `  source_script "Bad Script"`),
    (s) => s + `\n  creation_date ${rng.int(1800, 2200)}`,
    (s) => s.replace(/^metadata \{/m, `metadata {\n  authority_id dup_id\n  authority_id dup_id`),
  ];
  return rng.pick(ops)(src);
}

function opUnicodeInject(rng, src) {
  const lit = rng.pick(UNICODE_LITERALS);
  const forms = [
    `    sub "${lit}" "X"`,
    `    sub "a" "${lit}"`,
    `    sub ${rng.pick(ASCII_STRINGS)} "${lit}" after "${lit}"`,
  ];
  const snippet = rng.pick(forms);
  const lines = src.split("\n");
  const at = rng.int(1, Math.max(1, lines.length - 1));
  lines.splice(at, 0, snippet);
  return lines.join("\n");
}

const MUTATIONS = [
  { name: "truncate", fn: opTruncate, weight: 3 },
  { name: "byteflip", fn: opByteFlip, weight: 3 },
  { name: "linedel", fn: opLineDelete, weight: 3 },
  { name: "linedup", fn: opLineDuplicate, weight: 2 },
  { name: "lineswap", fn: opLineSwap, weight: 2 },
  { name: "splice", fn: opSpliceRules, weight: 4 },
  { name: "wf1", fn: opInjectWF1, weight: 5 },
  { name: "keyword", fn: opInjectKeyword, weight: 3 },
  { name: "escape", fn: opInjectEscape, weight: 3 },
  { name: "metadata", fn: opCorruptMetadata, weight: 2 },
  { name: "unicode", fn: opUnicodeInject, weight: 3 },
];

// ---------------------------------------------------------------------------
// Grammar-aware templates (valid but unusual maps)
// ---------------------------------------------------------------------------

function templateNested(rng) {
  const set = rng.pick([
    `any(["a", "b", "c"])`,
    `any("a".."c")`,
    `any([${rng.pick(UNICODE_LITERALS)}, "k"])`,
  ]);
  const inner = `${set} + maybe("k")`;
  const from = rng.pick([
    `maybe(${inner}) + capture(any("x".."z")) + some("q")`,
    `capture(maybe(${set})) + boundary`,
    `some(any(["k", "q"])) + ref(1)`,
    `word_boundary + capture(some("z")) + word_boundary`,
  ]);
  return wrapMap(rng, `  stage main {\n    sequence {\n      sub {\n        from ${from}\n        to "W" + ref(1)\n        not_before "j"\n        not_after "k"\n      }\n    }\n  }`);
}

function templateCaptureChain(rng) {
  const n = rng.int(2, 4);
  const parts = [];
  for (let i = 0; i < n; i++) parts.push(`capture(any("${asciiAtom(rng, i)}".."${asciiAtom(rng, i + 3)}"))`);
  const refs = parts.map((_, i) => `ref(${i + 1})`).join(" + ");
  return wrapMap(rng, `  stage main {\n    parallel {\n      sub {\n        from ${parts.join(" + ")}\n        to ${refs}\n      }\n    }\n  }`);
}

function templateEmptyRules(rng) {
  return wrapMap(rng, `  stage main {\n    sequence {\n      sub "" "L"\n      sub "a" ""\n      sub "" ""\n    }\n  }`);
}

function templateUnicode(rng) {
  const a = rng.pick(UNICODE_LITERALS);
  const b = rng.pick(UNICODE_LITERALS);
  return wrapMap(rng, `  stage main {\n    parallel {\n      sub "${a}" "${b}"\n      sub "${b}" "${a}"\n    }\n  }`);
}

function templateRulesetOverride(rng) {
  const rs = `rs${rng.int(0, 99)}`;
  return wrapMap(rng, `  ruleset ${rs} {\n    parallel {\n      sub "k" "q"\n      sub "t" "d" when kur\n    }\n  }\n  stage main {\n    use ${rs} override {\n      sub "c" "C"\n    }\n  }\n  languages kur chv`);
}

function templateAliasChain(rng) {
  return wrapMap(rng, `  aliases {\n    a1 = any(["x", "y", "z"])\n    a2 = a1 + any("1".."3")\n    a3 = maybe(a2)\n  }\n  stage main {\n    sequence {\n      sub a3 "R"\n    }\n  }`);
}

function templateDupFroms(rng) {
  return wrapMap(rng, `  stage main {\n    parallel {\n      sub "ab" "1"\n      sub "abc" "2"\n      sub "ab" "3"\n    }\n  }`);
}

function templateFuncalls(rng) {
  const d = rng.pick(FUNCALL_DIRECTIVES);
  const kw = `  stage main {\n    parallel { sub "a" "b" }\n    ${d}${d === "title_case" ? " word_separator: \"-\"" : ""}\n  }`;
  return wrapMap(rng, kw);
}

function templateBoundaries(rng) {
  const z = rng.shuffle(ZERO_WIDTH).slice(0, 3);
  return wrapMap(rng, `  stage main {\n    sequence {\n      sub {\n        from ${z[0]} + capture(any("a".."z")) + ${z[1]}\n        to "B" + ref(1)\n      }\n      sub {\n        from line_start + any("k", "q")\n        to "L"\n        after ${z[2]}\n      }\n    }\n  }`);
}

function templateSelfRun(rng) {
  return wrapMap(rng, `  stage main {\n    parallel { sub "a" "b" }\n    run stage.main\n  }`);
}

function templateBlocksInBlocks(rng) {
  // nested parallel inside sequence — pinned negative probe (rejected 4/4
  // per docs/parity A.1); valid-shaped but unusual input for the fuzz.
  return wrapMap(rng, `  stage main {\n    sequence {\n      sub "a" "b"\n      parallel {\n        sub "c" "d"\n      }\n    }\n  }`);
}

function asciiAtom(rng, i) {
  const alphabet = "abcdefghjkmnpqrstvwxyz";
  return alphabet[(i + rng.int(0, 25)) % alphabet.length];
}

function wrapMap(rng, body) {
  const sysname = `FZ:grammar:${rng.int(0, 999999)}`;
  return `system "${sysname}" {\n  metadata {\n    authority_id fz\n    id ${rng.int(0, 99999)}\n    name "grammar-aware fuzz map"\n  }\n${body}\n}\n`;
}

const GRAMMAR_TEMPLATES = [
  { name: "nested", fn: templateNested, weight: 4 },
  { name: "capture-chain", fn: templateCaptureChain, weight: 3 },
  { name: "empty-rules", fn: templateEmptyRules, weight: 2 },
  { name: "unicode", fn: templateUnicode, weight: 3 },
  { name: "ruleset-override", fn: templateRulesetOverride, weight: 3 },
  { name: "alias-chain", fn: templateAliasChain, weight: 3 },
  { name: "dup-froms", fn: templateDupFroms, weight: 2 },
  { name: "funcalls", fn: templateFuncalls, weight: 2 },
  { name: "boundaries", fn: templateBoundaries, weight: 3 },
  { name: "self-run", fn: templateSelfRun, weight: 1 },
  { name: "blocks-in-blocks", fn: templateBlocksInBlocks, weight: 2 },
];

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const opts = {
    out: null,
    seed: 20261120,
    mutation: 150,
    grammar: 50,
    corpusRoot: null,
    maxSeedBytes: 250_000,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--out") opts.out = argv[++i];
    else if (a === "--seed") opts.seed = Number(argv[++i]);
    else if (a === "--mutation") opts.mutation = Number(argv[++i]);
    else if (a === "--grammar") opts.grammar = Number(argv[++i]);
    else if (a === "--corpus-root") opts.corpusRoot = argv[++i];
    else if (a === "--max-seed-bytes") opts.maxSeedBytes = Number(argv[++i]);
    else throw new Error(`unknown flag ${a}`);
  }
  if (!opts.out) throw new Error("--out is required");
  return opts;
}

export function generateCases(opts) {
  const rng = makeRng(opts.seed);
  const corpus = listCorpus(opts.corpusRoot || undefined);
  if (corpus.length === 0) throw new Error("no corpus maps found");
  const donorPool = corpus
    .filter((m) => m.bytes <= 400_000)
    .map((m) => ({ ...m, text: readFileSync(m.path, "utf8") }));

  const cases = [];
  const total = opts.mutation + opts.grammar;

  for (let i = 0; i < total; i++) {
    const mode = i < opts.mutation ? "mutation" : "grammar";
    const id = `${mode}-${String(i).padStart(4, "0")}`;
    let text;
    let base = null;
    if (mode === "mutation") {
      base = pickSeedMap(rng, corpus, opts.maxSeedBytes);
      text = readFileSync(base.path, "utf8");
      const nOps = rng.int(1, 3);
      const applied = [];
      for (let k = 0; k < nOps; k++) {
        const mut = rng.weighted(MUTATIONS.map((m) => ({ item: m, weight: m.weight })));
        const before = text;
        try {
          text = mut.fn(rng, text, donorPool);
        } catch {
          text = before;
        }
        if (Buffer.compare(Buffer.isBuffer(text) ? text : Buffer.from(text, "utf8"), Buffer.isBuffer(before) ? before : Buffer.from(before, "utf8")) !== 0) {
          applied.push(mut.name);
        }
      }
      if (applied.length === 0) applied.push("no-op");
      cases.push({ id, mode, base: base.name, mutations: applied, text });
    } else {
      const tpl = rng.weighted(GRAMMAR_TEMPLATES.map((t) => ({ item: t, weight: t.weight })));
      text = tpl.fn(rng);
      cases.push({ id, mode, base: tpl.name, mutations: [], text });
    }
  }

  ensureDir(join(opts.out, "cases"));
  for (const c of cases) {
    ensureDir(join(opts.out, "cases", c.id));
    // Case files are written as bytes: byte-flip mutations may produce
    // invalid UTF-8 deliberately; the runner normalizes lossily for the
    // drivers so every runtime sees the identical string.
    writeFileSync(
      join(opts.out, "cases", c.id, "map.isc"),
      Buffer.isBuffer(c.text) ? c.text : Buffer.from(c.text, "utf8"),
    );
  }
  const manifest = {
    seed: opts.seed,
    mutation: opts.mutation,
    grammar: opts.grammar,
    corpusRoot: opts.corpusRoot || null,
    cases: cases.map(({ id, mode, base, mutations }) => ({ id, mode, base, mutations })),
  };
  writeFileSync(join(opts.out, "manifest.json"), JSON.stringify(manifest, null, 2));
  return manifest;
}

const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].split("/").pop());
if (isMain) {
  const opts = parseArgs(process.argv.slice(2));
  const manifest = generateCases(opts);
  console.log(
    `generated ${manifest.cases.length} cases (mutation=${manifest.mutation} grammar=${manifest.grammar}) seed=${manifest.seed} -> ${join(opts.out, "cases")}`,
  );
}
