"""Extract ICS 630-01 Annex D (Chinese Personal Names) data tables.

Sources (interscript-private-references/ics-630-01/):
  - "ANNEX D - Chinese_Personal_Names_FLTS.pdf"                 (Annex D prose, D-1..D-3)
  - "ANNEX D - Appendix A - Chinese_Personal_Names_FLTS (U).pdf" (IC Transliteration Table, D-4)
  - "ANNEX D - Appendix B - Chinese_Personal_Names_FLTS (U).pdf" (Conversion Table, D-5..D-18)
  - "ANNEX D - Appendix C - Chinese_Personal_Names_FLTS (U).pdf" (Common Surnames, D-19..D-22)

Extraction methods, per section:
  - Annex D prose:    pypdf text layer (all 3 pages).
  - Appendix A:       pdfplumber table grid (single table, 40 cols x 50 rows incl.
                      separator rows), text layer; header row + 25 initial rows.
                      Spot-checked visually against a 600 dpi render of the same
                      page (two "i" header columns, "Wong" cell, w- row).
  - Appendix B:       pypdf text layer, one row per line
                      "ic wadegiles yale zhuyin", all 14 pages.
  - Appendix C:       pypdf text layer, regex per entry line
                      "<hanzi> <STC 4 digits> <IC>[, alternates]", all 4 pages;
                      spot-checked visually against a 300 dpi render.

Output: tools/ics-630-01-annexd.json
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

SRC_DIR = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "/Users/mulgogi/src/interscript/interscript-private-references/ics-630-01"
)
OUT = Path(__file__).with_name("ics-630-01-annexd.json")

ANNEX_D = SRC_DIR / "ANNEX D - Chinese_Personal_Names_FLTS.pdf"
APP_A = SRC_DIR / "ANNEX D - Appendix A - Chinese_Personal_Names_FLTS (U).pdf"
APP_B = SRC_DIR / "ANNEX D - Appendix B - Chinese_Personal_Names_FLTS (U).pdf"
APP_C = SRC_DIR / "ANNEX D - Appendix C - Chinese_Personal_Names_FLTS (U).pdf"

# Appendix A column headers, as printed (39 final columns; note cols 4 and 5
# are BOTH printed "i", and cols 34/35 "uen"/"ueng" carry no cells in any row).
# Cells of the z/c/s/y rows sit under the first i column; zh/ch/sh/r under the
# second. For the l- and n- rows the printed "yu"/"ue" columns carry the
# umlauted syllables lü/lüe/nü/nüe (the IC standard folds ü to u).


def extract_appendix_a():
    pdf = pdfplumber.open(APP_A)
    page = pdf.pages[0]
    grid = page.find_tables()[0].extract()
    header = grid[0][1:]  # 39 final labels, first printed label is None-free ""
    rows = {}
    for row in grid:
        label = row[0]
        if not label or label.strip() == "":
            continue
        rows[label.strip()] = {
            str(i + 1): (cell if cell is not None else "")
            for i, cell in enumerate(row[1:])
            if cell not in ("", None)
        }
    return header, rows


# For each (initial row, printed final column) pair, the pinyin orthographic
# input syllable. Initial prefixes come from the row labels ("-","b-",...).
# Special cases: the second "i" column of the zh/ch/sh/r rows is still the
# syllable spelled with "i" (zhi/chi/shi/ri); the l-/n- ü-columns are spelled
# with ü (lü, lüe, nü, nüe); the y-/w- rows carry the full syllable as printed
# in the cell (you, weng, wong, ...).


def cell_input_syllable(initial, col_no, final, ic):
    if initial == "-":
        return ic.lower()
    if initial in ("y-", "w-"):
        return ic.lower()
    stem = initial[:-1]  # "ch-" -> "ch"
    # umlaut columns for l and n: pinyin writes lü/lüe/nü/nüe
    if stem in ("l", "n") and col_no in ("36", "37"):
        uml = {"36": "ü", "37": "üe"}[col_no]
        return stem + uml
    # column 36 is printed "yu": after j/q/x the ü of ju/qu/xu is written u
    if stem in ("j", "q", "x") and col_no == "36":
        return stem + "u"
    return stem + final


def build_appendix_a(header, rows):
    cells = []
    for initial, colmap in rows.items():
        for col_no, ic in sorted(colmap.items(), key=lambda kv: int(kv[0])):
            if initial == "-":
                cells.append(
                    {
                        "initial": initial,
                        "final": header[int(col_no) - 1],
                        "input": ic.lower(),
                        "ic": ic,
                    }
                )
                continue
            final = header[int(col_no) - 1]
            cells.append(
                {
                    "initial": initial,
                    "final": final,
                    "input": cell_input_syllable(initial, col_no, final, ic),
                    "ic": ic,
                }
            )
    return cells


def extract_appendix_b():
    reader = PdfReader(str(APP_B))
    rows = []
    pat = re.compile(r"^([a-z]+) ([a-zA-Zü‘’']+) ([a-zA-Zü']+) ([ㄅ-ㄩ]+)$")
    for page in reader.pages:
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            m = pat.match(line)
            if m:
                rows.append(
                    {
                        "ic": m.group(1),
                        "wade_giles": m.group(2),
                        "yale": m.group(3),
                        "zhuyin": m.group(4),
                    }
                )
    return rows


def extract_appendix_c():
    reader = PdfReader(str(APP_C))
    entries = []
    # char, STC code, renditions (IC first, alternates after commas)
    pat = re.compile(r"^(\S) (\d{4}) (.+?)\s*$")
    for pageno, page in enumerate(reader.pages, start=1):
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            m = pat.match(line)
            if not m:
                continue
            char, stc, rend = m.group(1), m.group(2), m.group(3)
            parts = [p.strip() for p in rend.split(",")]
            entries.append(
                {
                    "char": char,
                    "stc": stc,
                    "ic": parts[0],
                    "alternates": parts[1:],
                    "page": pageno,
                }
            )
    return entries


def main():
    header, rows = extract_appendix_a()
    cells = build_appendix_a(header, rows)
    appb = extract_appendix_b()
    appc = extract_appendix_c()

    data = {
        "source": "ICS 630-01, Foreign Language Transliteration Standards, "
        "Annex D: Standards for the Transliteration of Chinese Personal "
        "Names in Written Reports and Products (effective 10 August 2015)",
        "cover_memo": {
            "extraction_method": "single scanned page, no text layer; "
            "transcribed from a 200 dpi render (visual read)",
            "title": "Foreign Language Transliteration Standards",
            "standard": "Intelligence Community Standard 630-01",
            "authority": "National Security Act of 1947, as amended; the "
            "Reform and Terrorism Prevention Act of 2004; Executive Order "
            "12333, as amended; and IC Directive Number 607, Intelligence "
            "Community Foreign Language Capability",
            "policy": "Standardized transliteration within the IC on all "
            "finished analytical reports and products. Foreign Language "
            "Transliteration Standards (FLTS) for individual languages "
            "are developed and reviewed by each IC element's Senior "
            "Language Authority (SLA), promulgated as annexes titled "
            "'Standards for the Transliteration of Personal Names in "
            "Written Reports and Products'.",
            "approval": "ADNI, through the Foreign Language Program "
            "Office (FLPO), and approved IC FLTS are issued as ICS "
            "630-01; Heads of IC elements review and approve ICS 630-01 "
            "within their respective IC element",
            "effective": "10 August 2015 (date of signature, Deana A. "
            "Krichter, ADNI for Human Capital)",
        },
        "extraction": {
            "annex_d_prose": "pypdf text layer, 3 pages, complete",
            "appendix_a": "pdfplumber table grid (40x50 incl. separators) from "
            "the text layer; spot-checked visually at 600 dpi (duplicate i/i "
            "header columns, w- row 'Wong', y- row alignment)",
            "appendix_b": "pypdf text layer, all 14 pages, one row per line",
            "appendix_c": "pypdf text layer regex per entry; spot-checked "
            "visually at 300 dpi",
        },
        "appendix_a": {
            "title": "Appendix A: IC Transliteration Table",
            "note_as_printed": "Notes: this table includes initial-final "
            "combinations to form acceptable Chinese syllables.",
            "columns": header,
            "rows": rows,
            "cells": cells,
            "cell_count": len(cells),
        },
        "appendix_b": {
            "title": "Appendix B: Conversion Table of Common Chinese "
            "Romanization Systems",
            "columns_as_printed": [
                "IC Transliteraion (Based on Pinyin)",
                "Wade-Giles",
                "Yale",
                "Mandarin Phonetic (Zhuyin) Symbols",
            ],
            "rows": appb,
            "row_count": len(appb),
        },
        "appendix_c": {
            "title": "Appendix C: List of Common Chinese Surnames",
            "note_as_printed": "Chinese STC Transliteration per IC "
            "(IC first, followed by other common renditions); partially "
            "adapted from "
            "http://en.wikipedia.org/wiki/List_of_common_Chinese_surnames",
            "entries": appc,
            "entry_count": len(appc),
        },
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(f"appendix A cells: {len(cells)}")
    print(f"appendix B rows:  {len(appb)}")
    print(f"appendix C entries: {len(appc)}")


if __name__ == "__main__":
    main()
