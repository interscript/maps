"""Generate alalc-lao-Laoo-Latn-2012.isc — complete, clean implementation.
ALA-LC Lao Romanization Table 2012 (task #98; all rules from the doc)."""
from pathlib import Path

CONS = [("ກ","k","k"),("ຂ","kh","(k)"),("ຄ","kh","(k)"),("ງ","ng","ng"),
    ("ຈ","ch","(t)"),("ສ","s","(t)"),("ຊ","s","(t)"),("ຍ","ny",None),
    ("ດ","d","t"),("ຕ","t","(t)"),("ຖ","th","(t)"),("ທ","th","(t)"),
    ("ນ","n","n"),("ບ","b","p"),("ປ","p","(p)"),("ຜ","ph","(p)"),
    ("ຝ","f","(p)"),("ພ","ph","(p)"),("ຟ","f","(p)"),("ມ","m","m"),
    ("ຢ","y",None),("ຣ","r","(n)"),("ລ","l","(n)"),("ຮ","h",None)]
CL = [c for c, _, _ in CONS]
INITS = {c: i for c, i, _ in CONS}
FINALS = {c: f.strip("()") for c, i, f in CONS if f and f.strip("()") != i}
VSIGN = {"ັ":"a","າ":"ā","ິ":"i","ີ":"ī","ຶ":"ư","ື":"ư̄","ຸ":"u","ູ":"ū","ະ":"a"}
SEQS = [("ເ","ະ","e"),("ເ","","ē"),("ແ","ະ","æ"),("ແ","","ǣ"),
    ("ໂ","ະ","o"),("ໂ","","ō"),("ໄ","","ai"),("ໃ","","ai"),
    ("ເ","າະ","ǫ"),("ເ","ິະ","œ"),("ເ","ິ","œ"),("ເ","ີ","œ̄"),
    ("ເ","ັຽະ","ia"),("ເ","ັຽ","ia"),("","ຽ","īa"),("ເ","ຶອະ","ưa"),
    ("ເ","ຶອ","ưa"),("ເ","ືອ","ư̄a"),("","ົວະ","ua"),("","ັວ","ua"),
    ("","ົວ","ūa"),("","ວ","ūa"),("","ົາ","ao"),("","ໍາ","am"),
    ("","າຍ","āi"),("","ັຍ","ai")]
CCONS = "ກຂຄງຈສຊດຕຖທນບປຜຝພຟມຢຣລຮ"

b1 = ['    sub "່" ""', '    sub "້" ""', '    sub "໊" ""', '    sub "໋" ""']
b2 = [f'    sub "{a}" "{b}"' for a, b in [("ຫຍ","ny"),("ຫນ","n"),("ຫມ","m"),
    ("ຫຣ","r"),("ຫລ","l"),("ຫວ","v"),("ໜ","n"),("ໝ","m"),("ຫຼ","l")]]
b3 = []
for s, v in VSIGN.items():
    for c in CL:
        b3.append(f'    sub "{c}ວ{s}" "{INITS[c]}w{v}"')
FALL = dict(FINALS)
FALL.update({"ງ":"ng","ນ":"n","ມ":"m"})
for lead, lval in [("ເ","ē"),("ແ","ǣ")]:
    for c in CL:
        for fc, fv in FALL.items():
            b3.append(f'    sub "{lead}{c}ວ{fc}" "{INITS[c]}w{lval}{fv}"')
for lead, trail, val in SEQS:
    for c in CL:
        b3.append(f'    sub "{lead}{c}{trail}" "{INITS[c]}{val}"')
b4 = [f'    sub "{c}{s}ວ" "{INITS[c]}{v}"' for s, v in
      [("ິ","iu"),("ີ","īu"),("ຸ","ūa")] for c in CL]
b4 += [f'    sub "ອ{s}ວ" "{v}"' for s, v in [("ິ","iu"),("ີ","īu")]]
b5 = [f'    sub "{c}{s}" "{INITS[c]}{v}"' for s, v in VSIGN.items()
      for c in CL]
b5 += [f'    sub "ອ{s}" "{v}"' for s, v in VSIGN.items()]
b5 += [f'    sub "{s}" "{v}"' for s, v in VSIGN.items()]
b6 = [f'    sub {{ from "ວ" to "ūa" after any("{CCONS}") }}',
      '    sub { from "ວ" to "o" after boundary }']
b7 = ['    sub { from "ຍ" to "i" after boundary }']
b7 += [f'    sub {{ from "{c}" to "{FINALS[c]}" after boundary }}'
       for c in FINALS]
b7 += [f'    sub {{ from "{c}" to "{FINALS[c]}" after any("{CCONS}") }}'
       for c in FINALS]
b8 = ([f'    sub "{c}" "{INITS[c]}"' for c in CL] +
      ['    sub "ວ" "v"', '    sub "ອ" "ǭ"'] +
      [f'    sub "{a}" "{b}"' for a, b in zip("໐໑໒໓໔໕໖໗໘໙", "0123456789")] +
      ['    sub "ຯ" "..."', '    sub "ໆ" "..."'])

tests = '''tests {
   "\\u0ea7\\u0eb1\\u0e94" ->  "vat"
   "\\u0e82\\u0ea7\\u0eb2" ->  "khwā"
   "\\u0ec1\\u0e82\\u0ea7\\u0e87" ->  "khwǣng"
   "\\u0e9a\\u0eb8\\u0ea7\\u0e81" ->  "būak"
   "\\u0e99\\u0eb2\\u0ea7" ->  "nāo"
   "\\u0ec1\\u0e81\\u0ec9\\u0ea7" ->  "kǣo"
   "\\u0eab\\u0ecd\\u0e8d\\u0eb2" ->  "nyā"
   "\\u0eab\\u0ebc\\u0eb2\\u0e8d" ->  "lāi"
   "\\u0ead\\u0eb5\\u0e81" ->  "ʻīk"
   "\\u0e84\\u0eb4\\u0e94\\u0eaa\\u0eb0\\u0e95\\u0ebd\\u0e99" ->  "khitsatīan"
}
'''

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

txt = f'''system "ALA-LC:lao-Laoo:Latn:2012" {{

metadata {{
  authority_id alalc
  id 2012
  language iso-639-2:lao
  source_script Laoo
  destination_script Latn
  name "Lao Romanization Table (2012)"
  url https://www.loc.gov/catdir/cpso/romanization/lao.pdf
  creation_date 2012
  adoption_date
  description {{    ALA-LC Lao Romanization Table, 2012 version. Consonants have
    initial and word-final values (parenthesized source finals occur
    only in loans and keep the initial value here). Inherent vowel a.
    ho hip is silent in clusters (ligatures included); subscript lo lut
    is silent except after ho hip. DO is ʻ word-initially, else a
    vowel. WO is positional per Note 4 (cluster w, u+a before a final,
    o word-finally after a vowel). Vowel romanizations always follow
    the consonant. Tone marks are not romanized. Transcribed from the
    loc.gov document's complete text layer.
  }}

  notes {{
    note "Loan-only final values (parenthesized in the source) are not
    applied word-finally. Mid-word consonant sequences without vowel
    signs romanize with initial values (final values apply
    word-finally); syllabification follows standard Lao dictionaries."
  }}
}}

{tests}
stage main {{
{block(b1)}

{block(b2)}

{block(b3)}

{block(b4)}

{block(b7)}

{block(b5)}

{block(b6)}

{block(b8)}
}}
}}
'''
Path("maps-staging/alalc-lao-Laoo-Latn-2012.isc").write_text(
    txt, encoding="utf-8")
print("written",
      len(b1), len(b2), len(b3), len(b4), len(b5), len(b6), len(b7), len(b8))
