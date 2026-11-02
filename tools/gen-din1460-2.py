"""Generate the 62 DIN 1460-2:2011-10 maps (Cyrillic non-Slavic
languages) from the extracted table JSON. One map per language row;
dialect rows sharing an ISO code get a -s<langnum> suffix (the corpus's
table-suffix convention, cf. din-grc-...-31634-2011-t1).

Extraction provenance: tools/din1460-2-table.json — the PDF's real
text layer, columns anchored on the per-page position-number row
(y=136), values matched by x to the Cyrillic header letters. Position
13's header glyph is PUA (U+E519) in the text layer; per the visual
crop it is h with comma below (U+0068 + U+0322) — recorded here and
in the map notes.
"""
import json
from pathlib import Path

T = json.load(Path(__file__).with_name("din1460-2-table.json").open())
POS = {int(k): v for k, v in T["positions"].items()}
PUA = {"\ue553": "j\u0301", "\ue552": "j\u0304"}  # visual IDs at 12x
def fix(s):
    for k, v in PUA.items():
        s = s.replace(k, v)
    return s
POS = {k: fix(v) for k, v in POS.items()}
POS[13] = "h\u0322"  # PUA in the text layer; visual ID at 10x: h with comma below (cf. pos 12 = h-hooktop + comma)

CODE = {"Abasinisch": ("abq", None), "Abchasisch": ("ab", None),
    "Adygeisch": ("ady", None), "Altaisch": ("atv", None),
    "Aserbaidschanisch": ("az", None), "Awarisch": ("av", None),
    "Balkarisch": ("krc", "Balkar"), "Baschkirisch": ("ba", None),
    "Berg-Mari": ("mrj", None), "Burjatisch": ("bxr", None),
    "Chakassisch": ("kjh", None), "Darginisch": ("dar", None),
    "Dunganisch": ("dng", None), "Ersa-Mordwinisch": ("myv", None),
    "Eskimo": ("ess", "Asiatic (Siberian) Eskimo, Central Siberian Yupik"),
    "Ewenisch": ("eve", None), "Ewenkisch": ("evn", None),
    "Gagausisch": ("gag", None), "Inguschisch": ("inh", None),
    "Jakutisch": ("sah", None), "Kabardinisch": ("kbd", None),
    "Kalmückisch": ("xal", None), "Karakalpakisch": ("kaa", None),
    "Karatschaisch": ("krc", "Karachay"), "Kasachisch": ("kk", None),
    "Kasym-Chantisch": ("kca", "Kasym Khanty"),
    "Kirgisisch": ("ky", None), "Komi-Permjakisch": ("koi", None),
    "Komi-Syrjänisch": ("kv", None), "Korjakisch": ("kpy", None),
    "Krimtatarisch": ("crh", None), "Kumükisch": ("kum", None),
    "Kurdisch": ("ku", "Kurdish (Cyrillic)"),
    "Lakkisch": ("lbe", None), "Lesgisch": ("lez", None),
    "Mansisch": ("mns", None),
    "Mittel-Ob-Chantisch": ("kca", "Middle-Ob Khanty"),
    "Mokscha-Mordwin.": ("mdf", None), "Moldauisch": ("ro", "Moldavian (Cyrillic)"),
    "Mongolisch": ("khk", None), "Nanaisch": ("gld", None),
    "Nenzisch": ("yrk", None), "Wiesen-Mari": ("mhr", None),
    "Niwchisch": ("niv", None), "Nogaisch": ("nog", None),
    "Berg-Mari": ("mrj", None), "Ossetisch": ("os", None),
    "Schorisch": ("cjs", None), "Schuryschkar": ("kca", "Shuryshkar Khanty"),
    "Selkupisch": ("sel", None), "Surgut-Chantisch": ("kca", "Surgut Khanty"),
    "Tabassaranisch": ("tab", None), "Tadschikisch": ("tg", None),
    "Tatarisch": ("tt", None), "Tschetschenisch": ("ce", None),
    "Tschuktschisch": ("ckt", None), "Tschuwaschisch": ("cv", None),
    "Turkmenisch": ("tk", None), "Tuwinisch": ("tyv", None),
    "Udmurtisch": ("udm", None), "Uigurisch": ("ug", None),
    "Usbekisch": ("uz", None), "Wach-Chantisch": ("kca", "Wach Khanty")}

GRUPPE = {"K": "Caucasus", "T": "Turkic", "M": "Mongolic", "I": "Indo-European",
          "F": "Uralic", "P": "Paleo-Asiatic", "E": "Eskimo-Aleut"}

outdir = Path(__file__).resolve().parent.parent / "maps-staging"
made = []
for num in sorted(T["languages"], key=int):
    row = T["languages"][num]
    name = row["name"].rstrip("-")
    code, dialect = CODE[name]
    lid = f"din-{code}-Cyrl-Latn-1460-2-2011" + (f"-s{num}" if dialect else "")
    # merge duplicate position values (same letter row twice) — keep first
    rows = []
    seen = set()
    for p in sorted(row["vals"], key=int):
        cyr, lat = POS[int(p)], fix(row["vals"][p]).strip("()")
        key = (cyr, lat)
        if key in seen:
            continue
        seen.add(key)
        rows.append((cyr, lat))
    if not rows:
        continue
    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')
    subs = "\n".join(f'    sub "{esc(c)}" "{esc(l)}"' for c, l in rows)
    tests = "\n".join(f'   "{esc(c)}" ->  "{esc(l)}"' for c, l in rows[:4])
    dn = f" ({dialect})" if dialect else ""
    note13 = (" Dialect qualifier: " + dialect + "; the id carries the"
              " table's language number as the corpus table-suffix"
              " convention requires for shared ISO codes.") if dialect else ""
    txt = f'''system "DIN:{code}-Cyrl:Latn:1460-2-2011{'-s' + num if dialect else ''}" {{

metadata {{
  authority_id din
  id 1460-2-2011-{num}
  language iso-639-3:{code}
  source_script Cyrl
  destination_script Latn
  name "DIN 1460-2:2011-10, Tabelle 1 row {num}: {row['name']}{dn} ({GRUPPE.get(row['group'].strip('()'), row['group'])})"
  url https://www.beuth.de/de/norm/din-1460-2/134564104
  creation_date 2011
  adoption_date
  description {{
    DIN 1460-2:2011-10, Romanization of Cyrillic alphabets of
    non-Slavic languages, Tabelle 1, language row {num}
    ({row['name']}{dn}). The table assigns each Cyrillic letter of the
    language's alphabet a Latin letter or letter group; the column
    order follows DIN 1460:1982 (Slavic). Extracted mechanically from
    the standard's text layer; the mapping rows below are the table's
    own cells.
  }}

  notes {{
    note "Extraction provenance: the PDF's text layer carries the full
    grid; columns were anchored on the per-page position-number row and
    each cell matched by x-coordinate to its Cyrillic header letter.
    Position 13's header glyph is PUA (U+E519) in the text layer and
    was visually identified at 10x as h with comma below (U+0068 + U+0322), the plain-h counterpart of position 12's hooktop-h symbol.{note13}"
  }}
}}

tests {{
{tests}
}}

stage main {{
  parallel {{
{subs}
  }}
}}
}}
'''
    (outdir / f"{lid}.isc").write_text(txt, encoding="utf-8")
    made.append(lid)
print("generated", len(made), "maps")
print(made[:6])
