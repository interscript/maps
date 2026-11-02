"""Generate alalc-cjm-Cham-Latn-2015.isc — ALA-LC Cham Romanization
Table, 2015 version (no earlier versions). Full document: the consonant
table (Akhar Thrah + Akhar Srak living/dead forms), independent vowels,
Takai Akhar Hadiip (living vowel modifiers), Takai Akhar Mâtai (dead
feet), the Hua Bilau (Note 1), Western Cham special characters,
numerals, example words from the Cham calendar, and Notes 1-2.

Glyph correspondence: the romanization sequence matches the Unicode
Cham block order exactly (ngâ=NGUE, nyâ=NHUE, nja=NHJA, nâ=NUE,
nda=DDA, xa=SSA, mâ=MA, mba=BBA), so every glyph column is resolved by
alignment; the text layer renders script glyphs as ASCII lookalikes.

Encoding conventions (documented in the map notes):
- AA2D (U) romanizes â per the table's -u/â- row; AA32 (UE) romanizes
  u per the -u- row; validated by the examples Mânuk and Tikuh.
- Dead feet: vowel signs + the two final consonant signs
  (FINAL-NG AA43, FINAL-M AA4C); letter finals keep the inherent vowel
  (ka + final-k -> kak), sign finals replace it (Mânuk: ma+â, na+u+K).
- The table's dead forms -ph -b -w have NO Unicode encoding (the block
  has no final PH/B/W); recorded in notes, not silently dropped.
- The Western Cham special characters (soft mla/ma, rolled ra, Ppo,
  nân, negation oh, word-repeat) have no Unicode codepoints; recorded
  in notes.
- Hua Bilau (AA29): elongates the vowel (a->aa, o->oo) per Note 1;
  its word-final "may end with a vowel" reading is recorded.
- The modifier -ae- and the -lua reading have ambiguous glyph cells in
  the source (ASCII-lookalike collisions); recorded in notes. EI AA2C
  romanizes ei (its NamesList value, matching the dead-foot -ei row).
"""
from pathlib import Path

def L(name):
    for cp in range(0xAA00, 0xAA60):
        if __import__("unicodedata").name(chr(cp), "") == "CHAM " + name:
            return chr(cp)
    raise KeyError(name)

def W(*cps):
    return "".join(chr(c) for c in cps)

AB = chr(0x00E2)  # â

CONS = [(L("LETTER KA"), "ka"), (L("LETTER KHA"), "kha"),
    (L("LETTER GA"), "ga"), (L("LETTER GHA"), "gha"),
    (L("LETTER NGUE"), "ngâ"), (L("LETTER NGA"), "nga"),
    (L("LETTER CHA"), "ca"), (L("LETTER CHHA"), "cha"),
    (L("LETTER JA"), "ja"), (L("LETTER JHA"), "jha"),
    (L("LETTER NHUE"), "nyâ"), (L("LETTER NHA"), "nya"),
    (L("LETTER NHJA"), "nja"), (L("LETTER TA"), "ta"),
    (L("LETTER THA"), "tha"), (L("LETTER DA"), "da"),
    (L("LETTER DHA"), "dha"), (L("LETTER NUE"), "nâ"),
    (L("LETTER NA"), "na"), (L("LETTER DDA"), "nda"),
    (L("LETTER PA"), "pa"), (L("LETTER PPA"), "ppa"),
    (L("LETTER PHA"), "pha"), (L("LETTER BA"), "ba"),
    (L("LETTER BHA"), "bha"), (L("LETTER MA"), "mâ"),
    (L("LETTER BBA"), "mba"),
    (L("LETTER YA"), "ya"), (L("LETTER RA"), "ra"),
    (L("LETTER LA"), "la"), (L("LETTER VA"), "wa"),
    (L("LETTER SSA"), "xa"), (L("LETTER SA"), "sa"),
    (L("LETTER HA"), "ha")]

VOW = [(L("LETTER A"), "a"), (L("LETTER I"), "i"),
       (L("LETTER U"), "u"), (L("LETTER E"), "e"),
       (L("LETTER AI"), "ai"), (L("LETTER O"), "o")]

FIN = [(L("LETTER FINAL K"), "k"), (L("LETTER FINAL G"), "g"),
    (L("LETTER FINAL NG"), "ng"), (L("CONSONANT SIGN FINAL NG"), "ng"),
    (L("LETTER FINAL CH"), "c"), (L("LETTER FINAL T"), "t"),
    (L("LETTER FINAL N"), "n"), (L("LETTER FINAL P"), "p"),
    (L("LETTER FINAL Y"), "y"), (L("LETTER FINAL R"), "r"),
    (L("LETTER FINAL L"), "l"), (L("LETTER FINAL SS"), "x"),
    (L("CONSONANT SIGN FINAL M"), "m"), (L("CONSONANT SIGN FINAL H"), "h")]

SGN = [(L("VOWEL SIGN AA"), None), (L("VOWEL SIGN I"), "i"),
    (L("VOWEL SIGN II"), "ii"), (L("VOWEL SIGN EI"), "ei"),
    (L("VOWEL SIGN U"), AB), (L("VOWEL SIGN OE"), "e"),
    (L("VOWEL SIGN O"), "o"), (L("VOWEL SIGN AI"), "ai"),
    (L("VOWEL SIGN AU"), "au"), (L("VOWEL SIGN UE"), "u")]
HB = SGN[0][0]
SG = [s for s, _ in SGN[1:]]

# per-consonant modifier values (Takai Akhar Hadiip)
MOD = [(L("CONSONANT SIGN YA"), "ia"), (L("VOWEL SIGN I"), "i"),
    (L("VOWEL SIGN II"), "ii"), (L("VOWEL SIGN EI"), "ei"),
    (L("VOWEL SIGN U"), AB), (L("VOWEL SIGN OE"), "e"),
    (L("VOWEL SIGN O"), "o"), (L("VOWEL SIGN AI"), "ai"),
    (L("VOWEL SIGN AU"), "au"), (L("VOWEL SIGN UE"), "u"),
    (L("CONSONANT SIGN WA"), "ua"), (L("CONSONANT SIGN LA"), "la"),
    (L("CONSONANT SIGN RA"), "ra")]

YASG = L("CONSONANT SIGN YA")
LASG = L("CONSONANT SIGN LA")
RASG = L("CONSONANT SIGN RA")
WASG = L("CONSONANT SIGN WA")
UESG = L("VOWEL SIGN UE")
USG = L("VOWEL SIGN U")
OESG = L("VOWEL SIGN OE")
OSG = L("VOWEL SIGN O")
FNG = L("CONSONANT SIGN FINAL NG")
FM = L("CONSONANT SIGN FINAL M")

MODV = [s for s in MOD if s[0] not in (YASG, LASG, RASG, WASG)]

p1 = []
# dead feet: medial+vowel+final combos, vowel+final-sign combos, then
# pairs, then long combos
for c, v in CONS:
    stem = v[:-1]
    for sc, sv in MODV:
        for fc, fv in FIN:
            p1.append((c + YASG + sc + fc, stem + "y" + sv + fv))
            p1.append((c + RASG + sc + fc, stem + "r" + sv + fv))
    for fc, fv in FIN:
        p1.append((c + WASG + UESG + fc, stem + "ua" + fv))
        p1.append((c + LASG + UESG + fc, stem + "lu" + fv))
        p1.append((c + LASG + USG + fc, stem + "l" + AB + fv))
    p1.append((c + OESG + OSG + FNG, stem + "ao" + "ng"))
    p1.append((c + OESG + OSG, stem + "ao"))
    for sc, sv in MOD:
        for fc, fv in FIN:
            p1.append((c + sc + fc, stem + sv + fv))
    for fc, fv in FIN:
        p1.append((c + fc, v + fv))
# vowel letters + inherent (bare letters handled in p4)
# Hua Bilau: o-doubling row first, then generic elongation
for c, v in CONS:
    p1.append((c + OSG + HB, v[:-1] + "oo"))
    p1.append((c + HB, v + "a"))

p2 = []
# vowel-letter + final (independent vowels close syllables too)
for c, v in VOW:
    for fc, fv in FIN:
        p2.append((c + fc, v + fv))

p3 = []
# modifier pairs first (longer keys), then single modifier signs
for c, v in CONS:
    stem = v[:-1]
    for sc, sv in MODV:
        p3.append((c + YASG + sc, stem + "y" + sv))
        p3.append((c + RASG + sc, stem + "r" + sv))
    p3.append((c + LASG + UESG, stem + "lu"))
    p3.append((c + LASG + USG, stem + "l" + AB))
    p3.append((c + WASG + UESG, stem + "ua"))
    for sc, sv in MOD:
        p3.append((c + sc, stem + sv))

p4 = ([f'    sub "{c}" "{v}"' for c, v in CONS] +
      [f'    sub "{c}" "{v}"' for c, v in VOW] +
      [f'    sub "{chr(0xAA50 + i)}" "{i}"' for i in range(10)])

def blk(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

def esc(s):
    return "".join(ch if ord(ch) < 0x2000 else "\\u%04X" % ord(ch)
                   for ch in s)

TESTS = [
    ("tikuh", W(0xAA13, 0xAA2A, 0xAA06, 0xAA32, 0xAA4D)),
    ("kra", W(0xAA06, 0xAA34)),
    ("mânuk", W(0xAA20, 0xAA2D, 0xAA18, 0xAA32, 0xAA40)),
    ("asaih", W(0xAA00, 0xAA27, 0xAA30, 0xAA4D)),
    ("asau", W(0xAA00, 0xAA27, 0xAA31)),
    ("pabaiy", W(0xAA1A, 0xAA1D, 0xAA30, 0xAA48)),
    ("tapay", W(0xAA13, 0xAA1A, 0xAA48)),
    ("rimaong", W(0xAA23, 0xAA2A, 0xAA20, 0xAA2E, 0xAA2F, 0xAA43)),
    ("inâ garay", W(0xAA01, 0xAA18, 0xAA2D, 0x20, 0xAA08, 0xAA23, 0xAA48)),
    ("ula anaih", W(0xAA02, 0xAA24, 0x20, 0xAA00, 0xAA18, 0xAA30, 0xAA4D)),
    ("kak", W(0xAA06, 0xAA40)),
    ("kang", W(0xAA06, 0xAA42)),
    ("kaa", W(0xAA06, 0xAA29)),
    ("koo", W(0xAA06, 0xAA2F, 0xAA29)),
    ("kung", W(0xAA06, 0xAA32, 0xAA43)),
    ("kia", W(0xAA06, 0xAA33)),
    ("kla", W(0xAA06, 0xAA35)),
    ("kai", W(0xAA06, 0xAA30)),
    ("7", W(0xAA57)),
]
tests = "tests {\n" + "".join(
    f'   "{esc(inp)}" ->  "{esc(out)}"\n' for out, inp in TESTS) + "}\n"

txt = f'''system "ALA-LC:cjm-Cham:Latn:2015" {{

metadata {{
  authority_id alalc
  id 2015
  language iso-639-2:cjm
  source_script Cham
  destination_script Latn
  name "Cham Romanization Table (2015 version)"
  url https://www.loc.gov/catdir/cpso/romanization/cham.pdf
  creation_date 2015
  adoption_date
  description {{
    ALA-LC Cham Romanization Table, 2015 version (no earlier
    versions). The table serves both Akhar Thrah (Eastern Cham) and
    Akhar Srak (Western Cham), whose letters share the Unicode Cham
    block. Thirty-five consonants and semivowels with living (hadiip)
    and dead (mâtai) forms, six independent vowels, the living vowel
    modifiers (Takai Akhar Hadiip) including the medials ya/ra/la/wa,
    the dead feet (Takai Akhar Mâtai) with inherent consonant or vowel
    endings, the Hua Bilau vowel elongator, the numerals zero through
    nine, twelve example words from the Cham calendar, and Notes 1-2.
  }}

  notes {{
    note "Note 1: the Hua Bilau character marks the written word and
    ends in a vowel sound in Eastern Cham; in Western Cham it is the
    Plao A and only elongates vowel sounds (/a/ becomes /aa/, /o/
    becomes /oo/, etc.). The textbook compilation society and some
    Eastern Cham manuscripts also use it to elongate, a usage
    critiqued by senior experts; for this standard the Hua Bilau
    elongates the vowel in the middle of a word, and at the end of a
    word it means the word can end with a vowel sound. This map
    encodes the elongation (a after the vowel value, with the
    doubled-oo row for o); the word-final permission reading is not
    mechanically distinct and is recorded here. Note 2: the word
    Inâ (Eastern Cham) is romanized Enaa in Western Cham per a
    spelling variation. The independent vowel romanized e here is
    printed é in the Akhar Thrah column (the map emits e; the acute
    variant is a Thrah convention)."
    note "Unicode correspondences: the consonant romanization
    sequence aligns exactly with the Unicode Cham block order
    (ngâ=NGUE, nyâ=NHUE, nja=NHJA, nâ=NUE, nda=DDA, xa=SSA, mâ=MA,
    mba=BBA), and each letter's living and dead forms map to the base
    letters and the LETTER FINAL / CONSONANT SIGN FINAL codepoints.
    MUE, which falls between BHA and MA in the Unicode order, does not
    appear in the table and is not encoded.
    The modifier romanized â is VOWEL SIGN U (the table's -u/â row,
    with u as the variant reading); the modifier romanized u is
    VOWEL SIGN UE (the -u- row), validated by the examples Mânuk and
    Tikuh. EI romanizes ei, matching the dead-foot -ei row; the
    living modifier printed -ae- shares that glyph class and is
    recorded rather than separately encoded. The -lua modifier's
    glyph cell collides with -lu- in the source text layer and is
    recorded here; -lu- is encoded as the la medial plus UE. Dead
    feet -eng -aung -aong -aum -im -em are vowel signs combined with
    the final NG or M signs; -ao- is OE plus O (yielding the
    inherent-vowel a plus o). The table's dead forms -ph -b -w have
    no Unicode encoding (the block has no final PH, B or W); the
    examples Kubaw and Pabuei depend on them and are recorded rather
    than testable. The Western Cham special characters (soft mla and
    ma, rolled ra, the respect title Ppo, nân, the negation marker
    oh, and the word-repeat marker) have no Unicode codepoints and
    are recorded here from the table's special-characters section."
  }}
}}

{tests}
stage main {{
{blk([f'    sub "{k}" "{v}"' for k, v in p1])}

{blk([f'    sub "{k}" "{v}"' for k, v in p2])}

{blk([f'    sub "{k}" "{v}"' for k, v in p3])}

{blk(p4)}
}}
}}
'''
Path("maps-staging/alalc-cjm-Cham-Latn-2015.isc").write_text(
    txt, encoding="utf-8")
n = sum(len(b) for b in (p1, p2, p3, p4))
print("written", n, "rows;", len(TESTS), "tests")
