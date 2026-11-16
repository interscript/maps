#!/usr/bin/env python
"""Fuzz driver (py leg).

Usage: python3 driver-py.py <case.isc> <inputs-json>
Prints a single JSON line: {"runtime": "py", "parse": {...}, "exec": [...]}.

Parse leg: interscript.isc.isc_to_tree (origin/main 0.2.x architecture).
Exec leg: interscript.engine.Engine#transliterate over the main stage.
The case source is read as bytes and decoded with errors="replace" so
invalid UTF-8 is normalized to U+FFFD exactly like the other legs.
"""

import json
import os
import sys

sys.path.insert(
    0,
    os.environ.get("PY_SRC")
    or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "interscript-py", "src"),
)

from interscript.isc import isc_to_tree, IscParseError, UnsupportedConstruct  # noqa: E402
from interscript.engine import Engine, ExecutionError  # noqa: E402

CRASH_CLASSES = (
    AttributeError,
    KeyError,
    IndexError,
    RecursionError,
    TypeError,
    RuntimeError,
    NotImplementedError,
    ZeroDivisionError,
    ValueError,  # non-Isc ValueErrors leak internal state (e.g. int() errors)
)


def bucket(e: BaseException) -> str:
    if isinstance(e, IscParseError):
        return "PARSE"
    if isinstance(e, UnsupportedConstruct):
        return "UNSUPPORTED"
    if isinstance(e, ExecutionError):
        return "LOGIC"
    if isinstance(e, FileNotFoundError):
        return "LOAD"
    if isinstance(e, CRASH_CLASSES):
        return "CRASH"
    return "OTHER"


def shape(e: BaseException) -> dict:
    msg = str(e).splitlines()[0] if str(e) else ""
    return {
        "status": "ERR",
        "class": type(e).__name__,
        "bucket": bucket(e),
        "message": msg[:200],
    }


def main() -> int:
    case_file = sys.argv[1]
    inputs = json.loads(sys.argv[2] if len(sys.argv) > 2 else "[]")
    result = {"runtime": "py", "exec": []}

    with open(case_file, "rb") as f:
        raw = f.read()
    src = raw.decode("utf-8", errors="replace")

    try:
        tree = isc_to_tree(src, os.path.basename(case_file))
        result["parse"] = {"status": "OK"}
        engine = Engine(tree)
        for input_text in inputs:
            try:
                result["exec"].append(
                    {"input": input_text, "status": "OK", "output": engine.transliterate(input_text)}
                )
            except Exception as e:  # every failure shape is data here
                result["exec"].append({"input": input_text, **shape(e)})
    except Exception as e:  # noqa: BLE001
        result["parse"] = shape(e)

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
