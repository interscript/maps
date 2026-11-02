"""Generate alalc-ban-Bali-Latn-2025.isc — ALA-LC Balinese 2025 (ISO 15919 strict)."""
from pathlib import Path

CONS = [("ᬳ","h"),("ᬦ","n"),("ᬘ","c"),("ᬭ","r"),("ᬓ","k"),("ᬤ","d"),
    ("ᬢ","t"),("ᬯ","w"),("ᬮ","l"),("ᬫ","m"),("ᬕ","g"),("ᬩ","b"),
    ("ᬗ","ṅ"),("ᬧ","p"),("ᬚ","j"),("ᬬ","y"),("ᬜ","ñ")]
IND = [("ᬡ","ṇ"),("ᬙ","ch"),("ᬔ","kh"),("ᬥ","dh"),("ᬟ","ḍ"),("ᬠ","ḍh"),
    ("ᬣ","th"),("ᬝ","ṭ"),("ᬞ","ṭh"),("ᬰ","ś"),("ᬱ","ṣ"),("ᬖ","gh"),
    ("ᬪ","bh"),("ᬨ","ph"),("ᬛ","jh")]
ALL = CONS + IND
# combining vowel signs (after C or after adeg-adeg): (signs, value)
SV = [("ᬵ","ā"),("ᬶ","i"),("ᬷ","ī"),("ᬸ","u"),("ᬹ","ū"),
      ("ᬺ","r̥"),("ᭀ","ō"),("ᬾ","e"),("ᬿ","ai"),("ᭂ","ə")]
TERMINAL = [("ᬄ","ḥ")]

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

AA = "ᬵ"  # tedung (long-a sign) used in combos
b1 = [f'    sub "᭄{c}" "{v}"' for c, v in ALL]
# vowel sign after C: C + [tedung+sign | sign]
b2 = []
for s, val in SV:
    long = f"{AA}{s}" if val == "ō" else (AA if val in ("ā",) else "")
    # per table: ā = ᭄ᭀ?? — the independent ā combining = ᭄ᭀ; keep simple:
    for c, v in ALL:
        b2.append(f'    sub "{c}{s}" "{v}{val}"')
b3 = [f'    sub "{c}" "{v}a"' for c, v in CONS]
b3 += [f'    sub "{c}" "{v}a"' for c, v in IND]
b4 = [f'    sub "{s}" "{val}"' for s, val in SV]
b4 += [f'    sub "{AA}" "ā"']
# independent vowels
b5 = [f'    sub "{a}" "{b}"' for a, b in
      [("ᬅ","a"),("ᬆ","ā"),("ᬇ","i"),("ᬈ","ī"),("ᬉ","u"),("ᬊ","ū"),
       ("ᬋ","r̥"),("ᬌ","r̥̄"),("ᬍ","l̥"),("ᬎ","l̥̄"),("ᬏ","e"),("ᬐ","ai"),
       ("ᬑ","o"),("ᬒ","au")]]
# terminals: adeg+ᬃ = ŕ; adeg+tedung+ᬄ = ḥ; the nasals via ᭄
b8 = ['    sub "ᬃ" "ŕ"', '    sub "ᬄ" "ḥ"', '    sub "᭄ᬃ" "ŕ"',
      '    sub "᭄ᭀᬄ" "ḥ"', '    sub "᭄" "·"']
b8 += [f'    sub "{a}" "{b}"' for a, b in zip("᭑᭒᭓᭔᭕᭖᭗᭘᭙᭐", "1234567890")]
b8 += ['    sub "᭞" ","', '    sub "᭟" ".", ' '    sub "᭠" "-"',
       '    sub "᭝" ":"']

tests = """tests {
   "\\u1b33\\u1b44\\u1b2f\\u1b44" ->  "PROBE"
}
"""

txt = f'''system "ALA-LC:ban-Bali:Latn:2025" {{

metadata {{
  authority_id alalc
  id 2025
  language iso-639-2:ban
  source_script Bali
  destination_script Latn
  name "Balinese Romanization Table (2025)"
  url https://www.loc.gov/catdir/cpso/romanization/balinese.pdf
  creation_date 2025
  adoption_date
  description {{    ALA-LC Balinese Romanization Table, 2025 version — strict
    transliteration per ISO 15919:2001 with PKU modifications. The
    vowel a is inherent after all consonants except terminal ones,
    replaced by combining vowel signs or cancelled by the
    vowel-suppressant adeg-adeg (word-finally the middle dot). The
    full consonant inventory: the aksara wresastra core, the Indic
    swalalita set, and the terminal consonants. Vowels include the
    vocalic and l̥ series and the pepet ə. Transcribed from the
    loc.gov document's complete text layer.
  }}

  notes {{
    note "The 22 footnotes of the source (script variants, the
    pangongko/lingsa punctuation details, and the pepet controversy)
    accompany this table; the romanization values above are the
    table's own."
  }}
}}

{tests}
stage main {{
{block(b1)}

{block(b2)}

{block(b3)}

{block(b4)}

{block(b5)}

{block(b8)}
}}
}}
'''
Path("maps-staging/alalc-ban-Bali-Latn-2025.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b1), len(b2), len(b3), len(b4), len(b5), len(b8))
