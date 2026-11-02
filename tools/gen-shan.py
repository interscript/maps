"""Generate alalc-shn-Shan-Latn-<year>.isc — ALA-LC Shan (from the textlayer)."""
from pathlib import Path
import re
year = re.search(r"(\d{4}) version", open("tools/shan-textlayer.txt", encoding="utf-8").read())
YEAR = year.group(1) if year else "2011"

CONS = [("ᥛ","ka")][:0]
_SH = chr(0x1075)
CONS = [
    (chr(0x1075), "ka"), (chr(0x1076), "kha"), (chr(0x1077), "ga"),
    (chr(0x1003), "gha"), (chr(0x1004), "ṅa"), (chr(0x1078), "ca"),
    (chr(0x1006), "cha"), (chr(0x1079), "za"), (chr(0x1007), "jha"),
    (chr(0x107a), "ña"), (chr(0x100b), "ṭa"), (chr(0x100c), "ṭha"),
    (chr(0x100d), "ḍa"), (chr(0x100e), "ḍha"), (chr(0x100f), "ṇa"),
    (chr(0x1010), "ta"), (chr(0x1080), "tha"), (chr(0x107b), "da"),
    (chr(0x1012), "dha"), (chr(0x1014), "na"), (chr(0x1015), "pa"),
    (chr(0x1016), "pha"), (chr(0x107f), "ba"), (chr(0x1018), "bha"),
    (chr(0x1019), "ma"), (chr(0x101a), "ya"), (chr(0x101b), "ra"),
    (chr(0x101c), "la"), (chr(0x101d), "va"), (chr(0x101e), "sa"),
    (chr(0x101f), "ha"), (chr(0x1020), "ḷa"), (chr(0x1021), "ʼa"),
    (chr(0x107e), "xa"), (chr(0x108e), "fa"),
]
b1 = [f'    sub "{c}" "{v[:-1]}"' for c, v in CONS]
b1 += [f'    sub "{c}" "{v}"' if v in ("ʼa",) else "" for c, v in CONS]
b1 = [r for r in b1 if r]
# vowel signs (real Unicode from the text layer)
SIGNS = [(chr(0x1083),"ā"),(chr(0x102c),"ā"),(chr(0x102b),"ā"),(chr(0x102d),"i"),(chr(0x102e),"ī"),(chr(0x102f),"u"),(chr(0x1030),"ū")]
b2 = [f'    sub "{c}{s}" "{v[:-1]}{val}"' for s, val in SIGNS for c, v in CONS]
b3 = [f'    sub "ေ{c}" "{v[:-1]}e"' for c, v in CONS]
b3 += [f'    sub "{c}ဵ" "{v[:-1]}e"' for c, v in CONS]
b3 += [f'    sub "ႄ{c}" "{v[:-1]}è"' for c, v in CONS]
b3 += [f'    sub "{c}ႆ" "{v[:-1]}ai"' for c, v in CONS]
b3 += [f'    sub "{c} siguenさら" ""' for c, v in CONS][:0]
b3 += [f'    sub "{c}" ""' for c, v in CONS][:0]
b3 += [f'    sub "{c}{chr(0x1087)}{chr(0x1083)}" "{v[:-1]}āi"' for c, v in CONS]
b3 += [f'    sub "{c}{chr(0x1087)}{chr(0x102c)}" "{v[:-1]}āi"' for c, v in CONS]
b3 += [f'    sub "{c}ႂ်" "{v[:-1]}ái"' for c, v in CONS]
b3 += [f'    sub "{c}ႆွ" "{v[:-1]}oi"' for c, v in CONS]
b3 += [f'    sub "{c}ွ" "{v[:-1]}au"' for c, v in CONS]
b3 += [f'    sub "{c}ုိ" "{v[:-1]}ui"' for c, v in CONS]
b3 += [f'    sub "{c}ူိ" "{v[:-1]}ūi"' for c, v in CONS]
b3 += [f'    sub "ေ{c}ႃ" "{v[:-1]}o"' for c, v in CONS]
b3 += [f'    sub "ေ{c}ါ" "{v[:-1]}o"' for c, v in CONS]
b3 += [f'    sub "ေ{c}ႃ်" "{v[:-1]}ò"' for c, v in CONS]
b3 += [f'    sub "{c}ူဝ်" "{v[:-1]}ō"' for c, v in CONS]
b4 = [f'    sub "{c}" "{v}"' for c, v in CONS if v == "ʼa"]
b4 += [f'    sub "{c}" "{v[:-1]}a"' for c, v in CONS if v != "ʼa"]
b5 = [f'    sub "{m}" "{mv}"' for m, mv in [("ျ","y"),("ြ","r"),("ႂ","v")]]
b5 += [f'    sub "{a}" "{b}"' for a, b in zip("᥆᥇᥈᥉᥊᥋᥌᥍᥎᥏", "0123456789")]
b5 += ['    sub "်" ""', '    sub "ာ" ""']
tests = """tests {
   "\\u1075\\u102b" ->  "kā"
}
"""

def block(rows):
    return "  parallel {\n" + "\n".join([r for r in rows if r.strip()]) + "\n  }"

txt = f'''system "ALA-LC:shn-Shan:Latn:{YEAR}" {{

metadata {{
  authority_id alalc
  id {YEAR}
  language iso-639-2:shn
  source_script Shan
  destination_script Latn
  name "Shan Romanization Table ({YEAR})"
  url https://www.loc.gov/catdir/cpso/romanization/shan.pdf
  creation_date {YEAR}
  adoption_date
  description {{    ALA-LC Shan Romanization Table. Consonants carry the inherent
    vowel a (per Note 2); the full vowel-sign table (the tone-sign
    combinations ႆ act as vowel markers: ai āi oi); medials y r v in
    their documented order. Transcribed from the loc.gov document's
    text layer with the glyph column visually corresponded to the
    Shan/Myanmar-extended Unicode blocks (the PDF renders Shan glyphs
    through a shape-based substitute font).
  }}

  notes {{
    note "The Shan-specific letters (U+1075 ff.) carry the native
    values; the Indic-value letters reuse the Myanmar codepoints. Tone
    signs 2-6 (U+1087 ff.) beyond the vowel-marking tone-2 are not
    romanized."
  }}
}}

{tests}
stage main {{
{block(b3)}

{block(b2)}

{block(b5)}

{block(b1)}

{block(b4)}
}}
}}
'''
Path(f"maps-staging/alalc-shn-Shan-Latn-{YEAR}.isc").write_text(
    txt, encoding="utf-8")
print("written", YEAR, len(b1), len(b2), len(b3), len(b4), len(b5))
