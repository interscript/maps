#!/usr/bin/env python
"""Corpus parse timing (py): parse_isc on all 428 corpus maps, 3 runs."""
import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/src")
from interscript import parse_isc  # noqa: E402

d = Path("/Users/mulgogi/src/interscript/maps/maps")
libd = Path("/Users/mulgogi/src/interscript/maps/libs")
files = sorted(d.glob("*.isc"))
assert files, "no files"

_cache: dict[str, object] = {}

def resolve(target: str):
    """Dependency resolver over the corpus + libs dirs (mirrors the
    load-path resolution ruby/rs do natively)."""
    if target in _cache:
        return _cache[target]
    for base in (d, libd):
        p = base / f"{target}.isc"
        if p.exists():
            doc = parse_isc(p.read_text(encoding="utf-8"), p.name, resolve_dependency=resolve)
            _cache[target] = doc
            return doc
    return None

for run in range(3):
    _cache.clear()
    t0 = time.perf_counter()
    ok = 0
    for f in files:
        try:
            parse_isc(f.read_text(encoding="utf-8"), f.name, resolve_dependency=resolve)
            ok += 1
        except Exception as e:
            print(f"FAIL {f.name}: {str(e).splitlines()[0]}", file=sys.stderr)
    t1 = time.perf_counter()
    print(f"py parse {ok}/{len(files)} maps in {(t1 - t0) * 1000:.1f} ms")
