#!/usr/bin/env python
"""Parity battery driver (py leg).

Usage: driver.py <maps_dir> <map_id> <input> [--stage S] [--lang L] [--reverse]
Prints:  OK<TAB>result   or   ERR<TAB>Class<TAB>message
"""
import sys
from pathlib import Path

sys.path.insert(0, "/Users/mulgogi/src/interscript/interscript-ruby-wf1-py/interscript-py/src")

from interscript import parse_isc, isc_to_compiled_map  # noqa: E402
from interscript.executor import execute_stage  # noqa: E402
from interscript.loader import MapLoader  # noqa: E402


def main() -> int:
    argv = sys.argv[1:]
    maps_dir, map_id, text = argv[0], argv[1], argv[2]
    rest = argv[3:]
    stage = "main"
    language = None
    reverse = False
    while rest:
        a = rest.pop(0)
        if a == "--stage":
            stage = rest.pop(0)
        elif a == "--lang":
            language = rest.pop(0)
        elif a == "--reverse":
            reverse = True
        else:
            print(f"unknown flag {a}", file=sys.stderr)
            return 2

    try:
        path = Path(maps_dir) / f"{map_id}.isc"
        if not path.exists():
            # production py consumers resolve maps through MapLoader
            # (IR dirs) — surface its error for missing maps.
            raise MapLoader([Path(maps_dir) / "_ir"], verify=False).load(map_id)
        source = path.read_text(encoding="utf-8")
        doc = parse_isc(source, f"{map_id}.isc", resolve_dependency=lambda code: _dep(maps_dir, code))
        loader = MapLoader([Path(maps_dir) / "_ir"], verify=False)
        cm = isc_to_compiled_map(doc)
        if reverse:
            print("ERR\tUnsupported\treverse not implemented in py runtime")
            return 0
        out = execute_stage(cm, stage, text, loader, language)
        print(f"OK\t{out}")
    except Exception as e:  # battery wants every failure shape
        msg = str(e).splitlines()[0] if str(e) else ""
        print(f"ERR\t{type(e).__name__}\t{msg}")
    return 0


def _dep(maps_dir: str, code: str):
    path = Path(maps_dir) / f"{code}.isc"
    if not path.exists():
        return None
    return parse_isc(path.read_text(encoding="utf-8"), f"{code}.isc")


if __name__ == "__main__":
    raise SystemExit(main())
