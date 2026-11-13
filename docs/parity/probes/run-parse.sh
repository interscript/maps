#!/usr/bin/env bash
# Parse-probe runner: parse every pp-*.isc with all four runtimes.
# Output: one TSV line per (map, runtime): map<TAB>runtime<TAB>OK|ERR<TAB>detail
PP_DIR="$(cd "$(dirname "$0")" && pwd)/maps"
RUBY="ruby"
PY=/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/.venv/bin/python
ISCRS=/Users/mulgogi/src/interscript/interscript-rs/target/release/iscrs

for f in "$PP_DIR"/pp-*.isc; do
  base=$(basename "$f" .isc)
  # ruby
  out=$($RUBY -I/Users/mulgogi/src/interscript/interscript-ruby-wf1/lib -e '
    require "interscript"
    Interscript.load_path.unshift(ARGV[0])
    begin
      Interscript.parse(ARGV[1])
      puts "OK"
    rescue Exception => e
      puts "ERR\t#{e.class.name}\t#{(e.message||"").lines.first.to_s.chomp}"
    end
  ' "$PP_DIR" "$base" 2>&1)
  printf '%s\truby\t%s\n' "$base" "$out"
  # ts
  out=$(node -e '
  const { readFileSync } = require("fs");
  import("/Users/mulgogi/src/interscript/interscript-ts/dist/isc/index.js").then(({ parseIsc }) => {
    try {
      const src = readFileSync(process.argv[1], "utf8");
      parseIsc(src, process.argv[2]);
      console.log("OK");
    } catch (e) {
      console.log(`ERR\t${e.name}\t${String(e.message).split("\n")[0]}`);
    }
  });
  ' "$f" "$base" 2>&1)
  printf '%s\tts\t%s\n' "$base" "$out"
  # py
  out=$($PY -c '
import sys
sys.path.insert(0, "/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/src")
from interscript import parse_isc
src = open(sys.argv[1], encoding="utf-8").read()
try:
    parse_isc(src, sys.argv[2])
    print("OK")
except Exception as e:
    msg = str(e).splitlines()[0] if str(e) else ""
    print(f"ERR\t{type(e).__name__}\t{msg}")
' "$f" "$base" 2>&1)
  printf '%s\tpy\t%s\n' "$base" "$out"
  # rs
  out=$("$ISCRS" parse "$f" --maps "$PP_DIR" 2>&1) && printf '%s\trs\tOK\n' "$base" || printf '%s\trs\tERR\t%s\n' "$base" "$(printf '%s' "$out" | head -1)"
done
