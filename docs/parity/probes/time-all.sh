#!/usr/bin/env bash
# Definitive clean corpus-parse timing series: one runtime at a time,
# 3 runs each, serial, nothing else running.
set -u
echo "=== rs (iscrs parse, wall; incl. ~20ms process startup) ==="
for i in 1 2 3; do
  /usr/bin/time -p /Users/mulgogi/src/interscript/interscript-rs/target/release/iscrs parse /Users/mulgogi/src/interscript/maps/maps --maps /Users/mulgogi/src/interscript/maps/maps 2>&1 | grep -E "files parsed|real"
done
echo "=== ruby (in-process, parse_isc sweep) ==="
/tmp/parity-probes/time-ruby.sh
echo "=== ts (in-process, parseIsc sweep) ==="
node /tmp/parity-probes/time-ts.mjs
echo "=== py (in-process, parse_isc+resolver sweep) ==="
/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/.venv/bin/python /tmp/parity-probes/time-py.py
