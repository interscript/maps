# ISC-WF-1 — Workflow extension for the ISC language

Status: **Normative draft 1.0** (WO16). Approved semantics; additive
only. Conformance requirements are binding on every Interscript
runtime (Ruby, TypeScript, Python, Rust).

Related: `TODO.all-sys/16-workflow-extension.md` (motivation and work
order), `TODO.all-sys/INDEX.md`.

---

## 1. Scope

ISC-WF-1 extends the ISC language with three constructs:

- **W1 — named rulesets**: a reusable, named block of rules inside a
  map (or inside a dependency of the map).
- **W2 — use with override**: expansion of a ruleset at a stage
  position, with per-site row overrides (child-wins on exact
  from-equality).
- **W3 — language conditioning**: rules guarded by the declared
  languages of the map, selected at call time.

Everything not defined here is unchanged. The base language, its
stage semantics (parallel = one simultaneous longest-match pass;
document order across blocks), `dependency` + `run` composition,
`before`/`after` constraints, `any`/`boundary` primitives, and all
existing funcalls keep their current definitions. **Additivity
requirement**: a map that uses none of W1–W3 produces byte-identical
transliteration output before and after a runtime implements this
spec. Enforcement: the golden-capture harness (§7).

## 2. Grammar additions

Informal productions (normative text; the parsanol grammar encodes
the same):

```
stage_item    = ... | use_directive | languages_decl
use_directive = "use" ident ( "override" braced_override_block )?
languages_decl= "languages" ident ( ","? ident )*
sub_rule      = ... ( "when" ident ( "," ident )* )?
```

- `ident` follows the existing identifier production.
- `languages` is declared once per map, inside the `system` block,
  alongside `metadata`.
- `when` attaches to a `sub` rule only (not to blocks).
- New keywords `use`, `override`, `languages`, `when` join the
  keyword table, as does `ruleset` (the block head; the ruby/ts/py
  grammars keyword it, the rs grammar keeps it out of its table with
  equivalent corpus behavior). Maps using them as identifiers retain
  pass-through behavior only via the existing quoted-string forms (no
  corpus map uses any of these five words as bare identifiers;
  verified against the corpus at adoption time, re-verified including
  the libraries at the pilot landing).

## 3. W1 — named rulesets

### 3.1 Syntax

```
ruleset <ident> {
  <stage body items>       # parallel/sequence blocks and bare subs
}
```

A ruleset may appear anywhere a stage may appear, at map top level.
A ruleset may reference dependencies exactly as a stage does
(`use` of a dependency-declared ruleset: §5).

### 3.2 Expansion semantics

`use <ident>` inside a stage body **expands the referenced ruleset's
items in place, at that position, in document order** — a macro
expansion, not a sub-run:

- The expansion is textual-equivalent: the stage behaves exactly as
  if the ruleset's items had been written at the `use` position.
- Expansion is recursive: a ruleset whose items contain `use` of
  another ruleset expands fully. Cycles are a load error
  (`use` cycle: the same map-id/ruleset-name chain may not revisit a
  ruleset).
- The expansion inherits the enclosing pass structure: items inside a
  `parallel` block participate in that block's single pass; a
  ruleset containing a `parallel` block contributes that block as one
  pass at the expansion position.
- A ruleset never executes on its own. A map that declares only
  rulesets and no `main` stage is a library (the existing
  library-map semantics).

### 3.3 Where rulesets live

- In the same map: `use <ident>`.
- In a dependency: declared with the existing `dependency "id" as
  alias` directive, referenced as `use alias.<ident>`. Resolution
  uses the existing dependency loading (declared dependencies only;
  no implicit corpus-wide lookups).

## 4. W2 — use with override

### 4.1 Syntax

```
use <ident> override {
  <sub rules>              # full replacement rows
}
```

The `override` block is part of the `use` directive — one syntax, one
site. There is no file-level or stage-level override scoping.

### 4.2 Merge semantics

Let R = the ordered list of rules produced by expanding the ruleset
(§3.2), and O = the ordered list of override rules.

1. Partition R into R_kept and R_replaced: a rule r ∈ R is **replaced**
   if there exists o ∈ O with `from(o) == from(r)` under byte-exact
   string equality (no Unicode normalization; the corpus convention).
   If multiple rules in R share that from-string, ALL of them are
   replaced (the winner of the ruleset's internal last-wins resolution
   is superseded too — an override is strictly stronger).
2. The effective expansion = R_kept (in R's order) followed by O (in
   O's order).
3. An override row is complete: it replaces the imported row's `to`
   value AND any constraints. An override row may also carry its own
   `when` guard (§5), which applies to that row alone.
4. Override rows whose from-strings match nothing in R are simply
   added (row 3 covers them — they appear at the end).
5. The whole expansion (R_kept + O) participates in the enclosing
   stage's single longest-match pass like any other rules.
6. Placement of O: when the expansion ends with a parallel block, O's
   rows join that block, so R_kept and O share one longest-match pass
   (replacement acts on the source-script pass, §4.3). Otherwise O
   appends after R_kept as stage-level rows.

### 4.3 Rationale notes (non-normative)

- Child-wins on exact from-equality is the narrowest definition that
  makes "same table, different value for these rows" deterministic;
  prefix- or constraint-based shadowing is deliberately NOT
  implemented.
- Replacement (not post-pass re-substitution) is required: after the
  base pass has emitted Latin text, re-targeting a single row's
  output is ambiguous against other rows sharing prefixes. Overrides
  must act on the source-script pass.

## 5. W3 — language conditioning

### 5.1 Declaration and selection

A map declares the languages it serves:

```
system "ISO:rus-Cyrl:Latn:9-1995" {
  languages rus bel ukr bul srp mkd
  ...
}
```

The caller selects one declared language for a transliteration call
(`transliterate(map, text, language: "kur")`; CLI `--language kur`).
Selection is optional:

- If the caller selects no language (or selects a language not in the
  map's `languages` declaration), all `when`-guarded rules are INERT,
  and the map behaves exactly as if those rules were absent.
- If the caller selects a declared language, every rule whose `when`
  list contains that language APPLIES; rules whose `when` lists omit
  it are INERT.

### 5.2 Pass semantics with guards

Within one parallel pass, the applicable rule set = unguarded rules ∪
guarded rules whose `when` matches the selected language. Matching is
the existing longest-match, with this precedence addition:

- If an unguarded rule and a guard-applicable rule have the SAME
  from-string, the **guard-applicable rule wins** (a language-specific
  value overrides the generic value for that language, without
  requiring the generic row to be restated).

Sequence blocks apply their rules in order; a guarded rule whose guard
is inert is skipped.

### 5.3 Relationship to `run` and W2

Guards compose with W1/W2: imported and overridden rows may carry
`when`. An override row's `when` replaces whatever the imported row
had (§4.2 rule 3).

### 5.4 Examples

```
system "ISO:rus-Cyrl:Latn:9-1995" {
  languages kur ckv
}
stage main {
  parallel {
    sub "қ" "ķ"            # generic (no language selected)
    sub "қ" "k̦" when kur   # Kurdish tradition
    sub "ҫ" "ş"            # generic
    sub "ҫ" "ș" when chv   # Chuvash tradition
  }
}
```

- `--language kur` → қ renders **k̦** (kur guard applies); ҫ renders
  **ş** (its `when chv` guard is inert).
- no language selected → қ renders **ķ**; ҫ renders **ş** (all
  guards inert; the generic rows apply).
- `--language chv` → қ renders **ķ** (kur guard inert); ҫ renders
  **ș** (chv guard applies).

## 6. Conformance requirements

A runtime conforms to ISC-WF-1 when it:

1. Parses all four constructs and rejects malformed forms with the
   existing parse-error surface.
2. Implements §§3–5 semantics exactly (expansion order, merge rules,
   guard precedence).
3. Preserves additivity: golden-capture zero-delta on maps not using
   the constructs (§1, §7).
4. Rejects `use`/override cycles at load time with a load error.
5. Reports unselected-language inertness identically (no partial
   application).

## 7. Additivity harness

Before any runtime change, a golden capture freezes: for every corpus
map, the output of every embedded-test input and the probe set, using
a conforming runtime. Each runtime merge re-runs the capture and MUST
show zero delta on maps whose source contains none of `ruleset`,
`use `, `override`, `languages `, `when ` (the non-adopting set).
Deltas on adopting maps are reviewed against this spec.

## 8. Worked examples

### 8.1 Shared machinery with per-map overrides (ALA-LC pattern)

```
dependency "alalc-tha-shared" as thairules

system "ALALC:tha-Thai:Latn:2011" {
  stage main {
    use thairules.leading_vowels override {
      sub "ะ" "a"      # 2011 guide differs from the shared base here
    }
    parallel {
      sub "ก" "k"
      ...
    }
  }
}
```

### 8.2 Language-conditioned variants (ISO 9 pattern)

See §5.4.

## 9. Canonical-adopted rs grammar extensions

The interscript-rs portable grammar (`grammar/isc.parg`) extends the
ruby-DSL concern grammar with four constructs. They are the canonical
spelling of the workflow extension — every other runtime adopts them
(ts/py through the sha-pinned portable grammar, ruby through the
concern layer). All four are parse-additive and corpus-dormant at
adoption: no map in the corpus uses any of them at a position the
pre-WF-1 grammar would have parsed differently (verified against the
corpus at adoption time, re-verified at the WO19 G6 round).

1. **`ruleset_decl`** — a named rule collection at document level
   (`ruleset <ident> { stage-items }`). A ruleset body is a stage
   body: it carries rules and rule-line items only — a funcall or
   stage `run` inside a ruleset is a load error, because ruleset
   content joins passes through W1 expansion (§3) where non-rule items
   cannot participate. Duplicate ruleset declarations in one document
   are a load error (WO18 G7).

2. **`use_directive`** — `use <ident>[.<ident>] [override { … }]`
   (§4). The bare form flattens the referenced ruleset's rules at this
   position; the `override` form replaces rows whose collapsed from-key
   matches, appending the survivors after the kept rows (§4.2, the
   trailing-parallel join of §4.2.6). A stage-line `use` participates
   in the stage like any other item; a `use` inside a
   `parallel`/`sequence` block joins that block's single pass (§3.2,
   ruby concern `rule_line`).

3. **`languages_decl`** — `languages <ident> (","? <ident>)*` at
   document level (§5.1). Declared once per map; a second declaration
   is a parse error. The declaration gates §5.1: a caller's language
   selection outside the declaration makes every `when` guard inert.

4. **`when` guard on `sub` rules** — a trailing ident list on a rule,
   inside the rule's own braces for the block form
   (`sub { from … to … when kur }`; canonical binding, ruby parses the
   inside form only — the ts/py outside-form tolerance was retired at
   WO19 G6 item 5) and after the constraints for the compact form
   (`sub "a" "b" when kur`). The list is comma- or whitespace-
   separated, keyword-guarded so it never swallows the next rule (§5.2).

The four new keywords (`use`, `override`, `languages`, `when`) join
the keyword table, as does `ruleset` (the block head; the ident-list
guards need every sibling block head keyworded). WO19 G6 item 1
completed the table alignment: the six fn-literal names
(`upcase` `downcase` `title_case` `reverse` `strip` `swapcase`) are
reserved in every runtime's keyword table, while `name = any(...)`
alias declarations remain valid (the `alias_decl` production has no
keyword guard).
