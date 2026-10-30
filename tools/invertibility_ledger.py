"""A2 - the invertibility ledger generator (static analysis)."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

SUB_RE = re.compile(r'sub\s+"((?:[^"\\]|\\.)*)"\s+"((?:[^"\\]|\\.)*)"\s*$')
CTX_RE = re.compile(r'from\s+"')
SYSTEM_RE = re.compile(r'system\s+"([^"]+)"')


def unescape(s):
    return s.encode("utf-8").decode("unicode_escape") if "\\u" in s else s


def analyze(path):
    text = path.read_text(encoding="utf-8")
    m = SYSTEM_RE.search(text)
    system = m.group(1) if m else path.stem
    pairs = {}
    tgt_srcs = defaultdict(list)
    src_ct = defaultdict(int)
    n_ctx = 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if "from \"" in line and line.strip().startswith("from"):
            n_ctx += 1
        mm = SUB_RE.match(s)
        if not mm:
            continue
        src, tgt = unescape(mm.group(1)), unescape(mm.group(2))
        src_ct[src] += 1
        pairs[src] = tgt
        tgt_srcs[tgt].append(src)
    many_to_one = {t: s for t, s in tgt_srcs.items() if len(s) > 1}
    one_to_many = {s: c for s, c in src_ct.items() if c > 1}
    verdict = ("LOSSLESS_ONE_TO_ONE" if not many_to_one and not one_to_many
               else "LOSSY_MANY_TO_ONE" if many_to_one else "CONTEXT_ONLY")
    return {"system": system, "file": path.name, "pairs": len(pairs),
            "context_rules": n_ctx, "many_to_one": len(many_to_one),
            "many_to_one_examples": {t: s[:4] for t, s in list(sorted(many_to_one.items()))[:6]},
            "one_to_many": len(one_to_many),
            "one_to_many_examples": {s: c for s, c in list(sorted(one_to_many.items()))[:6]},
            "verdict": verdict}


def main():
    root = Path(__file__).resolve().parent.parent / "maps"
    out = {}
    for p in sorted(root.glob("*.isc")):
        try:
            out[p.stem] = analyze(p)
        except Exception as e:
            out[p.stem] = {"file": p.name, "error": repr(e)[:120]}
    dest = Path(__file__).resolve().parent.parent / "docs" / "coverage" / "invertibility-ledger.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    tallies = defaultdict(int)
    for v in out.values():
        tallies[v.get("verdict", "ERROR")] += 1
    print(json.dumps(tallies, indent=2))
    print("ledger:", dest)


if __name__ == "__main__":
    main()
