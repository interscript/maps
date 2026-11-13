| probe | ruby | ts | py | rs |
|---|---|---|---|---|
| sanity-basic | OK bcQ | OK bcQ | OK bcQ | OK bcQ |
| sanity-basic-empty-input | OK | OK | OK | OK |
| sanity-basic-stage-second | OK aBk | OK aBk | OK aBk | OK aBk |
| missing-main-stage | ERR NoMethodError undefined method 'reverse_run' for nil | OK aaa | OK aaa | ERR MapLogicError stage "main" not found in tst-nomain |
| missing-dependency | ERR Interscript::MapNotFoundError Couldn't locate nonexistent-map-xyz | ERR MapNotFoundError Map not found: nonexistent-map-xyz | ERR MapNotFoundError map not found: 'nonexistent-map-xyz' (load paths: /tmp/parity-probes/maps/_ir) | ERR MapNotFoundError map "nonexistent-map-xyz" |
| dependency-run-ok | OK AKA | OK AKA | OK AKA | OK AKA |
| dependency-missing-stage | ERR NoMethodError undefined method 'reverse_run' for nil | ERR MapLogicError Stage not found: nothere | ERR MapLogicError stage not found: nothere | ERR MapLogicError stage "nothere" not found in tst-dep-lib |
| dup-parallel | OK X | OK X | OK X | OK X |
| dup-sequence | OK 1 | OK 1 | OK 1 | OK 1 |
| unknown-alias | ERR Interscript::SystemConversionError Alias undefined_alias not found | OK XaX | OK XbX | ERR MapLogicError alias "undefined_alias" not found during expansion |
| ruleset-cycle | ERR Interscript::Isc::ParseError tst-rscycle.isc: Failed to match: expected one of [(?-mix:\s), '#', 'sub', '}'] at line 10 char 7. | ERR IscParseError ISC parse error at line 10:10: tst-rscycle.isc: Failed to match isc_source at line 10 char 10 | ERR IscParseError ISC parse error at line 26:1: tst-rscycle.isc: ruleset declared more than once: a | OK 1yz |
| override-basics | OK qtC | OK qtC | OK qtC | OK qtC |
| override-absent-row | OK Z | OK Z | OK Z | OK Z |
| lang-selected-declared | OK Q | OK Q | OK Q | OK Q |
| lang-selected-undeclared | OK K | OK K | OK K | OK K |
| lang-no-selection | OK K | OK K | OK K | OK K |
| lang-selected-nodeclaration | OK K | OK K | OK K | OK Q |
| capture-parallel | ERR NoMethodError undefined method 'max_length' for an instance of Interscript::Node::Item::CaptureGroup | OK axXB | OK axXB | OK aXB |
| capture-parallel-match | ERR NoMethodError undefined method 'max_length' for an instance of Interscript::Node::Item::CaptureGroup | OK axX | OK axX | OK aX |
| reverse-lossy | OK ac | ERR Unsupported reverse not implemented in ts runtime (no reverse module in src/) | ERR Unsupported reverse not implemented in py runtime | OK ac |
| reverse-nonlossy-control | OK bak | ERR Unsupported reverse not implemented in ts runtime (no reverse module in src/) | ERR Unsupported reverse not implemented in py runtime | OK bak |
| ml-funcall-rababa | OK Ka | ERR Error Stage "main" contains ML function calls (rababa/secryst). Use transliterateAsync() instead of transliterate(). | ERR AsyncFunctionError map calls ML function 'rababa'; the model layer is not mounted (install interscript-py[ml] and load a model, see interscript.models) | ERR Unsupported funcall "rababa" (rababa/secryst need external ML engines; not in slice 1) |
| ml-funcall-rababa-bare | ERR ArgumentError missing keyword: :config | ERR Error Stage "main" contains ML function calls (rababa/secryst). Use transliterateAsync() instead of transliterate(). | ERR AsyncFunctionError map calls ML function 'rababa'; the model layer is not mounted (install interscript-py[ml] and load a model, see interscript.models) | ERR Unsupported funcall "rababa" (rababa/secryst need external ML engines; not in slice 1) |
| alias-defined | OK VVV | OK VVV | OK VVV | OK VVV |
| fnlit-in-from | ERR Interscript::MapLogicError Wrong type Symbol, expected I::Node::Item | OK XdXoXwXnXcXaXsXeX | OK XdXoXwXnXcXaXsXeX | OK downcase |
| missing-map | ERR Interscript::MapNotFoundError Couldn't locate nonexistent-probe-map | ERR MapNotFoundError Map not found: nonexistent-probe-map | ERR MapNotFoundError map not found: 'nonexistent-probe-map' (load paths: /tmp/parity-probes/maps/_ir) | ERR MapNotFoundError map "nonexistent-probe-map" |
| use-in-sequence | ERR Interscript::Isc::ParseError tst-use-inseq.isc: Failed to match: expected one of [(?-mix:\s), '#', 'sub', '}'] at line 10 char 7. | ERR IscParseError ISC parse error at line 10:10: tst-use-inseq.isc: Failed to match isc_source at line 10 char 10 | ERR IscParseError ISC parse error at line 15:1: tst-use-inseq.isc: a ruleset containing a parallel/sequence block cannot be used inside a parallel/sequence block | OK 12 |
| use-stage-level | OK 12 | OK 12 | OK 12 | OK 12 |
| rs-cycle-bare | ERR Interscript::MapLogicError use cycle: ruleset a revisited through a -> b | ERR IscLoadError ISC load error: use cycle: T:tst-cycle-bare:1::a -> T:tst-cycle-bare:1::b -> T:tst-cycle-bare:1::a | ERR IscParseError ISC parse error at line 19:1: tst-cycle-bare.isc: use cycle: T:tst-cycle-bare:1/a -> T:tst-cycle-bare:1/b -> T:tst-cycle-bare:1/a | ERR MapLogicError use cycle: a -> b -> a |
| rs-duplicate-def | OK 1z | OK 1z | ERR IscParseError ISC parse error at line 17:1: tst-rsdup2.isc: ruleset declared more than once: a | OK 1z |
| rs-cycle-in-blocks | ERR Interscript::Isc::ParseError tst-rscycle2.isc: Failed to match: expected one of [(?-mix:\s), '#', 'sub', '}'] at line 5 char 7. | ERR IscParseError ISC parse error at line 5:10: tst-rscycle2.isc: Failed to match isc_source at line 5 char 10 | ERR IscParseError ISC parse error at line 21:1: tst-rscycle2.isc: use cycle: T:tst-rscycle2:1/a -> T:tst-rscycle2:1/b -> T:tst-rscycle2:1/a | ERR MapLogicError use cycle: a -> b -> a |
| use-dep-ruleset-missing | ERR Interscript::MapNotFoundError Couldn't locate nonexistent-map-xyz | ERR IscLoadError ISC load error: use: cannot resolve dependency "nonexistent-map-xyz" (needed for ruleset "base") | ERR IscParseError ISC parse error at line 8:1: tst-usedep-missing.isc: cannot resolve dependency: nonexistent-map-xyz | ERR MapNotFoundError map "nonexistent-map-xyz" |
| capture-in-sequence | OK aXb | OK aXb | OK aXb | OK aXb |
| capture-par2-shift | ERR NoMethodError undefined method 'max_length' for an instance of Interscript::Node::Item::CaptureGroup | OK kk3a | OK kk3a | OK 3ka |
| funcall-upcase-exec | ERR NoMethodError undefined method 'upcase' for module Interscript::Stdlib::Functions | OK ABC | OK ABC | OK ABC |
| funcall-battery-exec | OK h e a t i n g | OK h e a t i n g | OK h e a t i n g | OK h e a t i n g |
| longest-match | OK 1 | OK 1 | OK 1 | OK 1 |
| library-dep-alias | OK X | OK X | OK X | OK X |
