"""Generate alalc-lif-Limb-Latn-2011.isc — ALA-LC Limbu 2011."""
from pathlib import Path
C = [("ᤁ","ka"),("ᤂ","kha"),("ᤃ","ga"),("ᤄ","gha"),("ᤅ","ṅa"),
     ("ᤆ","ca"),("ᤇ","cha"),("ᤈ","ja"),("ᤉ","jha"),
     ("ᤋ","ta"),("ᤌ","tha"),("ᤍ","da"),("ᤎ","dha"),("ᤏ","na"),
     ("ᤒ","pa"),("ᤓ","pha"),("ᤔ","ba"),("ᤕ","bha"),("ᤖ","ma"),
     ("ᤗ","ya"),("ᤘ","ra"),("ᤙ","la"),("ᤚ","va"),
     ("ᤛ","śa"),("ᤜ","sa"),("ᤝ","ha")]
V = [(chr(0x1920),"a"),(chr(0x1921),"i"),(chr(0x1922),"u"),
     (chr(0x1923),"ē"),(chr(0x1924),"ai"),(chr(0x1925),"ō"),
     (chr(0x1926),"au")]
VIND = [("ᤀ","a"),("ᤡ","i")][:0]
VIND = [("ᤀ","a"),("ᤡ","i"),("ᤢ","u")][:0]
VIN = [("ᤀ","a"),("ᤡ","i"),("ᤢ","u")]
b2 = [f'    sub "{c}{s}" "{v[:-1]}{sv}"' for c, v in C for s, sv in V]
b1 = [f'    sub "{c}" "{v}"' for c, v in C]
b3 = [f'    sub "{c}" "{v}"' for c, v in VIN]
tests = """tests {
   "\\u1901" ->  "ka"
   "\\u1901\\u1920" ->  "ke"
}
"""
def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"
txt = f'''system "ALA-LC:lif-Limb:Latn:2011" {{

metadata {{
  authority_id alalc
  id 2011
  language iso-639-2:lif
  source_script Limb
  destination_script Latn
  name "Limbu Romanization Table (2011)"
  url https://www.loc.gov/catdir/cpso/romanization/limbu.pdf
  creation_date 2011
  adoption_date
  description {{    ALA-LC Limbu Romanization Table, 2011 version. Twenty-six
    consonants (the Sirijunga alphabet order) with the inherent vowel
    a; the syllable-initial vowel forms per the table; the dependent
    vowel signs (ᤠ ᤡ ᤢ ᤣ ᤤ ᤥ) carry the grammar values, noted per
    the table's Note 1. The Limbu glyphs are visually corresponded to
    the Unicode Limbu block (the PDF's text layer carries no script
    codepoints).
  }}

  notes {{
    note "Note 1: only the syllable-initial vowel forms are listed in
    the source; the dependent-sign values follow Limbu grammar
    practice (ĕ and ō mark the short vowels the script distinguishes)."
  }}
}}

{tests}
stage main {{
{block(b2)}

{block(b1)}

{block(b3)}
}}
}}
'''
Path("maps-staging/alalc-lif-Limb-Latn-2011.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b1), len(b2), len(b3))
