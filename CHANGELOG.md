# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.0] — 2026-08-26

- Corpus source format migrated from Ruby DSL (`.imp`) to ISC (`.isc`);
  transliteration parity verified at 100% across all 289 systems.
- New release channel: compiled JSON-IR artifacts
  (`interscript-maps-ir-<version>.tar.gz` + `.sha256`) attached to
  GitHub Releases by the `map-artifact` workflow; consumed by Workers
  deployments via the Assets binding.

## [Latest]

See GitHub releases for detailed release notes: https://github.com/interscript/maps/releases
