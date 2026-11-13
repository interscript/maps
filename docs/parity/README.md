# ISC Runtime Feature-Parity Audit — ruby (reference) / ts / py / rs

Audit date: 2026-11-13. Research-only artifact: every claim below is
backed by a runnable probe in [`probes/`](probes/) or by a file:line
citation in the named runtime. No fixes are proposed here; the ranked
gap list in [§C](#c-ranked-gap-list) is the input for the fix campaign.

## Runtimes audited

| runtime | repo / tree | version | engine |
|---|---|---|---|
| ruby (reference) | `interscript-ruby` origin/main (wf1 tree) | gem 3.5.0 | hand-written parslet grammar (`lib/interscript/isc/grammar/concerns/*.rb`) + vendored `grammar/isc.parg` scaffold |
| ts | `interscript-ts` (npm `interscript` 5.10.0, dist built) | 5.10.0 | parsanol portable grammar (`src/isc/grammar/grammar-source.ts`) executed by a table-driven PEG (`grammar/peg.ts`) |
| py | `interscript-py` (wf1 tree, `.venv`) | 0.1.0 | same portable grammar (`grammar/grammar_source.py`, sha-pinned sync of the ts source) executed by `grammar/peg.py` |
| rs | `interscript-rs` (release build `target/release/iscrs`) | slice-1 (WO14) | same portable grammar (`grammar/isc.parg`, vendored from ruby with ISC-WF-1 additions) executed by the parsanol portable engine |

Grammar provenance: the three portable grammars (ts/py/rs) are line-oriented
ports of the ruby concern grammar; rs's copy carries the ISC-WF-1
extensions and an explicit keyword-table deviation (see [B.2](#b2-keyword-tables)).

Method: every cell was produced by (a) executing a probe map through all
four runtimes with the drivers in `probes/`, or (b) reading the cited
code. Nothing is asserted from memory or assumption. The battery and its
raw results are committed under `probes/` and `probes/results/`.

---

## A. Feature inventory matrix

Legend: **Y** = supported, **P** = partial (constraints noted), **N** =
absent, **D** = present but behaviorally divergent (see §B).

### A.1 Parse surface (`.isc` grammar)

| feature | ruby | ts | py | rs | evidence |
|---|---|---|---|---|---|
| `sequence` / `parallel` blocks, bare stage-level `sub` | Y | Y | Y | Y | `pp-*`, `tst-basic` parse+exec 4/4 |
| nested `parallel` inside `sequence` (block-in-block) | N | N | N | N | `pp-nested-blocks` (pinned negative probe): rejected 4/4 |
| block rules (`sub { from … to … }`) | Y | Y | Y | Y | `pp-block-sub-full` |
| `before` / `after` / `not_before` / `not_after` | Y | Y | Y | Y | `pp-block-sub-full` |
| `capture(...)` / `ref(N)` — parse | Y | Y | Y | Y | `pp-alias-reffwd` |
| `capture`/`ref` — execute in **sequence** | Y | Y | Y | Y | `tst-capture-seq`: `aX` 4/4 |
| `capture`/`ref` — execute in **parallel** | D crash | D wrong output | D wrong output | Y | [G1](#g1--captureref-inside-parallel-blocks-corrupt-output-ts-py-accidental-crash-ruby) |
| `any(...)`: string sets, `"a".."z"` ranges, alias args, nesting | Y | Y | Y | Y | `pp-any-stringset`, `pp-block-sub-full` |
| `maybe(...)` / `some(...)` | Y | Y | Y | Y | `pp-block-sub-full` |
| zero-width primitives (`boundary`, `line_start`, `line_end`, `word_boundary`, `space`, `non_boundary`) | Y | Y | Y | Y | `pp-boundary-prims` |
| alias block, alias refs, dependency-qualified refs | Y | Y | Y | Y | `tst-alias-def`, `tst-libdep` |
| `run stage.<x>` (local) / `run map.<dep>.stage.<x>` | Y | Y | Y | Y | `pp-run-local`, `tst-dep-run` |
| `separate` [+ `separator:`], `compose` / `decompose` | Y | Y | Y | Y | `pp-separate-sep`, `tst-funcall-exec` |
| `downcase` / `title_case` [+ kwargs] | Y | Y | Y | Y | `pp-titlecase-kwarg`, `tst-funcall-exec` |
| `upcase` directive — parse | Y | Y | Y | Y | `pp-upcase` |
| `upcase` directive — execute | **D NoMethodError** (no `Stdlib::Functions.upcase`) | Y | Y | Y | [G8](#g8--ruby-does-not-implement-four-fn-literals-upcase-reverse-strip-swapcase) |
| `rababa` directive [+ kwargs] — parse | Y | Y | Y | Y | `tst-ml`, `tst-ml-bare` |
| `rababa` — execute | D (env-dependent; named provisioning error without the gem/model) | D named sync-guard error; async path = provisioning | D named `AsyncFunctionError` | D load-time `Unsupported` | [B.3](#b3-behavioral-battery-results) rows `ml-*` |
| metadata (`authority_id`, `description { }`, generic fields) | Y | Y | Y | Y | `pp-tests-meta` |
| `notes { note "…" }` | Y | Y | Y | Y | `pp-notes-block` |
| `tests { "in" -> "out" [note "…"] }` | Y | Y | Y | Y | `pp-tests-meta`, `tst-basic` |
| `dependency "id" [as alias]` | Y | Y | Y | Y | `tst-dep-run`, `tst-libdep` |
| unaliased dependency = library import (aliases merge into scope) | Y | Y | Y | Y | `tst-libdep`: `X` 4/4 |
| `stage(name)` paren form | Y | Y | Y | Y | `pp-stage-block-form` |
| W1 `ruleset <ident> { … }` | Y | Y | Y | Y | `pp-ruleset-local` |
| W1 `use <ident>` at **stage level** | Y | Y | Y | Y | `tst-use-stagelevel` |
| W1 `use` **inside** sequence/parallel blocks | **N** grammar reject | **N** grammar reject | **D** parses, then semantic reject | **Y** (spec §3.2) | [G5](#g5--use-inside-sequenceparallel-blocks-only-rs-implements-spec-32) |
| W1 cycle detection (load-time named error) | Y | Y | Y | Y | `tst-cycle-bare` 4/4 named errors |
| W1 **duplicate** ruleset definition | D silent (first def wins) | D silent (first def wins) | **Y** named load error | D silent, order-dependent merge | [G7](#g7--duplicate-ruleset-definitions-only-py-rejects) |
| W2 `use <ident> override { … }` (child-wins, kept-order, absent-row-added) | Y | Y | Y | Y | `tst-rsbase` `qtC`/`Z` 4/4; spec §4.2 rows pinned in `interscript-rs/tests/wf1.rs` |
| W2 `use <alias>.<ruleset>` across dependency | Y | Y | Y | Y | `rs-wf-override*` corpus maps; `tst-usedep-missing` errors named 4/4 |
| W3 `languages` decl + `when` guards — parse | Y | Y | Y | Y | `pp-langs-when` |
| W3 selection of a **declared** language (§5.2 guard precedence) | Y | Y | Y | Y | `tst-lang-undecl --lang kur` → `Q` 4/4 |
| W3 undeclared selection / no selection → guards inert (§5.1) | Y | Y | Y | **D** rs activates the guard | [G2](#g2--rs-ignores-the-w3-languages-declaration-spec-51) |
| comments in item/stage position; `#` strictness | Y | Y | Y | Y | corpus-wide parse sweeps (§A.5) |

### A.2 Execution semantics

| feature | ruby | ts | py | rs | notes |
|---|---|---|---|---|---|
| parallel tree mode (last-wins trie, longest-match-first) | Y | Y | Y | Y | `tst-dup-parallel` `X` 4/4 |
| megaregexp fallback (constraint/re-only-alias blocks) | Y | D | D | Y | [G1](#g1--captureref-inside-parallel-blocks-corrupt-output-ts-py-accidental-crash-ruby) |
| longest-match precedence within a parallel pass | Y | Y | Y | Y | `tst-longest` `1` 4/4 |
| W3 guard filtering, §5.2 shadowing (guard-applicable beats unguarded same-from) | Y | Y | Y | Y | `tst-lang-undecl` rows |
| duplicate froms in one parallel block (last wins) | Y | Y | Y | Y | `tst-dup-parallel` |
| duplicate froms in a sequence (later overwrites) | Y | Y | Y | Y | `tst-dup-seq` `1` 4/4 |
| empty input | Y (`""`) | Y | Y | Y | battery `sanity-basic-empty-input` |
| missing **main** stage | **D** accidental `NoMethodError` | D silent no-op | D silent no-op | **D** named `MapLogicError` | [G4](#g4--missing-stage-behavior-four-behaviors-rubys-is-an-accidental-crash) |
| missing **run-target** stage | **D** accidental `NoMethodError` | Y named | Y named | Y named | [G4](#g4--missing-stage-behavior-four-behaviors-rubys-is-an-accidental-crash) |
| missing dependency (run target) | Y named (parse-time) | Y named | Y named | Y named | battery `missing-dependency` |
| unknown alias in `from` | Y named `SystemConversionError` | **D** silent empty-match corruption | **D** silent empty-match corruption | Y named load error | [G3](#g3--unresolved-aliases-compile-to-the-empty-matcher-in-ts-and-py-silent-corruption) |
| funcall literal (`downcase`/`upcase`/…) in `from` position | D named `MapLogicError` | D silent empty-match corruption | D silent empty-match corruption | D silent rule-drop | [G6](#g6--keyword-table-and-fn-literal-in-from-three-ways) |
| reverse mode (reversed document execution) | **P** node-level `Document#reverse` + DSL reverse-name load fallback; no CLI | **N** | **N** | **Y** full + `iscrs reverse` | [G10](#g10--reverse-mode-absent-in-ts-and-py) |
| `transliterate_each` (ambiguity enumeration) | **Y** only here | N | N | N | ruby `Interscript.transliterate_each` |

### A.3 Loader surfaces

| feature | ruby | ts | py | rs |
|---|---|---|---|---|
| directory load path, stem resolution | Y (`Interscript.load_path`) | Y (strategies) | Y (`MapLoader` dirs) | Y (`Runtime` load path, `$ISCRS_MAPS`) |
| `.isc` maps | Y | Y (direct API + HTTP `iscStrategy`) | Y (`parse_isc` API only — not loader-integrated) | Y |
| `.iml` charset libraries | Y | N | N | Y |
| legacy `.imp` Ruby-DSL maps | Y (DSL eval) | N | N | P (named `Unsupported` at load) |
| JSON-IR artifact loading (`interscript.maps.ir.v1`) | N (ruby **emits** IR: `Compiler::JsonIR` — no loader) | **Y** primary (filesystem/bundled/HTTP strategies) | **Y** primary (+ manifest, sha256 `verify_artifact`, release tarball extraction) | N |
| dependency resolution point | parse time (DSL), lazy import at exec | expand time (resolver) + exec time (runtime loader, IR only) | parse time (fused into `parse_isc`, resolver kwarg) + exec time (IR loader only) | load time (`.isc` load path) |
| bare `parse_isc`/`parseIsc` on the full corpus | n/a (ruby parses with lazy deps: 428/428) | Y 428/428 (expansion is a separate step) | **N 422/428** — the 6 WF-1-adopting maps fail without a resolver kwarg | Y 428/428 (load path) |
| registry aliases (`interscript-maps.yaml` map aliases) | Y (`Interscript.map_aliases`) | N | N | N |
| release fetch command | N (rubygems distribution) | N (HTTP strategy instead) | Y (`python -m interscript.artifact_fetch`) | Y (`iscrs maps-fetch`, checksum-verified) |
| reverse-name load fallback (`parse("a-Latn-Cyrl-x")` auto-reverses) | Y | N | N | N |

### A.4 Neural / IMF (IMF v1, ByT5 ONNX)

| feature | ruby | ts | py | rs |
|---|---|---|---|---|
| IMF v1 artifact loading (zip manifest + sha256) | Y (`Interscript::ML::IMF`) | Y (`ml/imf/loader`) | Y (`models/loader`) | Y (`imf/loader`) |
| models.yaml registry resolve + cached download (`index-vN`) | Y | Y (`ml/imf/registry`) | Y (`models/registry`) | Y (`imf/registry`, `$SECRYST_INDEX/$SECRYST_CACHE`) |
| greedy single-row inference | Y (`ML::Translator#translate`) | Y (`ml/imf`) | Y (`models.Model`) | Y (`iscrs infer`) |
| ByT5 byte table (byte+3, trailing EOS) | Y (`ml/vocab`) | Y (`ml/imf/tokens`) | Y (`models/tokens`) | Y (`imf/tokens`) |
| plane model | Y (`ml/plane`) | Y (`ml/models/plane`) | N | N |
| rababa adapter (funcall) | P (requires `rababa` gem + provisioned model; named `ExternalUtilError` otherwise) | Y (onnx sessions, node+web) | Y (mount handler; named `AsyncFunctionError` until mounted) | **N** (named `Unsupported` at load — slice-1 boundary) |
| secryst adapter (funcall) | Y (`stdlib/functions/secryst_adapter`) | Y (`ml/models/secryst`) | Y (mount handler) | **N** (same slice-1 boundary) |
| conformance harness (frozen fixture families) | Y (spec, env-gated `CONFORMANCE_VECTORS`) | Y (`test/conformance.test.ts`) | Y (`conformance.py`) | Y (`imf/conformance` + `iscrs conformance`) |

### A.5 Corpus parse sweeps (428 maps, this machine)

| runtime | result | how |
|---|---|---|
| ruby | 428/428 | `Interscript::Interpreter.parse_isc` over `maps/*.isc` |
| ts | 428/428 | `parseIsc` sweep (`iscrs`-equivalent parse-only) |
| py | 422/428 bare; **428/428 with a dependency resolver** | bare `parse_isc` fails exactly 6 maps that `use` dependency-declared rulesets: `alalc-jav-Arab-Latn-2012`, `alalc-jba-Hebr-Latn-2011`, `alalc-lad-Hebr-Latn-2025`, `alalc-tha-Thai-Latn-2011`, `alalc-zsm-Arab-Latn-2011`, `bgnpcgn-tha-Thai-Latn-2002` (`cannot resolve dependency … no resolver provided`) |
| rs | 428/428 | `iscrs parse <dir> --maps <dir>` (`{"parsed": 428, "failed": 0}`) |

### A.6 CLI surfaces

| command | ruby `bin/interscript` | ts `interscript` (dist/cli.js) | py | rs `iscrs` |
|---|---|---|---|---|
| transliterate | Y (`translit <file> -s SYS [-o out] [-c compiler]`) | Y (`transliterate`/`t`, stdin/`-i`/`-o`) | N (library only) | Y (`transliterate <map> <str> [--stage] [--language]`) |
| batch/file input | Y (`translit` file → file) | Y (`batch <sys> <file> [--csv]`) | N | N |
| list maps | Y (`list`) | Y (`list` + `--authority/--source-script` filters) | N (`map_list()` API) | N |
| reverse | N | N | N | **Y** (`reverse <map> <str>`) |
| corpus test runner | N (RSpec owns this) | N (vitest owns this) | N (pytest owns this) | **Y** (`test`, `test-all [--json]`) |
| parse sweep | N | N | N | **Y** (`parse`, `parse-all [--json]`) |
| golden capture | N | N | N | **Y** (`capture [-o] [--root]`) |
| grammar self-test | N | N | N | **Y** (`grammar-test`) |
| detect (map identification) | N | **Y** (`detect <in> <out>`) | N | N |
| ML infer / conformance | N | N | N | **Y** (`infer`, `conformance`) |
| artifact fetch | N | N | Y (`python -m interscript.artifact_fetch`) | **Y** (`maps-fetch <version>`) |
| stats | Y (`stats`) | N | N | N |

### A.7 Auxiliary APIs

| capability | ruby | ts | py | rs |
|---|---|---|---|---|
| detector (which map explains in→out) | Y (`Interscript.detect`) | **Y** (`detector.ts`, mirrors ruby) | N | N |
| equivalence check between two systems | Y (`equivalence.rb`) | **Y** (`equivalence.ts`) | N | N |
| map visualization | Y (`visualize/`) | N | N | N |
| cross-compilers (emit Ruby/Python/JS source) | Y (`Compiler::Ruby/Python/Javascript` — legacy, CI-maintained) | N (ts **is** a target) | N | N |
| JSON-IR emission | Y (`Compiler::JsonIR`, SCHEMA_VERSION 1) | N (consumes) | N (consumes) | N |

### A.8 Corpus parse timing (428 maps, median of 3)

Machine: macOS 14 (Darwin 23.1.0), apple-silicon. Methodology: clean
serial runs — one runtime at a time, nothing else executing; in-process
timing loops for ruby/ts/py (`Process.clock_gettime` /
`performance.now()` / `perf_counter` around the sweep), wall-clock for
rs's `iscrs parse <dir>` (adds ~20 ms process startup). "Parse" =
each runtime's native parse entry over `maps/*.isc` sorted, with each
runtime's native dependency semantics (see A.5; py measured with a
resolver over `maps/`+`libs/` — its bare entry cannot take the corpus).
Scripts: `probes/time-ruby.sh`, `time-ts.mjs`, `time-py.py`; rs via
`iscrs parse`. Raw transcript: `probes/results/timing.txt`.

| runtime | runs (ms) | median | per-map mean |
|---|---|---|---|
| ts (`parseIsc`) | 16742.8 / 15826.8 / 15986.5 | **15986 ms (~16.0 s)** | ~37 ms |
| py (`parse_isc` + resolver) | 77839.3 / 80709.3 / 81024.7 | **80709 ms (~80.7 s)** | ~189 ms |
| rs (`iscrs parse`, release, wall) | 81410 / 79220 / 77490 | **79220 ms (~79.2 s)** | ~185 ms |
| ruby (`Interscript::Interpreter.parse_isc`) | 186029.0 / 156782.2 / 161449.9 | **161450 ms (~161.5 s)** | ~377 ms |

**WO18 update (2026-11-13):** py's generated parser is now
closure-compiled (interscript-ruby: rules compile once into Python
closures at load; capture values folded where the flattener would).
Controlled before/after in the perf session: **~78 s → ~22 s per
corpus pass (~3.5x)**, byte-identical output (py-vs-py parity driver
435/435 on both projections; embedded suite unchanged; golden green
in-suite). The table above records the audit-day baseline and is kept
for comparability; py's current expectation is the ~22 s line.

Single-map spot checks (clean, cold):

- rs, `bgnpcgn-rus-Cyrl-Latn-1947.isc`: **0.03 s**;
  rs, `acadsin-zho-Hani-Latn-2002.isc` (42,761 lines): **6.5 s**,
  `var-zho-Hani-Latn-wd-1979.isc` (42,802 lines): **6.5 s** — the two
  zhōngwén maps alone are ~13 s of rs's 79 s corpus total.
- ruby, `acadsin-zho-Hani-Latn-2002.isc`: **6.7 s**.
- ts, `var-zho-Hani-Latn-wd-1979.isc`: **1.7 s**.

Interpretation: the PEG-interpreter engines (ts 16 s, py 81 s, rs 79 s)
bracket the parslet-based ruby (161 s) — ts is ~10x faster than ruby on
this sweep. Per-map cost on normal-sized maps is low single-digit ms
for ts and tens of ms for the others; the huge zhōngwén maps carry a
disproportionate share of every engine's total. Earlier informal
readings (taken while other corpus parses ran concurrently) were up to
5x inflated by CPU contention — the numbers above are the clean
series. Parse throughput is not parity-relevant for correctness; the
per-engine hot spots are a note for a future perf campaign.

---

## B. Behavioral divergence battery

### B.1 Probe suite

`probes/` contains, all runnable:

- `driver.rb` / `driver.mjs` / `driver.py` / `driver-rs.sh` — one driver
  per runtime, uniform output contract `OK<TAB>result` /
  `ERR<TAB>Class<TAB>message`. The ts driver uses the production path
  (`parseIsc → expandDocument → iscToCompiledMap → normaliseMap →
  executeStage` with a `MapLoader` for dependency stage-runs); the py
  driver uses `parse_isc → isc_to_compiled_map → execute_stage` with an
  IR `MapLoader` for dependencies.
- `maps/` — 30+ probe maps (`tst-*` behavior probes, `pp-*` grammar-surface
  probes, `kw-*` keyword-table probes).
- `build-ir.mjs` — emits the JSON IR of every probe map into `maps/_ir/`
  (the shared artifact form both ts and py loaders consume).
- `run-parse.sh` (grammar-surface sweep), `run-kw.sh` (keyword tables),
  `run-battery.sh` (the 38-case behavior battery), `time-*.sh/.mjs/.py`
  (corpus timings).
- `results/` — raw outputs committed alongside (`battery.tsv`,
  `parse-results.tsv`, `kw-results.tsv`).

### B.2 Keyword tables

44 candidate identifiers probed in alias-name position (`kw-<ident>.isc`).
37 agree across all four runtimes; 7 diverge:

| identifier | ruby | ts | py | rs |
|---|---|---|---|---|
| `downcase` | KW | ok | ok | ok |
| `reverse` | KW | ok | ok | ok |
| `ruleset` | KW | KW | KW | ok |
| `strip` | KW | ok | ok | ok |
| `swapcase` | KW | ok | ok | ok |
| `title_case` | KW | ok | ok | ok |
| `upcase` | KW | ok | ok | ok |

(remainder: all KW in all four — `parallel`, `sequence`, `stage`, `sub`,
`use`, `override`, `languages`, `when`, `capture`, `ref`, …)

Sources: ruby's effective table = the vendored parg `keyword` list
(`grammar/isc.parg:113`) **plus** the WF-1 keywords and the fn-literal
names added by the concern layer (`lib/interscript/isc/grammar/concerns/items.rb:129-135`);
rs deliberately omits `ruleset` (`interscript-rs/grammar/isc.parg:119-122`
— "`ruleset` deliberately stays OUT (§2 lists exactly these four)");
ts and py keyword all of them (`grammar-source.ts` / `grammar_source.py`
`keyword` production).

Corpus equivalence: a ruby sweep of all 428 corpus maps (alias names +
stage names + dependency aliases vs the full keyword list) reports
**zero collisions**, so both divergence groups are latent only —
documented as such in ISC-WF-1 §2 ("no corpus map uses any of these
five words as bare identifiers; verified against the corpus at adoption
time"). This audit re-verifies that claim and extends it: the six
fn-literal keywords ruby reserves (`upcase` `downcase` `title_case`
`reverse` `strip` `swapcase`) also collide with no corpus identifier.
The corollary divergence — what happens when such an identifier IS used
— is [G6](#g6--keyword-table-and-fn-literal-in-from-three-ways).

### B.3 Behavioral battery results

38 cases × 4 runtimes; full raw output in
[`probes/results/battery.tsv`](probes/results/battery.tsv), full
markdown table in
[`probes/results/battery-table.md`](probes/results/battery-table.md).
Diverging rows condensed (rs error text is the `iscrs` Display string;
classes normalized per runtime):

| probe | ruby | ts | py | rs |
|---|---|---|---|---|
| missing-main-stage | ERR NoMethodError `undefined method 'reverse_run' for nil` | OK `aaa` (silent no-op) | OK `aaa` (silent no-op) | ERR MapLogicError `stage "main" not found in tst-nomain` |
| dependency-missing-stage | ERR NoMethodError `undefined method 'reverse_run' for nil` | ERR MapLogicError `Stage not found: nothere` | ERR MapLogicError `stage not found: nothere` | ERR MapLogicError `stage "nothere" not found in tst-dep-lib` |
| unknown-alias | ERR SystemConversionError `Alias undefined_alias not found` | **OK `XaX`** (silent corruption) | **OK `XbX`** (silent corruption) | ERR MapLogicError `alias "undefined_alias" not found during expansion` |
| ruleset-cycle (dup-def + use-in-blocks) | ERR ParseError | ERR IscParseError | ERR IscParseError `ruleset declared more than once: a` | **OK `1yz`** (executes the order-dependent merge) |
| rs-duplicate-def (dup defs, stage-level use) | OK `1z` (first def wins) | OK `1z` | **ERR** `ruleset declared more than once: a` | OK `1z` |
| rs-cycle-bare (pure cycle) | ERR MapLogicError `use cycle: ruleset a revisited through a -> b` | ERR IscLoadError `use cycle: …` | ERR IscParseError `use cycle: …` | ERR MapLogicError `use cycle: a -> b -> a` |
| use-in-sequence | ERR ParseError (grammar) | ERR IscParseError (grammar) | ERR IscParseError `a ruleset containing a parallel/sequence block cannot be used inside a parallel/sequence block` | **OK `12`** |
| lang-selected-nodeclaration | OK `K` (guard inert) | OK `K` | OK `K` | **OK `Q`** (guard applied) |
| capture-parallel (`axb`) | ERR NoMethodError `undefined method 'max_length' …CaptureGroup` | **OK `axXB`** (wrong) | **OK `axXB`** (wrong) | OK `aXB` |
| capture-par2-shift (`k3a`) | ERR NoMethodError `undefined method 'max_length' …CaptureGroup` | **OK `kk3a`** (wrong) | **OK `kk3a`** (wrong) | OK `3ka` |
| fnlit-in-from (`downcase`) | ERR MapLogicError `Wrong type Symbol, expected I::Node::Item` | **OK `XdXoXwXnXcXaXsXeX`** | **OK `XdXoXwXnXcXaXsXeX`** | OK `downcase` (rule silently dropped) |
| funcall-upcase-exec | ERR NoMethodError `undefined method 'upcase' for module Interscript::Stdlib::Functions` | OK ` ABC` | OK ` ABC` | OK ` ABC` |
| ml-funcall-rababa | OK `Ka` * (env-provisioned on this machine; named `ExternalUtilError` without) | ERR `Stage "main" contains ML function calls (rababa/secryst). Use transliterateAsync()` | ERR AsyncFunctionError `model layer is not mounted…` | ERR Unsupported `funcall "rababa" … not in slice 1` |
| ml-funcall-rababa-bare | ERR ArgumentError `missing keyword: :config` | ERR (same sync-guard) | ERR AsyncFunctionError | ERR Unsupported |
| reverse-lossy | OK `ac` | N (no reverse) | N (no reverse) | OK `ac` |
| missing-map | ERR MapNotFoundError | ERR MapNotFoundError | ERR MapNotFoundError | ERR MapNotFoundError |

(Consistent rows omitted from this condensed table — sanity, duplicates,
overrides, declared-language selection, library-dep alias merge,
longest-match, empty input, missing dependency, missing-dep-ruleset use —
all 4/4 agreements; see the TSV for the full 38.)

\* ruby's `ml-funcall-rababa` cell: this machine has the `rababa` gem
(0.1.1) installed and the model cached, so the reference executed real
inference. The canonical unprovisioned behavior is the named
`ExternalUtilError` (`stdlib/functions/rababa_adapter.rb:32-38`,
`42-48`).

---

## C. Ranked gap list

Ranking: silent wrong output > spec violation > accidental crash >
fail-loud divergence > feature absence > surface asymmetry.

### G1 — capture/ref inside parallel blocks: corrupt output (ts, py); accidental crash (ruby)

- **What.** A `sub` with `capture(...)`/`ref(N)` inside a `parallel`
  block produces silently WRONG output in ts and py. `capture([a-z])+"x" → ref(1)+"X"`:
  input `ax` → ruby crashes, ts/py emit `axX` (expected `aX`), rs emits
  `aX`. With two captures and a preceding plain rule: input `k3a` →
  ts/py emit `kk3a` (expected `3ka`), rs emits `3ka`.
- **Why it happens.** Both engines join the parallel rules into one
  alternation wrapping each rule in a named group
  (ts `src/stdlib.ts:188-213 parallelMegaregexp`; py
  `src/interscript/stdlib.py:115-141 parallel_megaregexp`). The replace
  callback then hands the template resolver the GLOBAL group list,
  which now contains the named wrapper groups — so `$1` in a `ref(1)`
  template resolves to the wrapper's whole match instead of the rule's
  first capture. py's docstring even codifies the shifted numbering
  ("the group also shifts inner capture numbering exactly as in the
  TS/Ruby engines") — but the `$N` templates are built 1:1 from ref
  ids and never compensated.
- **Ruby reference.** ruby rejects captures from the tree path by
  design (`interpreter.rb:273-276` "Can't use a CaptureGroup in a par
  context"), but the megaregexp fallback then crashes with an
  accidental `NoMethodError: undefined method 'max_length'` —
  `Item::CaptureGroup` has no `max_length`
  (`stdlib.rb:171 deterministic_sort_by_max_length`,
  `interpreter.rb:166-173`). So ruby's net behavior is also broken,
  just loudly.
- **Canonical.** rs (correct capture math; `interpreter.rs:938` handles
  the Function/CaptureGroup parallel cases deliberately, and the
  battery's `tst-capture-par2` pins the correct output), or at minimum
  ruby's deliberate named rejection. The
  current ts/py behavior is the worst of both worlds: neither correct
  nor loud.
- **Fix scope.** ts: group-offset math in `parallelMegaregexp` +
  `buildReplacement` (or reject captures in parallel with
  `MapLogicError`). py: same in `parallel_megaregexp`. ruby: give
  `Item::CaptureGroup`/`CaptureRef` a `max_length` (or skip-with-named-
  error in the sort) so the intended `SystemConversionError` surfaces.
  rs: none.

### G2 — rs ignores the W3 `languages` declaration (spec §5.1)

- **What.** Selecting a language the map does NOT declare must leave
  every `when` guard inert (spec §5.1; §6 conformance item 5 "reports
  unselected-language inertness identically"). ruby/ts/py do; rs
  activates matching guards: `tst-lang-nodecl --lang kur` → ruby/ts/py
  `K`, rs `Q`.
- **Why.** rs's `guard_applies` (`src/document.rs:68-71`) checks only
  the rule's `when` list against the selection; nothing consults
  `Document.languages` (`document.rs:136-137`, populated
  `builder.rs:60-88`). rs's own docstring (`interpreter.rs:111-113`) and
  CLI help ("guards inert when the map does not declare LANG") promise
  the gate — it is documented but not implemented.
- **Canonical.** ruby/ts/py (the spec text).
- **Fix scope.** rs only: gate the selection on `doc.languages` in
  `transliterate_lang`/`execute_stage`.

### G3 — unresolved aliases compile to the EMPTY matcher in ts and py (silent corruption)

- **What.** `sub unknown_alias "X"` — ruby raises
  `SystemConversionError "Alias … not found"` at execution
  (`interpreter.rb:254`); rs raises at load (`builder.rs:502`); ts and
  py compile the alias to `re: ""` and silently insert `X` at every
  string boundary: input `a` → ts `XaX`, py `XbX`; input `zzz` →
  `XzXzXzX`.
- **Why.** ts `src/runtime/compile-item.ts:65` — `if (!resolved) return
  { re: "", literal: "" }`; py `src/interscript/items.py:101-102` —
  `if resolved is None: return _compiled("", "")`. Same defect class
  fires when a dependency-imported alias cannot be resolved at runtime
  (loader missing the dep).
- **Canonical.** Fail loud. ruby is the reference and the project's
  stated philosophy prefers named errors over accidental behavior; an
  empty matcher is never a legitimate alias semantics.
- **Fix scope.** ts + py: raise `MapLogicError` on unresolved alias
  (message mirroring ruby/rs).

### G4 — missing-stage behavior: four behaviors; ruby's is an accidental crash

- **What.** Requesting a stage the map doesn't have:
  - missing **main** stage — ruby: `NoMethodError` (accidental:
    `interpreter.rb:9` `stage = @map.stages[stage]` → nil; nil flows into
    `execute_rule` and crashes at `interpreter.rb:134`); ts/py: silent no-op
    returning the input (`runtime/interpreter.ts:65-67`,
    `executor.py:83-84` — py's docstring says "matching the TS
    runtime"); rs: named `MapLogicError "stage \"main\" not found"`
    (`interpreter.rs:205-208`).
  - missing **run-target** stage — ruby: `NoMethodError undefined
    method 'reverse_run' for nil` (`interpreter.rb:205-213`: `imported_stages[...]`
    → nil at 207/211, `execute_rule(nil)` crashes at 134); ts/py/rs: all named `MapLogicError`.
- **Canonical.** rs's named error. The project convention is fail-loud;
    ruby's crash is accidental (nil dereference), and the ts/py silent
    no-op hides map typos (`--stage mahn` silently "works"). Note this
    is an API-visible change for ts/py consumers who rely on the no-op;
    the minimal uncontroversial step is fixing ruby's crash to the
    named error and aligning run-target semantics (already named in
    ts/py/rs).
- **Fix scope.** ruby: named `MapLogicError` at both sites. ts/py:
    campaign decision — named error recommended for parity with rs/ruby
    (post-fix); document if the no-op is kept deliberately.

### G5 — `use` inside sequence/parallel blocks: only rs implements spec §3.2

- **What.** The spec explicitly allows it: "items inside a `parallel`
  block participate in that block's single pass; a ruleset containing a
  `parallel` block contributes that block as one pass at the expansion
  position" (§3.2). rs executes this (`tst-use-inseq` → `12`); ruby/ts
  reject at the grammar (`rule_line` lacks `use_directive` — ts
  `grammar-source.ts` vs rs `grammar/isc.parg:217-219`); py parses it
  but rejects at expansion with "a ruleset containing a
  parallel/sequence block cannot be used inside a parallel/sequence
  block".
- **Canonical.** The spec (rs). Corpus-equivalent today — all 428 maps
  parse on ruby, whose grammar rejects use-in-block, proving no corpus
  map uses it; but WF-1 adopting maps in staging could.
- **Fix scope.** ruby: add `use_directive` to the concern `rule_line`
  + expansion into groups. ts: same in `grammar-source.ts` +
  `expand.ts`. py: keep the parse, drop the containment rejection in
  `isc.py`. rs: none.

### G6 — keyword table and fn-literal-in-from: three ways

- **What.** Two keyword-table groups diverge (B.2): `ruleset`
  (rs-only identifier) and the six fn-literal names (ruby-only
  keywords). The fn-literal group has behavioral consequences beyond
  parse acceptance: `sub downcase "X"` parses in ts/py/rs as a
  FUNCALL LITERAL in from position (portable `item_atom` tries
  `fn_lit` before `alias_reference`), and then:
  ruby `MapLogicError "Wrong type Symbol, expected I::Node::Item"`
  (`node/item.rb:45` via `try_convert`); ts/py: empty-from corruption
  (boundary insertion, same defect as G3 — `compile-item.ts:60-67`,
  `items.py` fn branch); rs: rule silently dropped (`interpreter.rs:938`
  "Function items have no build_item case -> nil -> no keys").
- **Canonical.** Two rulings needed from the owner:
  1. one keyword table (recommend: ruby's effective table is the
     reference; adding the six fn names to the portable grammars'
     keyword list makes `downcase = any(...)` an alias everywhere —
     today ts/py/rs parse it as a funcall reference instead);
  2. fn-literal-in-from semantics (recommend: named error everywhere —
     ruby's outcome; rs's silent drop and ts/py's silent corruption
     both hide map bugs).
- **Fix scope.** keyword alignment: ts+py grammar-source + rs parg
  (one line each) — with the corpus-equivalence proof above, zero
  corpus impact. fn-from: ts/py raise `MapLogicError`; rs decide
  (drop→error). ruby: none.

### G7 — duplicate ruleset definitions: only py rejects

- **What.** `ruleset a` declared twice: py raises named load error
  (`grammar/actions.py:139`); ruby/ts silently keep the FIRST
  definition; rs silently merges with order-dependent expansion —
  with `use` inside blocks the merge can produce content from BOTH
  definitions (`tst-rscycle` → rs `1yz` executes x→1 AND z→3) while
  the same map at stage-level `use` yields first-def-wins (`1z`).
- **Canonical.** py's fail-loud (an extension of spec §6 item 4's
  cycle rejection to duplicate definition).
- **Fix scope.** ruby + ts: duplicate check at parse/expansion; rs:
  duplicate check in `builder.rs` ruleset table.

### G8 — ruby does not implement four fn literals (`upcase`, `reverse`, `strip`, `swapcase`)

- **What.** The grammar accepts them as stage directives and `to`
  funcalls in all four runtimes; ruby's `Stdlib::Functions`
  (`stdlib/functions.rb`) implements only `title_case`, `downcase`,
  `compose`, `decompose`, `separate`, `unseparate`, `secryst`,
  `rababa`, `rababa_reverse` — exactly the set
  `Stdlib.available_functions` declares (`stdlib.rb:178-180`).
  Executing `upcase`:
  `NoMethodError: undefined method 'upcase' for module
  Interscript::Stdlib::Functions` (probe `funcall-upcase-exec`);
  ts/py/rs implement it and agree (` ABC`).
- **Canonical.** ts/py/rs (the ISC surface includes the directive;
  the ruby reference is incomplete). Note `Interscript::Stdlib` has a
  `reverse_function` helper (`stdlib.rb:182`; not a `Functions` member the dispatcher can reach) and the interpreter
  handles `to == :upcase/:downcase` as special-case symbols
  (`interpreter.rb:195-199`) — the legacy compiler paths cover some of
  this; the Interpreter path does not.
- **Fix scope.** ruby: add the four functions to
  `Stdlib::Functions` (upcase/reverse/strip/swapcase) with the ts
  semantics as reference.

### G9 — ruleset redefinition/cycle error classes and parse-error verbosity

- **What.** Same semantic failure, four different surfaces: pure cycle
  = ruby `MapLogicError`, ts `IscLoadError`, py `IscParseError`
  (load-phase error reported under the parse class —
  `isc.py:270-273` routes through `self.error`), rs `MapLogicError`.
  Ruby's parse failures additionally print the full expected-set
  (multi-hundred-char "expected one of [(?-mix:\s), '#', …]" — see
  battery rows), which is unusable for map authors compared to
  ts/py/rs's `line:col` pointers.
- **Canonical.** Behavior is already correct everywhere (all fail
  loud); this is a classification/usability cleanup, lowest priority.
- **Fix scope.** py: introduce a load-phase error class;
  ruby: trim the expected-set in `ParseError#message`.

### G10 — reverse mode absent in ts and py

- **What.** ruby has node-level `Document#reverse` (whole `node/*`
  family, `reversibility_spec.rb` pins round-trips) plus the DSL's
  reverse-name load fallback (`dsl.rb:30-39`); rs mirrors it fully
  (`src/reverse.rs`, `iscrs reverse`, `tests/reverse.rs` pins
  ruby-generated expectations, including the documented ruby-crash
  deviations); ts and py have nothing (`grep -rn reverse src/` in both
  finds no reverse implementation).
- **Canonical.** rs is the port reference (it pins ruby behavior
  including where ruby crashes). Whether ts/py SHOULD have reverse is
  an owner decision — as a feature gap it is silent (no wrong output),
  hence mid-table.
- **Fix scope.** if approved: port `interscript-rs/src/reverse.rs` to
  ts/py; both runtimes need no grammar change.

### G11 — bare `rababa` (no kwargs): ruby `ArgumentError`

- **What.** `rababa` without `config:` parses everywhere; ruby
  executes into `ArgumentError: missing keyword: :config`
  (`stdlib/functions.rb:41` `def self.rababa(output, config:)` vs the
  grammar's optional kwargs `isc.parg:215`); ts/py give the named
  provisioning error, rs the load-time Unsupported.
- **Canonical.** A named map-logic error ("rababa requires config:")
  rather than a Ruby-level ArgumentError. Minor.
- **Fix scope.** ruby: validate at interpreter funcall dispatch.

### G12 — loader/asymmetry (documented, not bugs)

- py's bare `parse_isc` cannot ingest 6 corpus maps (dependency
  ruleset `use`) without the caller supplying `resolve_dependency` —
  the only runtime whose single-call parse entry is not
  corpus-complete (A.5). ts splits parse (`parseIsc`) from expansion
  (`expandDocument`), so its parse entry is complete; ruby/rs resolve
  via load path.
- ts/py dependency stage-runs require the dependency as JSON IR at
  runtime (no `.isc` runtime loader); ruby/rs resolve `.isc`
  dependencies natively. ts's `iscToCompiledMap` returns a plain
  `aliases` object — executing it WITHOUT `normaliseMap` crashes
  (`this.map.aliases.get is not a function`,
  `runtime/context.ts:46` vs `isc/converter.ts:64,91,99`); the
  production path always normalises, but the public export invites
  the misuse (my first driver draft hit exactly this).
- IR is emitted only by ruby (`Compiler::JsonIR`), loaded only by
  ts/py; rs neither loads nor emits IR.

### Timing postscript (feeds the perf campaign, not parity fixes)

The two ~43k-line zhōngwén maps carry a disproportionate share of every
engine's corpus parse time (rs 6.5 s each of its 79 s total; ruby
6.7 s; ts 1.7 s) — see §A.8 for the clean series.

---

## Reproducing

```sh
cd docs/parity/probes
./run-parse.sh        # grammar-surface sweep (pp-*)   -> results/parse-results.tsv
./run-kw.sh           # keyword tables (kw-*)           -> results/kw-results.tsv
node build-ir.mjs     # emit IR for the probe maps into maps/_ir/
./run-battery.sh      # 38-case behavior battery        -> results/battery.tsv
./time-all.sh         # clean serial corpus-timing series -> results/timing.txt
```

Drivers reference the four runtime trees by absolute path
(`~/src/interscript/…`); adjust the constants at the top of each driver
for other checkouts. rs errors are normalized from `iscrs`'s stderr
Display strings (`map logic error: …` → `MapLogicError …`).
