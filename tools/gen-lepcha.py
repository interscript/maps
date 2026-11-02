"""Generate alalc-lep-Lepc-Latn-2012.isc — ALA-LC Lepcha Romanization
Table, September 2012 (earlier version: 1997). Full document: vowels,
consonants, clusters, Notes 1-3, Rules of application 1-3.

Encoding conventions (documented in the map notes):
- Cerebrals: Unicode encodes TTA (1C4D) = tra, TTHA (1C4E) = thra,
  DDA (1C4F) = dra. The table's cerebral nasal (romanized na-dot-below,
  "ṇa") has NO Unicode encoding; this map accepts the invented
  composition LETTER NA + SIGN NUKTA (1C0D + 1C37) for it, following
  the Devanagari nukta-extension precedent.
- ran (1C36) occurs after inherent -a (romanized â) or after the -i
  sign (romanized ī), per the Unicode Standard's Lepcha section.
- Initial vowels = LETTER A (1C23) as vowel carrier + the appropriate
  dependent sign (Unicode Standard); bare A = "a".
- Glottal: A + subjoined ya (Note 2) romanizes "ʼay…" (U+02BC).
- Finals: K M L N P R T + NYIN-DO/KANG (both "ng"; complementary
  contexts per the Unicode Standard).
"""
from pathlib import Path

def L(name):
    for cp in list(range(0x1C00, 0x1C38)) + [0x1C4D, 0x1C4E, 0x1C4F]:
        if chr(cp) and __import__("unicodedata").name(chr(cp), "") == "LEPCHA " + name:
            return chr(cp)
    raise KeyError(name)

A = L("LETTER A")
YSUB = L("SUBJOINED LETTER YA")
RSUB = L("SUBJOINED LETTER RA")
RAN = L("SIGN RAN")
NUK = L("SIGN NUKTA")

NG = chr(0x1E47)  # n-dot-below
CONS = [(L("LETTER KA"), "ka"), (L("LETTER KLA"), "kla"),
    (L("LETTER KHA"), "kha"), (L("LETTER GA"), "ga"),
    (L("LETTER GLA"), "gla"), (L("LETTER NGA"), chr(0x1E45) + "a"),
    (L("LETTER CA"), "ca"), (L("LETTER TSA"), "tsa"),
    (L("LETTER CHA"), "cha"), (L("LETTER TSHA"), "tsha"),
    (L("LETTER JA"), "ja"), (L("LETTER DZA"), "za"),
    (L("LETTER NYA"), "nya"), (L("LETTER TTA"), "tra"),
    (L("LETTER TTHA"), "thra"), (L("LETTER DDA"), "dra"),
    (L("LETTER TA"), "ta"), (L("LETTER THA"), "tha"),
    (L("LETTER DA"), "da"), (L("LETTER NA"), "na"),
    (L("LETTER PA"), "pa"), (L("LETTER PLA"), "pla"),
    (L("LETTER PHA"), "pha"), (L("LETTER FA"), "fa"),
    (L("LETTER FLA"), "fla"), (L("LETTER BA"), "ba"),
    (L("LETTER BLA"), "bla"), (L("LETTER MA"), "ma"),
    (L("LETTER MLA"), "mla"), (L("LETTER YA"), "ya"),
    (L("LETTER RA"), "ra"), (L("LETTER LA"), "la"),
    (L("LETTER VA"), "va"), (L("LETTER WA"), "wa"),
    (L("LETTER SA"), "sa"), (L("LETTER SHA"), "sha"),
    (L("LETTER HA"), "ha"), (L("LETTER HLA"), "hla")]

# dependent vowel signs (per Unicode names); ran handled separately
SGN = [(L("VOWEL SIGN AA"), chr(0x0101)), (L("VOWEL SIGN I"), "i"),
    (L("VOWEL SIGN O"), "o"), (L("VOWEL SIGN OO"), chr(0x014D)),
    (L("VOWEL SIGN U"), "u"), (L("VOWEL SIGN UU"), chr(0x016B)),
    (L("VOWEL SIGN E"), "e")]
RANV = chr(0x00E2)  # â
IILONG = chr(0x012B)  # ī
FIN = [(L("CONSONANT SIGN K"), "k"), (L("CONSONANT SIGN M"), "m"),
    (L("CONSONANT SIGN L"), "l"), (L("CONSONANT SIGN N"), "n"),
    (L("CONSONANT SIGN P"), "p"), (L("CONSONANT SIGN R"), "r"),
    (L("CONSONANT SIGN T"), "t"), (L("CONSONANT SIGN NYIN-DO"), "ng"),
    (L("CONSONANT SIGN KANG"), "ng")]
GL = chr(0x02BC)  # ʼ

ALLSIGN = SGN + [(RAN, RANV)]
CL = [c for c, _ in CONS]
INIT = {c: v for c, v in CONS}

p1 = []
# consonant + sign (+ ran) (+ final): full syllable combinatorics;
# medial ya/ra lose their inherent vowel to a following sign
for c, v in CONS:
    stem = v[:-1]
    for scp, sv in SGN:
        for fcp, fv in FIN:
            p1.append((c + scp + fcp, stem + sv + fv))
            p1.append((c + YSUB + scp + fcp, stem + "y" + sv + fv))
            p1.append((c + RSUB + scp + fcp, stem + "r" + sv + fv))
    for fcp, fv in FIN:
        p1.append((c + L("VOWEL SIGN I") + RAN + fcp, stem + IILONG + fv))
        p1.append((c + RAN + fcp, stem + RANV + fv))

p2 = []
# medials: subjoined ya / subjoined ra (Rules 2-3); invented na+nukta
# (longer medial keys precede the bare medial rows within the pass)
for c, v in CONS:
    stem = v[:-1]
    for scp, sv in SGN:
        p2.append((c + YSUB + scp, stem + "y" + sv))
        p2.append((c + RSUB + scp, stem + "r" + sv))
    for fcp, fv in FIN:
        p2.append((c + YSUB + fcp, stem + "ya" + fv))
        p2.append((c + RSUB + fcp, stem + "ra" + fv))
    p2.append((c + YSUB, stem + "ya"))
    p2.append((c + RSUB, stem + "ra"))
for scp, sv in SGN:
    for fcp, fv in FIN:
        p2.append((L("LETTER NA") + NUK + scp + fcp, NG + sv + fv))
    p2.append((L("LETTER NA") + NUK + scp, NG + sv))
for fcp, fv in FIN:
    p2.append((L("LETTER NA") + NUK + fcp, NG + "a" + fv))
p2.append((L("LETTER NA") + NUK, NG + "a"))
# consonant + ran / sign (ran-after-i rows first: longer keys)
for c, v in CONS:
    stem = v[:-1]
    p2.append((c + L("VOWEL SIGN I") + RAN, stem + IILONG))
    p2.append((c + RAN, stem + RANV))
    for scp, sv in SGN:
        p2.append((c + scp, stem + sv))

p3 = []
# consonant + final (Rule 1: inherent a kept, final appended)
for c, v in CONS:
    for fcp, fv in FIN:
        p3.append((c + fcp, v + fv))

p4 = []
# carrier-A syllables (initial vowels; Note 2 glottal cluster)
for scp, sv in SGN:
    for fcp, fv in FIN:
        p4.append((A + YSUB + scp + fcp, GL + "ay" + sv + fv))
        p4.append((A + scp + fcp, sv + fv))
for fcp, fv in FIN:
    p4.append((A + YSUB + fcp, GL + "ay" + fv))
    p4.append((A + L("VOWEL SIGN I") + RAN + fcp, IILONG + fv))
    p4.append((A + RAN + fcp, RANV + fv))
    p4.append((A + fcp, "a" + fv))
for scp, sv in SGN:
    p4.append((A + YSUB + scp, GL + "ay" + sv))
p4.append((A + YSUB, GL + "ay"))
p4.append((A + L("VOWEL SIGN I") + RAN, IILONG))
p4.append((A + RAN, RANV))
for scp, sv in SGN:
    p4.append((A + scp, sv))

p5 = [f'    sub "{c}" "{v}"' for c, v in CONS] + [f'    sub "{A}" "a"']

def blk(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

def esc(s):
    return "".join(ch if ord(ch) < 0x2000 else "\\u%04X" % ord(ch)
                   for ch in s)

TESTS = [
    ("ka", L("LETTER KA")),
    ("ki", L("LETTER KA") + L("VOWEL SIGN I")),
    ("kā", L("LETTER KA") + L("VOWEL SIGN AA")),
    ("kak", L("LETTER KA") + L("CONSONANT SIGN K")),
    ("kang", L("LETTER KA") + L("CONSONANT SIGN NYIN-DO")),
    ("kat", L("LETTER KA") + L("CONSONANT SIGN T")),
    ("kan", L("LETTER KA") + L("CONSONANT SIGN N")),
    ("kap", L("LETTER KA") + L("CONSONANT SIGN P")),
    ("kam", L("LETTER KA") + L("CONSONANT SIGN M")),
    ("kar", L("LETTER KA") + L("CONSONANT SIGN R")),
    ("kal", L("LETTER KA") + L("CONSONANT SIGN L")),
    ("kya", L("LETTER KA") + YSUB),
    ("mya", L("LETTER MA") + YSUB),
    ("klya", L("LETTER KLA") + YSUB),
    ("kra", L("LETTER KA") + RSUB),
    ("gra", L("LETTER GA") + RSUB),
    ("ʼayuk", A + YSUB + L("VOWEL SIGN U") + L("CONSONANT SIGN K")),
    ("tra", L("LETTER TTA")),
    ("dra", L("LETTER DDA")),
    ("thra", L("LETTER TTHA")),
    ("ṇa", L("LETTER NA") + NUK),
    ("â", A + RAN),
    ("ī", A + L("VOWEL SIGN I") + RAN),
]
tests = "tests {\n" + "".join(
    f'   "{esc(inp)}" ->  "{esc(out)}"\n' for out, inp in TESTS) + "}\n"

txt = f'''system "ALA-LC:lep-Lepc:Latn:2012" {{

metadata {{
  authority_id alalc
  id 2012-09
  language iso-639-2:lep
  source_script Lepc
  destination_script Latn
  name "Lepcha Romanization Table (2012-09)"
  url https://www.loc.gov/catdir/cpso/romanization/lepcha.pdf
  creation_date 2012
  adoption_date
  description {{
    ALA-LC Lepcha Romanization Table, September 2012 version (earlier
    version: 1997). Thirty-nine consonant and cluster letters in the
    guttural/palatal/cerebral/dental/labial arrangement plus
    semivowels, sibilants and the aspirate, with the inherent vowel a
    (Note 3); ten vowel values a ā i ī u ū e o ō â listed in their
    syllable-initial forms (Note 1); final superscripts k ng t n p m r
    l (Rule of application 1); the subjoined ya and ra mutations
    (Rules 2-3); and the glottal carrier of Note 2. Glyphs visually
    corresponded to the Unicode Lepcha block (the PDF's text layer
    carries no script codepoints).
  }}

  notes {{
    note "Note 1: only the vowel forms that appear at the beginning of
    a syllable are listed; the forms used for vowels following a
    consonant exclude the carrier letter, and no distinction between
    the two is made in romanization. Note 2: the letter a is also used
    as a glottal stop and subjoined ya is added to it in a cluster; it
    is romanized with an apostrophe (U+02BC) plus a (document example:
    ayuk with initial glottal stop). Note 3: the vowel a is implicit
    after all consonants and consonant clusters and is supplied in
    romanization, except when another vowel is indicated by its
    appropriate sign. Rule of application 1: the letters used in the
    final position assume superscript shapes above the preceding
    syllable (examples kak kang kat kan kap kam kar kal). Rule 2:
    subjoined ya is added to a consonant cluster without an
    intervening vowel (kya mya klya). Rule 3: subjoined ra likewise
    (kra gra)."
    note "Unicode correspondences: the cerebral stops are encoded as
    the invented letters TTA (U+1C4D, tra), TTHA (U+1C4E, thra) and
    DDA (U+1C4F, dra). The table's cerebral nasal (romanized with
    n-dot-below plus a) has no Unicode encoding; this map accepts the
    composition LETTER NA + SIGN NUKTA (U+1C0D + U+1C37) for it,
    following the Devanagari nukta-extension precedent — an encoding
    convention of this map, not a source form. The final velar nasal
    has two signs in complementary contexts (CONSONANT SIGN NYIN-DO
    U+1C34 without a dependent vowel, CONSONANT SIGN KANG U+1C35 with
    one), both romanized ng. The SIGN RAN (U+1C36) occurs after
    inherent -a (romanized a-circumflex) or after the -i vowel sign
    (romanized i-macron), per the Unicode Standard's Lepcha section;
    syllable-initial forms are the carrier letter plus the same
    signs."
  }}
}}

{tests}
stage main {{
{blk([f'    sub "{k}" "{v}"' for k, v in p1])}

{blk([f'    sub "{k}" "{v}"' for k, v in p2])}

{blk([f'    sub "{k}" "{v}"' for k, v in p3])}

{blk([f'    sub "{k}" "{v}"' for k, v in p4])}

{blk(p5)}
}}
}}
'''
Path("maps-staging/alalc-lep-Lepc-Latn-2012.isc").write_text(
    txt, encoding="utf-8")
n = sum(len(b) for b in (p1, p2, p3, p4, p5))
print("written", n, "rows;", len(TESTS), "tests")
