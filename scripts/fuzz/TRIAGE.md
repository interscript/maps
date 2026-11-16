# WO20 differential fuzz campaign — triage report

Campaign: 2026-11-17, branch `wo20-fuzz`, maps#284.
Harness: `scripts/fuzz/` (generator + runner + classifier + minimizer).

## Runtimes under test

| runtime | tree | note |
|---|---|---|
| ruby | interscript-ruby origin/main (4c47eb5, v3.7.2) | fresh clone; DSL parse path |
| ts | interscript-ts origin/main (b74cfda, dist built) | fresh clone; production parse chain |
| py | interscript-py origin/main (c6ae457, 0.2.x, PYTHONPATH=src) | fresh clone; new handwritten parser |
| rs | interscript-rs release 0.3.2 (74b4b8d) | built against crates.io parsanol ^1.5.1 |

Note: rs origin/main (94c5f28) does not build standalone — its `Cargo.toml`
path-pins a maintainer-local parsanol tree carrying unreleased APIs
(`array_item`/`hash_item`); crates.io parsanol 1.5.1 lacks them. The
campaign therefore used the released 0.3.2 commit, which is what the
publish pipeline verifies (path→version rewrite, see rs
`.github/workflows/publish.yml`). The two post-0.3.2 commits are a perf
change and a golden-rows refresh; parse semantics unchanged.

Note: docs/parity audits the WF1-tree py (0.1.0 portable grammar); the
campaign's py is origin/main 0.2.x (new handwritten parser + regex
engine) — the current canonical per the task statement
(PYTHONPATH=interscript-py/src). Several parity-era known kinds behave
differently there; classification used case-content signatures, not
per-runtime behavior.

## Campaign

- Cases: 1600 (1200 corpus-mutation, 400 grammar-aware), seed 20261117.
- Observations: 6400 (4 runtimes × 1600), per-case timeout 45 s.
- Outcomes: agree 1007, known-kind 268, FINDINGS 325 (cases with at least
  one unexplained crash/hang/divergence).
- Finding kinds (case-level, non-exclusive): divergence 315, crash 167,
  hang 10. By primarily-offending runtime: py 118, ruby 29, ts 15, rs 15.
- The 325 findings cluster into 16 behavior-shape groups, which reduce to
  7 root causes / filed issues below. The long tail (bucket-level error
  class differences on shared rejections, e.g. py naming
  `UnsupportedConstruct` where others raise PARSE errors) is consistent
  with the G9 documented family on the new py and is not separately filed.

## Filed issues

| # | repo | kind | root cause | campaign evidence | repro |
|---|---|---|---|---|---|
| [interscript-py#43](https://github.com/interscript/interscript-py/issues/43) | py | hang | parse infinite loop on truncated maps (`_stage`/`_block_items`) | 10 cases (all TIMEOUTs are py) | `findings/py-parse-hang/map.isc` (10 lines) |
| [interscript-py#44](https://github.com/interscript/interscript-py/issues/44) | py | crash | malformed/unsupported `\u` escapes raise raw `ValueError` not `IscParseError` (fires on note text too) | 107 cases (largest class) | `findings/py-malformed-escape-crash/map.isc` |
| [interscript-ruby#864](https://github.com/interscript/interscript-ruby/issues/864) | ruby | crash | `NameError: uninitialized constant Node::Item::CaptureRef` on `ref(N)` in from position | 14 cases | `findings/ruby-ref-in-from-crash/map.isc` |
| [maps#292](https://github.com/interscript/maps/issues/292) | ruby vs others | divergence | `alias = maybe(...)` miscompiled — rule silently never fires | 52 cases | `findings/ruby-alias-maybe-silent/map.isc` |
| [maps#293](https://github.com/interscript/maps/issues/293) | py vs others | divergence | py 0.2.x parse boundary differs in both directions (accepts nested blocks/unknown keywords; rejects zero-width primitives in from) | ~130 cases | `findings/py-nested-block-acceptance/map.isc`, `findings/py-zero-width-reject/map.isc` |
| [maps#294](https://github.com/interscript/maps/issues/294) | all four | divergence+crash | self-recursive `run stage.<self>`: rs SIGABRT, ruby/ts stack-overflow crashes, py named guard | 15 cases | `findings/self-run-recursion/map.isc` |
| [maps#295](https://github.com/interscript/maps/issues/295) | py | divergence | note-text `{` corrupts py parse → wrong output; py silently succeeds where others raise MapLogicError | 2 cases | `findings/py-note-brace-corruption/map.isc` |

## Smoke mode

`smoke-cases/` holds 199 committed cases (seed 20261120, 420-case pool,
agree-or-known survivors; one py-hang case swapped after the classifier's
hang-filter fix). `node smoke.mjs` is green across all four runtimes
locally (agree 155 / known 44 / findings 0) and across ruby+ts in
maps-CI (`.github/workflows/fuzz-smoke.yml`).

## Known-kind filter notes

Classification excludes docs/parity G1–G12 signatures (capture-in-parallel,
unresolved-alias empty matcher, missing main stage, use-in-blocks,
fn-literal keywords, duplicate rulesets, ruleset cycles, ML funcalls,
dependency loader asymmetry). Two harness-level normalizations: invalid
UTF-8 is replaced with U+FFFD identically for all four runtimes (the
parsers, not the file APIs, are under test); dependency-bearing cases
never see their dependency document (isolated per-case dirs), so loader
asymmetry (G12) is filtered.

## Generator changes made during triage

- `\u{...}` braced literals replaced with grammar-valid `\uXXXX` / `\U` forms
  in `generate.mjs` (the braced form rejects 4/4 and was undiscoverable as
  divergence; the escape-edge mutation family still exercises malformed
  escapes deliberately).
- Constraint templates corrected to the probe-verified `not_before "x"` bare
  form (an early draft emitted `before not_before("j")`).
