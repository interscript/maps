"""Generate alalc-tha-Thai-Latn-2011.isc — ALA-LC Thai 2011 (task #100).
Rule 5: the inherent vowel is dictionary-determined — bare consonants
romanize WITHOUT an inserted vowel (the D+M composition point)."""
from pathlib import Path

# (letters, initial, final)  final "-" = never
CONS = [("ก","k","k"),("ข","kh","k"),("ฃ","kh","k"),("ค","kh","k"),
    ("ฅ","kh","k"),("ฆ","kh","k"),("ง","ng","ng"),("จ","čh","t"),
    ("ฉ","ch","t"),("ช","ch","t"),("ฌ","ch","t"),("ญ","y","n"),
    ("ด","d","t"),("ฎ","d","t"),("ฑ","th","t"),("ต","t","t"),("ฏ","t","t"),
    ("ถ","th","t"),("ฐ","th","t"),("ท","th","t"),("ธ","th","t"),
    ("ฒ","th","t"),("น","n","n"),("ณ","n","n"),("บ","b","p"),("ป","p","p"),
    ("ผ","ph","p"),("พ","ph","p"),("ภ","ph","p"),("ฝ","f","p"),("ฟ","f","p"),
    ("ม","m","m"),("ย","y",None),("ร","r","n"),("ล","l","n"),("ฬ","l","n"),
    ("ว","w",None),("ศ","s","t"),("ษ","s","t"),("ส","s","t"),("ฮ","h",None)]
CL = [c for c, _, _ in CONS]
INITS = {c: i for c, i, _ in CONS}
FINALS = {c: f for c, i, f in CONS if f and f != i}
CCONS = "".join(CL)

# sign (after C) -> value
VSIGN = {"ะ":"a","ั":"a","า":"ā","ำ":"am","ิ":"i","ี":"ī","ึ":"ư",
         ("ื","อ"):"ưa","ุ":"u","ู":"ū","อ":"ǭ"}
# leading + trailing: (lead, trail, value)
LEADS = [("เ","ะ","e"),("เ","","ē"),("แ","ะ","æ"),("แ","","ǣ"),
         ("โ","ะ","o"),("โ","","ō"),("ไ","","ai"),("ใ","","ai")]
COMBO = [("","ัวะ","ua"),("","ัว","ūa"),("","เอะ","œ"),("","เอ","œ̄"),
         ("","เียะ","ia"),("","เีย","īa"),("","เือะ","ưa"),
         ("","เือ","ư̄a"),("","เาะ","ǫ")]
# offglides: (lead, trail, value) — same shape as LEADS
GLIDE = [("ไ","ย","ai"),("ใ","ย","ai"),("","ัย","ai"),
         ("","าย","āi"),("เ","า","ao"),("","าว","āo"),
         ("","ุย","ui"),("โ","ย","ōi"),("","อย","ǭi"),
         ("เ","ยย","œ̄i"),("เ","ือย","ư̄ai"),("","ัว","ua"),
         ("","ัวะ","ua"),("","ิว","iu"),("เ","็ว","eo"),
         ("เ","ว","ēo"),("แ","ว","ǣo"),("เ","ียว","īeo")]
RUE = [("ฤ","rư"),("ฤื","ri"),("ฤ","rœ̄"),("ฤา","rư̄"),
       ("ฦ","lư"),("ฦา","lư̄")]

b1 = ['    sub "่" ""', '    sub "้" ""', '    sub "๊" ""', '    sub "๋" ""']
b2 = [f'    sub "ห{c}" "{INITS[c]}"' for c in CL if c != "ห"]
b2 += [f'    sub "อ{c}" "{INITS[c]}"' for c in CL if c != "อ"]
b2 += [('    sub "ทร" "s"')]
b3 = []
for s, v in VSIGN.items():
    if isinstance(s, tuple):
        s = "".join(s)
    for c in CL:
        b3.append(f'    sub "{c}{s}" "{INITS[c]}{v}"')
for lead, trail, val in LEADS:
    for c in CL:
        b3.append(f'    sub "{lead}{c}{trail}" "{INITS[c]}{val}"')
for lead, trail, val in GLIDE:
    for c in CL:
        b3.append(f'    sub "{lead}{c}{trail}" "{INITS[c]}{val}"')
for pat, val in RUE:
    b3.append(f'    sub "{pat}" "{val}"')
b4 = [f'    sub "{c}ร" "{INITS[c]}ǭn"' for c in CL if c != "ร"]
b4 += [f'    sub {{ from "{c}" to "{FINALS[c]}" after boundary }}'
       for c in FINALS]
b4 += [f'    sub {{ from "{c}" to "{FINALS[c]}" after any("{CCONS}") }}'
       for c in FINALS]
b5 = [f'    sub "{c}" "{INITS[c]}"' for c in CL]
b5 += [f'    sub "{s}" "{v}"' for s, v in VSIGN.items()
       if not isinstance(s, tuple)]
b5 += [('    sub "อ" "ʻ"')]
b5 += [f'    sub "{a}" "{b}"' for a, b in zip("๐๑๒๓๔๕๖๗๘๙", "0123456789")]
b5 += ['    sub "ฯ" "…"', '    sub "ๆ" "(repeat)"', '    sub "ฯลฯ" "Ia"']

tests = '''tests {
   "\\u0e01\\u0e33" ->  "kam"
   "\\u0e44\\u0e17\\u0e22" ->  "thai"
   "\\u0e19\\u0e04\\u0e23" ->  "nkhǭn"
}
'''

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

txt = f'''system "ALA-LC:tha-Thai:Latn:2011" {{

metadata {{
  authority_id alalc
  id 2011
  language iso-639-2:tha
  source_script Thai
  destination_script Latn
  name "Thai Romanization Table (2011)"
  url https://www.loc.gov/catdir/cpso/romanization/thai.pdf
  creation_date 2011
  adoption_date
  description {{    ALA-LC Thai Romanization Table, 2011 version. Consonants have
    initial and word-final values; tones are not romanized; ho hip and
    the four tone-marking o-ang words are silent before a consonant;
    tho-thanthakhat + ro (ทร) = s. Rule 5: the inherent vowel (o, a,
    or ǭ) is determined from an authoritative dictionary — bare
    consonants therefore romanize without an inserted vowel, the
    composition point for a vocalization model. Transcribed from the
    loc.gov document's complete text layer.
  }}

  notes {{
    note "Rule 5 quoted: Thai consonants are sometimes purely
    consonantal and sometimes followed by an inherent vowel romanized
    o, a, or ǭ depending on the pronunciation as determined from an
    authoritative dictionary. Silent consonants (Rule 6) are not
    detectable from the script alone. Double-function consonants
    (Rule 7) romanize twice at their respective values."
  }}
}}

{tests}
stage main {{
{block(b1)}

{block(b2)}

{block(b3)}

{block(b4)}

{block(b5)}
}}
}}
'''
Path("maps-staging/alalc-tha-Thai-Latn-2011.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b1), len(b2), len(b3), len(b4), len(b5))
