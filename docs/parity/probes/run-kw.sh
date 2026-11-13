#!/usr/bin/env bash
# Keyword-table probe: parse each kw-<ident>.isc with all four runtimes.
# A map parses iff <ident> is NOT a keyword (in item/alias-name position).
KW_DIR="$(cd "$(dirname "$0")" && pwd)/maps"
RUBY="ruby"
PY=/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/.venv/bin/python
ISCRS=/Users/mulgogi/src/interscript/interscript-rs/target/release/iscrs

for f in "$KW_DIR"/kw-*.isc; do
  base=$(basename "$f" .isc); ident=${base#kw-}
  row="$ident"
  out=$($RUBY -I/Users/mulgogi/src/interscript/interscript-ruby-wf1/lib -e '
    require "interscript"
    Interscript.load_path.unshift(ARGV[0])
    begin
      Interscript.parse(ARGV[1]); puts "ok"
    rescue Exception
      puts "KW"
    end
  ' "$KW_DIR" "$base" 2>/dev/null)
  row="$row\t$out"
  out=$(node -e '
  const { readFileSync } = require("fs");
  import("/Users/mulgogi/src/interscript/interscript-ts/dist/isc/index.js").then(({ parseIsc }) => {
    try { parseIsc(readFileSync(process.argv[1], "utf8"), "x"); console.log("ok"); }
    catch { console.log("KW"); }
  });' "$f" 2>/dev/null)
  row="$row\t$out"
  out=$($PY -c '
import sys
sys.path.insert(0, "/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/src")
from interscript import parse_isc
try:
    parse_isc(open(sys.argv[1], encoding="utf-8").read(), "x"); print("ok")
except Exception: print("KW")
' "$f" 2>/dev/null)
  row="$row\t$out"
  if "$ISCRS" parse "$f" --maps "$KW_DIR" >/dev/null 2>&1; then out=ok; else out=KW; fi
  row="$row\t$out"
  printf '%b\n' "$row"
done
