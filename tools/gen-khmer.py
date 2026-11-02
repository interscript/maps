"""Generate alalc-khm-Khmr-Latn-2013.isc — ALA-LC Khmer 2013 (task #99).
All mappings from the loc.gov document; series marks per Note 4;
inherent vowel per the kak/mak/sak examples; coeng = bare consonant."""
from pathlib import Path

CONS = [("ក","k"),("ខ","kh"),("គ","g"),("ឃ","gh"),("ង","ng"),("ច","c"),
    ("ឆ","ch"),("ជ","j"),("ឈ","jh"),("ញ","ñ"),("ដ","ṭ"),("ឋ","ṭh"),
    ("ឌ","ḍ"),("ឍ","ḍh"),("ណ","ṇ"),("ត","t"),("ថ","th"),("ទ","d"),
    ("ធ","dh"),("ន","n"),("ប","p"),("ផ","ph"),("ព","b"),("ភ","bh"),
    ("ម","m"),("យ","y"),("រ","r"),("ល","l"),("វ","v"),("ឝ","ś"),
    ("ឞ","ṣ"),("ស","s"),("ហ","h"),("ឡ","ḷ")]
CM = dict(CONS)
HARD = "ងញមបយរវ"   # ៉ -> ˝
SOFT = "បសហអ"       # ៊ -> ʹ
# dependent vowel signs (single) + combos: (signs, value)
V = [("ា","a"),("ិ","i"),("ី","ī"),("ឹ","ỳ"),("ឺ","ȳ"),("ុ","u"),
     ("ូ","ū"),("ួ","ua"),("ើ","oe"),("ឿ","ẏ"),("ៀ","ia"),("េ","e"),
     ("ែ","ae"),("ៃ","ai"),("ោ","o"),("ៅ","au")]
COMBO = [("ាំ","ām"),("ិះ","iḥ"),("ឹះ","ỳḥ"),("ុះ","uḥ"),("េះ","eḥ"),
         ("ោះ","oah"),("ុំ","um"),("ាំ","ām"),("ំ","am"),("ះ","aḥ")]
IND = [("ឥ","i"),("ឦ","ī"),("ឧ","u"),("ឩ","ū"),("ឰ","ai"),("ឱ","o"),
       ("ឫ","ṛ"),("ឬ","ṝ"),("ឭ","ḷ"),("ឮ","ḹ"),("ឯ","ae"),("ឪ","yu"),
       ("ឳ","au")]

b1 = [f'    sub "{c1}្{c2}" "{v1}{v2}"' for c1, v1 in CONS
      for c2, v2 in CONS]
b2 = ([f'    sub "{c}៉" "{CM.get(c, "ʼ")}˝"' for c in HARD] +
      [f'    sub "{c}៊" "{CM.get(c, "ʹ")}ʹ"' for c in SOFT])
b3 = [f'    sub "{c}ា{c2}់" "{v}â{v2}"' for c, v in CONS
      for c2, v2 in CONS]
b3 += [f'    sub "{c}ុ{s2}" "{CM.get(c, "‛")}{mark}{v2}"'
       for c, mark in [(c, "˝") for c in HARD if c != "ប"]
       + [(c, "ʹ") for c in SOFT if c != "ប"]
       for s2, v2 in [("ិ","i"),("ី","ī"),("ឹ","ỳ"),("ឺ","ȳ")]]
b3 += [f'    sub "{c}ុ{s2}" "{CM[c]}˝{v2}"'
       for c in ["ប"]
       for s2, v2 in [("ិ","i"),("ី","ī"),("ឹ","ỳ"),("ឺ","ȳ")]]
b3 += [f'    sub "{c}{signs}" "{CM[c]}{val}"'
      for signs, val in sorted(COMBO + V, key=lambda r: -len(r[0]))
      for c, _ in CONS]
b3 += [f'    sub "អ{signs}" "‛{val}"'
       for signs, val in sorted(COMBO + V, key=lambda r: -len(r[0]))]
b4 = [f'    sub "{c}ា{c2}់" "{v}â{v2}"' for c, v in CONS
      for c2, v2 in CONS]
b4 = [f'    sub "{c}់" "{v}á"' for c, v in CONS]
b4 += ['    sub "អ់" "‛á"']
b5f = [f'    sub {{ from "{c}" to "{v}" after boundary }}'
       for c, v in CONS]
b5s = [f'    sub "{signs}" "{val}"'
       for signs, val in sorted(COMBO + V, key=lambda r: -len(r[0]))]
b5 = [f'    sub "{c}" "{v}a"' for c, v in CONS]
b5 += ['    sub "អ" "‛"']
b6 = [f'    sub "{c}" "{v}"' for c, v in IND]
b7 = ['    sub "៌" "r"', '    sub "៍" "˚"', '    sub "៎" "ʼ"',
      '    sub "៏" "ʻ"', '    sub "ៈ" "à"', '    sub "័" "ă"']
b8 = ([f'    sub "{a}" "{b}"' for a, b in zip("០១២៣៤៥៦៧៨៩", "0123456789")] +
      ['    sub "ៗ" "(repeat)"', '    sub "។ល។" ".l."', '    sub "។ប។" ".p."',
       '    sub "។" "."', '    sub "៕" "."', '    sub "៖" ":"'])

tests = '''tests {
   "\\u1780\\u1780" ->  "kak"
   "\\u1798\\u1780" ->  "mak"
   "\\u179f\\u1780" ->  "sak"
   "\\u1780\\u1780\\u17cb" ->  "kák"
   "\\u179f\\u1780\\u17cb" ->  "sák"
   "\\u1780\\u17b6\\u1780\\u17cb" ->  "kâk"
   "\\u179f\\u17b6\\u1780\\u17cb" ->  "sâk"
   "\\u1798\\u17bb\\u1793" ->  "mun"
   "\\u1794\\u17bc\\u17b8" ->  "p˝ī"
   "\\u179f\\u17bc\\u17b8" ->  "sʹī"
}
'''

def block(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

txt = f'''system "ALA-LC:khm-Khmr:Latn:2013" {{

metadata {{
  authority_id alalc
  id 2013
  language iso-639-2:khm
  source_script Khmr
  destination_script Latn
  name "Khmer Romanization Table (2013)"
  url https://www.loc.gov/catdir/cpso/romanization/khmer.pdf
  creation_date 2013
  adoption_date
  description {{    ALA-LC Khmer Romanization Table, 2013 version. Consonants carry
    the Indic values (k kh g gh ng c ch j jh ñ ...). A bare consonant
    takes the inherent vowel a (kak mak sak); the coeng subscript
    suppresses it and repeats the consonant value; the bantoc shortens
    the preceding vowel to an acute (kák). The series marks mos-soton
    (˝) and treysap (ʹ) romanize immediately after their consonant.
    Dependent vowels follow the consonant; nikahit am, reahmuk ah, and
    the yuukaleapintu grave per the table. Transcribed from the
    loc.gov document (the dependent-sign glyphs are visually
    corresponded to the Unicode Khmer block; the vowel-table's leading
    mark is table typography, not romanization).
  }}

  notes {{
    note "Subscript consonants repeat the full consonant's value after
    it (kr, khv per the document's krakhvák). The ba + aa ligature
    form romanizes as pâ/pā unchanged. Robat (៌) = r; viriam (៍) = a
    non-combining ring above (U+02DA) word-finally; triisap (៎) = the
    alif; toandakhiat (៏) = the ayn."
  }}
}}

{tests}
stage main {{
{block(b1)}

{block(b2)}

{block(b3)}

{block(b4)}

{block(b5f)}

{block(b5s)}

{block(b5)}

{block(b6)}

{block(b7)}

{block(b8)}
}}
}}
'''
Path("maps-staging/alalc-khm-Khmr-Latn-2013.isc").write_text(
    txt, encoding="utf-8")
print("written", len(b1), len(b2), len(b3), len(b4), len(b5), len(b6),
      len(b7), len(b8))
