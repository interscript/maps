"""Generate alalc-mya-Mymr-Latn-2011.isc — ALA-LC Burmese 2011.
Inherent vowel a (Devanagari-style); asa closes the syllable with ʻ;
medials y r v h between the consonant and its vowel; tones ʹ ʺ."""
from pathlib import Path

CONS = [("က","k"),("ခ","kh"),("ဂ","g"),("ဃ","gh"),("င","ṅ"),("စ","c"),
    ("ဆ","ch"),("ဇ","j"),("झ","jh"),("ဉ","ñ"),("ဏ","ṇ"),("တ","t"),
    ("ထ","th"),("ဒ","d"),("ဓ","dh"),("န","n"),("ပ","p"),("ဖ","ph"),
    ("ဗ","b"),("ဘ","bh"),("မ","m"),("ယ","y"),("ရ","r"),("လ","l"),
    ("ဝ","w"),("သ","s"),("ဟ","h"),("ဠ","ḷ")]
CM = dict(CONS)
VSIGN = [("ါ","ā"),("ာ","ā"),("ိ","i"),("ီ","ī"),("ု","u"),("ူ","ū")]
MEDS = ["", "y", "r", "v", "h", "yv", "rv", "yh", "vh", "yvh", "rvh"]
MEDCH = {"y":"ျ","r":"ြ","v":"ွ","h":"ှ"}

b_med = []
for m in MEDS:
    mchars = "".join(MEDCH.get(x, x) for x in m)
    for chars, val in VSIGN:
        for c, v in CONS:
            b_med.append((f"{c}{mchars}{chars}", f"{v}{m}{val}"))
# combos first: one block, longest match by pattern length
b_med.sort(key=lambda r: -len(r[0]))
b_med = [f'    sub "{pat}" "{val}"' for pat, val in b_med]
b_e = [f'    sub "ေ{c}" "{v}e"' for c, v in CONS]
b_ai = [f'    sub "ဲ{c}" "{v}ai"' for c, v in CONS]
b_o = ([f'    sub "ေ{c}ာ" "{v}o"' for c, v in CONS] +
       [f'    sub "ေ{c}ါ" "{v}o"' for c, v in CONS])
b_oas = [f'    sub "ေ{c}ာ်" "{v}oʻ"' for c, v in CONS]
b_ui = [f'    sub "{c}ို" "{v}ui"' for c, v in CONS]
b_med = sorted([f'    sub "{c}ိ" "{v}i"' for c, v in CONS] + b_ui
               + b_med, key=lambda r: -len(r.split('"')[1]))
b_asa = [f'    sub "{c}္" "{v}ʻ"' for c, v in CONS]
b_asa += [f'    sub "{c}်" "{v}ʻ"' for c, v in CONS]
b_bare = [f'    sub "{c}" "{v}a"' for c, v in CONS]
b_rest = ['    sub "ံ" "ṃ"', '    sub "့" "ʹ"', '    sub "း" "ʺ"']
b_ind = [f'    sub "{a}" "{b}"' for a, b in
         [("ဣ","i"),("ဤ","ī"),("ဥ","u"),("ဦ","ū"),("ဧ","e"),
          ("ဩ","o"),("ဪ","oʻ")]]
b_num = [f'    sub "{a}" "{b}"' for a, b in zip("၀၁၂၃၄၅၆၇၈၉", "0123456789")]
b_punct = ['    sub "၊" ","', '    sub "။" "."']
b_abbr = ['    sub "၏" "e*"', '    sub "၍" "r*"', '    sub "၌" "n*"',
          '    sub "၎" "l*"']

tests = """tests {
   "\\u1019\\u103d\\u102b" ->  "mva"
   "\\u1000\\u103c\\u101d\\u102c" ->  "krva"
   "\\u101c\\u103d\\u102e\\u1017\\u103e\\u102c" ->  "lvhā"
   "\\u1015\\u102d\\u102f\\u1037" ->  "puiʹ"
   "\\u1015\\u102d\\u102f\\u1038" ->  "puiʺ"
   "\\u1025\\u1015\\u102f\\u1005\\u103a" ->  "upusʻ"
}
"""

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

txt = f'''system "ALA-LC:mya-Mymr:Latn:2011" {{

metadata {{
  authority_id alalc
  id 2011
  language iso-639-2:mya
  source_script Mymr
  destination_script Latn
  name "Burmese Romanization Table (2011)"
  url https://www.loc.gov/catdir/cpso/romanization/burmese.pdf
  creation_date 2011
  adoption_date
  description {{    ALA-LC Burmese Romanization Table, 2011 version. Consonants carry
    the Indic values with the inherent vowel a (Devanagari-style); the
    asa/virama closes the syllable with an ʻ; medials y r v h romanize
    between the consonant and its vowel in the order y-or-r, then v,
    then h; anusvara ṃ; the dot-below and visarga tone marks romanize
    ʹ and ʺ. Modified conjunct ligatures are visual only — Unicode
    text spells the sequences, so no special rows are needed.
    Transcribed from the loc.gov document's text layer.
  }}

  notes {{
    note "Word division: a space after each syllable is applied by the
    caller per the table's word-division section. Abbreviation signs
    e* r* n* l* included."
  }}
}}

{tests}
stage main {{
{block(b_med)}

{block(b_e)}

{block(b_ai)}

{block(b_o)}

{block(b_oas)}

{block(b_ui)}

{block(b_asa)}

{block(b_bare)}

{block(b_rest)}

{block(b_ind)}

{block(b_num)}

{block(b_punct)}

{block(b_abbr)}
}}
}}
'''
Path("maps-staging/alalc-mya-Mymr-Latn-2011.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b_med), len(b_e), len(b_o), len(b_asa), len(b_bare))
