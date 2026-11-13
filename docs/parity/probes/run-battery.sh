#!/usr/bin/env bash
# Execution battery runner: run every (map, input, flags) case across all four runtimes.
# Output TSV: case<TAB>runtime<TAB>OK/ERR<TAB>detail
set -u
P="$(cd "$(dirname "$0")" && pwd)"
RUBY="ruby"
PY=/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/.venv/bin/python

run_case() {
  local name="$1" map="$2" input="$3"; shift 3
  local flags=("$@")
  local r t p s
  r=$($RUBY "$P/driver.rb" "$P/maps" "$map" "$input" "${flags[@]}" 2>&1 | head -1)
  t=$(node "$P/driver.mjs" "$P/maps" "$map" "$input" "${flags[@]}" 2>&1 | head -1)
  p=$($PY "$P/driver.py" "$P/maps" "$map" "$input" "${flags[@]}" 2>&1 | head -1)
  s=$(bash "$P/driver-rs.sh" "$P/maps" "$map" "$input" "${flags[@]}" 2>&1 | head -1)
  printf '%s\truby\t%s\n' "$name" "$r"
  printf '%s\tts\t%s\n' "$name" "$t"
  printf '%s\tpy\t%s\n' "$name" "$p"
  printf '%s\trs\t%s\n' "$name" "$s"
}

# P0 sanity
run_case "sanity-basic" tst-basic "abk"
run_case "sanity-basic-empty-input" tst-basic ""
run_case "sanity-basic-stage-second" tst-basic "abk" --stage second
# P1 missing main stage
run_case "missing-main-stage" tst-nomain "aaa"
# P2 missing dependency (run into nonexistent map)
run_case "missing-dependency" tst-nomapdep "aaa"
# P2-control dependency run works
run_case "dependency-run-ok" tst-dep-run "aka"
# P3 run into dependency stage that does not exist
run_case "dependency-missing-stage" tst-dep-badstage "aka"
# P4 duplicate froms
run_case "dup-parallel" tst-dup-parallel "ab"
run_case "dup-sequence" tst-dup-seq "a"
# P5 unknown alias in from
run_case "unknown-alias" tst-unknownalias "a"
# P6 ruleset cycle
run_case "ruleset-cycle" tst-rscycle "xyz"
# P7 use+override
run_case "override-basics" tst-rsbase "ktc"
run_case "override-absent-row" tst-rsbase "zzz" --stage absrow
# P8/P9 language selection
run_case "lang-selected-declared" tst-lang-undecl "k" --lang kur
run_case "lang-selected-undeclared" tst-lang-undecl "k" --lang chv
run_case "lang-no-selection" tst-lang-undecl "k"
run_case "lang-selected-nodeclaration" tst-lang-nodecl "k" --lang kur
# P10 capture in parallel
run_case "capture-parallel" tst-capture-parallel "axb"
run_case "capture-parallel-match" tst-capture-parallel "ax"
# P11 reverse on lossy map
run_case "reverse-lossy" tst-lossy "xk" --reverse
run_case "reverse-nonlossy-control" tst-basic "cbQ" --reverse
# P12 ML funcall
run_case "ml-funcall-rababa" tst-ml "ka"
run_case "ml-funcall-rababa-bare" tst-ml-bare "ka"
# alias-defined control + fnlit-from
run_case "alias-defined" tst-alias-def "abc"
run_case "fnlit-in-from" tst-fnlit-from "downcase"
# missing map entirely
run_case "missing-map" nonexistent-probe-map "x"
# W1 grammar positions and cycles
run_case "use-in-sequence" tst-use-inseq "ab"
run_case "use-stage-level" tst-use-stagelevel "ab"
run_case "rs-cycle-bare" tst-cycle-bare "xy"
run_case "rs-duplicate-def" tst-rsdup2 "xz"
run_case "rs-cycle-in-blocks" tst-rscycle2 "xyz"
run_case "use-dep-ruleset-missing" tst-usedep-missing "x"
# capture/ref scoping
run_case "capture-in-sequence" tst-capture-seq "axb"
run_case "capture-par2-shift" tst-capture-par2 "k3a"
# funcall edges
run_case "funcall-upcase-exec" tst-upcase-exec "§abc"
run_case "funcall-battery-exec" tst-funcall-exec "§heating"
run_case "longest-match" tst-longest "ab"
# library dependency (alias merge into scope)
run_case "library-dep-alias" tst-libdep "ᄀ"
