"""Generate alalc-bod-Tibt-Latn-2015.isc — ALA-LC Tibetan 2015 (Wylie)."""
import unicodedata
from pathlib import Path

BASE = [("ཀ","k"),("ཁ","kh"),("ག","g"),("ང","ng"),("ཅ","c"),("ཆ","ch"),
    ("ཇ","j"),("ཉ","ny"),("ཏ","t"),("ཐ","th"),("ད","d"),("ན","n"),
    ("པ","p"),("ཕ","ph"),("བ","b"),("མ","m"),("ཙ","ts"),("ཚ","tsh"),
    ("ཛ","dz"),("ཝ","w"),("ཞ","zh"),("ཟ","z"),("འ","ʼ"),("ཡ","y"),
    ("ར","r"),("ལ","l"),("ཤ","sha"),("ས","sa"),("ཧ","ha"),("ཨ","a")]
EXT = [("ཊ","ṭ"),("ཋ","ṭh"),("ཌ","ḍ"),("ཎ","ṇ"),("གྷ","gh"),("དྷ","dh"),
       ("བྷ","bh")]
ALL = BASE + EXT
V = [(chr(0x0F71),"ā"),(chr(0x0F72),"i"),(chr(0x0F73),"ī"),
     (chr(0x0F74),"u"),(chr(0x0F75),"ū"),(chr(0x0F76),"r̥"),
     (chr(0x0F77),"r̥̄"),(chr(0x0F78),"l̥"),(chr(0x0F79),"l̥̄"),
     (chr(0x0F7A),"e"),(chr(0x0F7B),"ai"),(chr(0x0F7C),"o"),
     (chr(0x0F7D),"au")]

def bare(v):
    if v == "a": return ""
    if v == "sha": return "sh"
    if v == "ʼa" or v == "ʼ": return "ʼ"
    return v[:-1] if v.endswith("a") else v

BAREVAL = {c: bare(v) for c, v in ALL}
SUBVAL = {}
for cp in range(0x0F90, 0x0FBD):
    name = unicodedata.name(chr(cp), "")
    if "SUBJOINED LETTER" in name:
        base_cp = cp - 0x50
        SUBVAL[chr(cp)] = BAREVAL.get(chr(base_cp)) or \
            name.split("SUBJOINED LETTER ")[1].lower().replace("-a", "ʼ")

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

b1 = [f'    sub "{c}{sc}" "{BAREVAL[c]}{SUBVAL[sc]}"'
      for c in BAREVAL for sc in sorted(SUBVAL, key=ord)]
b2 = [f'    sub "{c}{s}" "{v}{val}"' for s, val in V for c, v in ALL]
b3 = [f'    sub "{c}" "{v}a"' for c, v in ALL]
b3 += [f'    sub "{s}" "{val}"' for s, val in V]
b4 = ['    sub "ཾ" "ṃ"', '    sub "ྃ" "m̐"', '    sub "ཿ" "ḥ"',
      '    sub "྅" "`"']
b4 += [f'    sub "{chr(c)}" ""' for c in (0x0F0B, 0x0F0C)]
b5 = [f'    sub "{a}" "{b}"' for a, b in [("གཡ","gʹya"),("ནཡ","nʹya")]]
b6 = [f'    sub "{a}" "{b}"' for a, b in zip("༠༡༢༣༤༥༦༧༨༩", "0123456789")]

tests = """tests {
   "\\u0f40\\u0f0b" ->  "ka"
   "\\u0f40\\u0f71\\u0f0b" ->  "kā"
   "\\u0f40\\u0f90\\u0f0b" ->  "kka"
   "\\u0f40\\u0f7a\\u0f0b" ->  "ke"
   "\\u0f40\\u0f72\\u0f42\\u0f0b" ->  "kiga"
}
"""

txt = f'''system "ALA-LC:bod-Tibt:Latn:2015" {{

metadata {{
  authority_id alalc
  id 2015
  language iso-639-2:bod
  source_script Tibt
  destination_script Latn
  name "Tibetan Romanization Table (2015)"
  url https://www.loc.gov/catdir/cpso/romanization/tibetan.pdf
  creation_date 2015
  adoption_date
  description {{    ALA-LC Tibetan Romanization Table, 2015 version — the Wylie
    system. Every base consonant carries the inherent vowel a (Note 2);
    subjoined letters take no vowel; the thirteen vowel signs include
    the vocalic r and l and the a-chung lengthening (ā); the ʼa chung
    (འ) romanizes as the alif. Non-Tibetan retroflex and aspirate
    extensions per the special-letter section. Transcribed from the
    loc.gov document.
  }}

  notes {{
    note "Note 3: the ʼa chung is the alif unless marked with a vowel
    sign (then alif + vowel). Notes 8-9: the non-joiner disambiguator
    ʹ appears in the documented clusters g.ya and n.ya. Stacked
    consonants are explicit in Unicode as subjoined letters (U+0F90
    ff.), each romanized bare after its base."
  }}
}}

{tests}
stage main {{
{block(b1)}

{block(b2)}

{block(b3)}

{block(b4)}

{block(b5)}

{block(b6)}
}}
}}
'''
Path("maps-staging/alalc-bod-Tibt-Latn-2015.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b1), len(b2), len(b3), len(b4), len(b5), len(b6))
