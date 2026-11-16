# ISC differential fuzz harness (WO20 — maps#284)

Differential fuzzing across the four ISC parsers (ruby, ts, py, rs): throw
mutated/generated `.isc` at every runtime, hunt crashes, hangs, and
cross-runtime divergences the curated corpus cannot surface.

## Layout

| file | role |
|---|---|
| `generate.mjs` | case generator: corpus mutation + grammar-aware templates |
| `run.mjs` | campaign runner: per-case, per-runtime drivers with timeouts |
| `classify.mjs` | finding classifier: crash / hang / divergence + known-kind filter |
| `minimize.mjs` | finding minimizer (delta-debugging shrink + repro proof) |
| `smoke.mjs` | CI-able seeded smoke mode over committed `smoke-cases/` |
| `drivers/` | one driver per runtime, uniform JSON contract |
| `smoke-cases/` | committed seeded corpus (~200 cases), must stay green |
| `TRIAGE.md` | campaign triage report (findings + minimized repros) |

## Runtime locations

Drivers locate the runtime trees via environment variables; defaults assume
the runtime repos are checked out as siblings of the maps clone:

| runtime | env var | default (from repo root) |
|---|---|---|
| ruby | `RUBY_LIB` | `../interscript-ruby/lib` |
| ts | `TS_DIST` | `../interscript-ts/dist` (after `npm run build`) |
| py | `PY_SRC` | `../interscript-py/src` |
| rs | `ISCRS_BIN` | `../interscript-rs/target/release/iscrs` |

Missing runtimes are skipped by smoke mode (maps-CI runs ruby + ts) and can
be excluded from campaigns with `--runtimes`.

## Driver contract

`driver-<rt> <case.isc> <inputs-json>` prints one JSON line:

```json
{"runtime":"ruby","parse":{"status":"OK"},"exec":[{"input":"ab","status":"OK","output":"..."}]}
```

Parse leg = the runtime's canonical `.isc` parse entry (ruby: the DSL load
path `Interscript.parse`; ts: `parseIsc -> expandDocument -> iscToCompiledMap
-> normaliseMap`; py: `interscript.isc.isc_to_tree` (origin/main 0.2.x);
rs: `iscrs parse --maps`). Exec leg = main stage over the case's own test
inputs (up to 3, extracted from the `tests { }` block; fallback `"ab"`).

Error buckets are normalized across runtimes: `OK PARSE LOAD LOGIC
UNSUPPORTED CRASH TIMEOUT OTHER`. A driver exiting nonzero without JSON is
recorded as a process-level crash; exceeding the runner timeout is a hang.

Harness-boundary normalization: cases may contain invalid UTF-8 (byte-flip
mutations); the runner substitutes U+FFFD for every runtime identically, so
the parsers — not the file APIs — are under test.

## Known-kind filter

Divergences documented in `docs/parity/README.md` (audit items G1–G12, plus
the env-dependent ML funcall battery rows) are design facts, not findings.
The classifier detects their signatures on case content (`capture/ref` in
parallel blocks, unresolved aliases, missing main stage, `use` inside
blocks, fn-literal keywords, duplicate rulesets, ruleset cycles, ML
funcalls) and classifies those cases as `known`. Everything else is a
FINDING. Findings carry their evidence; each one is re-audited against the
parity docs before it becomes an issue.

## Usage

```sh
# campaign (from this dir)
node generate.mjs --out /tmp/fuzz-run --seed 1234 --mutation 1200 --grammar 400
RUBY_LIB=... TS_DIST=... PY_SRC=... ISCRS_BIN=... \
  node run.mjs --cases /tmp/fuzz-run/cases --out /tmp/fuzz-run/results.jsonl --jobs 6
node classify.mjs --results /tmp/fuzz-run/results.jsonl --cases /tmp/fuzz-run/cases \
  --out /tmp/fuzz-run/findings.jsonl --summary /tmp/fuzz-run/summary.md
node minimize.mjs --findings /tmp/fuzz-run/findings.jsonl --cases /tmp/fuzz-run/cases \
  --out-dir /tmp/fuzz-run/min

# CI-able smoke (committed cases; green required)
node smoke.mjs --runtimes ruby,ts
```

Rules of the campaign (issue #284): findings get minimized and documented;
parser bugs are NOT fixed here — fix issues get filed and sequenced.
