# CLAUDE.md — maps

The single source of truth for Interscript's transliteration corpus:
293 authority-backed systems in the ISC language (`.isc`), named per
ISO 24229. Project purpose and direction: `interscript-models` README.

## Facts that bite

- `.isc` is the only hand-edited form. Everything derived (the
  `interscript-maps` gem, release artifacts, index files) is built by
  CI from this corpus — never commit generated artifacts by hand.
- CI gates: ISC parse in Ruby + TypeScript, each map's embedded tests,
  cross-runtime parity against the test corpus. All must pass before
  merge.
- File names follow ISO 24229:
  `authority-language-SourceScript-TargetScript-year`, e.g.
  `bgnpcgn-rus-Cyrl-Latn-1947`.
- Alias/dependency resolution uses declared dependencies only.
- `maps-staging/` holds in-flight systems; promoted changes move into
  `maps/` through review.

## Laws

- PRs only, never commit to main.
- Transcribe the ENTIRE source document when encoding a system —
  every section, including unnumbered ones; omission falsifies the
  record.
- Never conflate bibliographic systems (e.g. ISO 9 — no vocalizer)
  with phonological systems (e.g. RTGS, BGN/PCGN phonological) — they
  are different families with different semantics.
