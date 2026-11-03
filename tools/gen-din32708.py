"""Generate din-jpn-Hrkt-Latn-32708-2014.isc — DIN 32708:2014-08
Romanization of Japanese (modified Hepburn, kana). Sources:
tools/din32708-kana.json (Tabelle 1-2, extracted from the text layer,
row-aware pairing) and tools/din32708-seq.json (Tabelle 3 gairaigo
sequences)."""
import json
from pathlib import Path

base = json.load(Path(__file__).with_name("din32708-kana.json").open())
seq = json.load(Path(__file__).with_name("din32708-seq.json").open())
seq["ヴ"] = "vu"
CONS = "bcdfghjklmnpqrstvwxz"

def double(v):
    return ("t" if v.startswith("ch") else v[0]) + v

MAC = {"a": "\u0101", "i": "\u012b", "u": "\u016b", "e": "\u0113", "o": "\u014d"}
rows = []
for k, v in sorted(seq.items(), key=lambda x: -len(x[0])):
    rows.append((k, v))
    if v[0] in CONS:
        rows.append(("\u3063" + k, double(v)))
        rows.append(("\u30C3" + k, double(v)))
    if v[-1] in MAC and len(v) > 1:
        rows.append((k + "\u30FC", v[:-1] + MAC[v[-1]]))
for k, v in base.items():
    if v[0] in CONS and len(v) > 1:
        rows.append(("\u3063" + k, double(v)))
        rows.append(("\u30C3" + k, double(v)))
    if v[-1] in MAC and len(v) <= 3:
        rows.append((k + "\u30FC", v[:-1] + MAC[v[-1]]))
for k, v in base.items():
    if v[0] in "aiueoy":
        rows.append(("\u3093" + k, "n\u0027" + v))
        rows.append(("\u30F3" + k, "n\u0027" + v))
for k, v in seq.items():
    if v[0] in "aiueoy":
        rows.append(("\u3093" + k, "n\u0027" + v))
rows.append(("\u3093", "n"))
rows.append(("\u30F3", "n"))
for k, v in base.items():
    rows.append((k, v))
rows.sort(key=lambda x: -len(x[0]))
subs = "\n".join(f'    sub "{k}" "{v}"' for k, v in rows)

tests = [
    ("\u304a\u3046", "o\u014d"), ("\u3068\u3046", "t\u014d"),
    ("\u304a\u304a", "o\u014d"), ("\u30a2\u30fc", "a\u014d"),
    ("\u306b\u3044\u304c\u305f", "niigata"),
    ("\u3061\u3044\u3055\u3044", "chiisai"),
    ("\u307b\u3093\u3084\u304f", "hon\u0027yaku"),
    ("\u304b\u3093\u3076\u3093", "kanbun"),
    ("\u3057\u3093\u3076\u3093", "shinbun"),
    ("\u306b\u307b\u3093", "nihon"),
    ("\u307e\u3063\u3061\u3083", "matcha"),
    ("\u304c\u3063\u3053\u3046", "gakk\u014d"),
    ("\u30c1\u30a7\u30c3\u30af", "chekku"),
    ("\u30d5\u30a1\u30a4\u30eb", "fairu"),
    ("\u30c6\u30a3\u30fc", "t\u012b"), ("\u30a4\u30a7", "ye"),
    ("\u30f4\u30a1", "va"), ("\u30b1\u30fc\u30ad", "k\u0113ki"),
    ("\u3086\u304d", "yuki"),
]
tests = "tests {\n" + "".join(f'   "{i}" ->  "{o}"\n' for i, o in tests) + "}\n"

txt = f'''system "DIN:jpn-Hrkt:Latn:32708-2014" {{

metadata {{
  authority_id din
  id 32708-2014
  language iso-639-2:jpn
  source_script Hrkt
  destination_script Latn
  name "DIN 32708:2014-08 Romanization of Japanese (Kana)"
  url https://www.din.de
  creation_date 2014
  adoption_date
  description {{
    DIN 32708:2014-08, Romanization of Japanese: the modified Hepburn
    system of Kenkyusha\'s New Japanese-English Dictionary (3rd/4th
    ed.) applied to the two kana syllabaries in modern orthography
    (gendai kanazukai). Tabelle 1 (the one-mora syllables, including
    the historical kana), Tabelle 2 (the yoon syllables), Tabelle 3
    (the gairaigo sequences, whose readings the norm itself marks as
    proposals), and Tabelle 4 (the subscripted kana, whose sokuon
    doubles the following consonant). Extracted mechanically from the
    standard\'s text layer; both syllabaries are accepted.
  }}

  notes {{
    note "The norm states this is a transcription, not a
    transliteration, and that kanji require their kana readings —
    kanji themselves are outside the tables. Section 5.4: long vowels
    render with macrons regardless of kana representation — the ou
    and oo sequences, ei and uu, and the katakana lengthening mark
    after a vowel kana all yield the macron; the ii double vowels of
    the i-row are distinct and are not merged. Section 5.5: the
    word-internal syllable-final n takes an apostrophe before a vowel
    or y (the modifier letter apostrophe U+02BC is recommended,
    U+0027 permitted — this map uses U+0027), and before b, m and p
    it is written n — the norm\'s own examples (Kanbun, ganmon, Kanpo)
    prescribe n where other systems write m. The sokuon doubles the
    following consonant (Tabelle 4 footnote); ch doubles as tch per
    the Hepburn system. Tabelle 1\'s parenthesized particle readings
    (ha as the topic particle wa, he as the particle e, section 5.8)
    are recorded here and not mechanically encoded — the particle
    readings depend on word identity. Tabelle 3\'s own ANMERKUNG
    states that its gairaigo area is neither unambiguous nor finally
    regulable and its readings are proposals; the fa/fwa style
    variants are encoded with the first-listed reading."
  }}
}}

{tests}
stage main {{
  parallel {{
{subs}
  }}

  # long-vowel and diphthong merges (after the kana pass)
  parallel {{
    sub "ou" "\u014d"
    sub "oo" "\u014d"
    sub "uu" "\u016b"
    sub "ei" "\u0113"
  }}
}}

}}
'''
Path(__file__).resolve().parent.parent.joinpath(
    "maps-staging/din-jpn-Hrkt-Latn-32708-2014.isc").write_text(
    txt, encoding="utf-8")
print("written", len(rows), "rows")
