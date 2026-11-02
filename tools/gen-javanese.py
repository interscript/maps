"""Generate alalc-jav-Java-Latn-2012.isc — ALA-LC "Javanese, Sundanese,
and Madurese" romanization table (PDF metadata: converted to MS Word
2012-01-10; the table carries no in-document version date).

Full document: 20 principal consonants (hanacaraka order, regular +
appended forms), 11 aksara murda + 6 aksara rekan (Note 4), vowels and
sandangan (taling e, pepet ĕ, wulu i, taling+tarung o, suku u,
tarung ā), free-standing vowels (a-kara seat, Note 7), other signs
(wignyan h, layar r, cecak ng, pa-cerek rĕ, nga-lelet lĕ, pengkal
ya-medial, cakra ra-medial, Note 5), pangkon/paten (Note 1), numerals,
and Notes 1-9.

Encoding conventions (documented in the map notes):
- Appended consonant forms are glyph variants; Unicode has no separate
  codepoints and romanization is identical.
- Murda default to the plain value; the parenthetical Old Javanese
  alternatives (ṇa, cha, kha, tha, śa, ṣa, pha, jña, gha, bha) are
  recorded in notes per Note 4.
- Rekan = base letter + CECAK TELU (the nukta) + [TARUNG], per the
  table's own glyph decomposition (each rekan cell is base+nukta) and
  the Unicode NamesList equivalence; ʼa = NGA + CECAK TELU (U+2019).
- Note 2 (variable h of ha): the h is preserved uniformly; the
  word-initial drop and the root-final rule are dictionary-dependent
  and recorded in notes only.
- Note 8 (o -> a): recorded in notes only; the rule requires
  word-scoped context.
- Pasangan clusters: the pangkon is retained as a marker on the
  stripped first consonant and consumed by the second-consonant rows
  (this interpreter build ignores before/after context conditions).
- DIRGA marks are colometric and deleted (Note 6); TOLONG normalizes
  to TARUNG (glyph variant of the same sign).
"""
from pathlib import Path

def L(name):
    for cp in range(0xA980, 0xA9E0):
        if __import__("unicodedata").name(chr(cp), "") == "JAVANESE " + name:
            return chr(cp)
    raise KeyError(name)

E = chr(0x0115)      # ĕ
AH = chr(0x2019)     # ʼ (as printed in the table: U+2019)

CONS = [(L("LETTER HA"), "ha"), (L("LETTER NA"), "na"),
    (L("LETTER CA"), "ca"), (L("LETTER RA"), "ra"),
    (L("LETTER KA"), "ka"), (L("LETTER DA"), "da"),
    (L("LETTER TA"), "ta"), (L("LETTER SA"), "sa"),
    (L("LETTER WA"), "wa"), (L("LETTER LA"), "la"),
    (L("LETTER PA"), "pa"), (L("LETTER DA MAHAPRANA"), "dha"),
    (L("LETTER JA"), "ja"), (L("LETTER YA"), "ya"),
    (L("LETTER NYA"), "nya"), (L("LETTER MA"), "ma"),
    (L("LETTER GA"), "ga"), (L("LETTER BA"), "ba"),
    (L("LETTER TTA MAHAPRANA"), "tha"), (L("LETTER NGA"), "nga")]
MURDA = [(L("LETTER NA MURDA"), "na"), (L("LETTER CA MURDA"), "ca"),
    (L("LETTER RA AGUNG"), "ra"), (L("LETTER KA MURDA"), "ka"),
    (L("LETTER TA MURDA"), "ta"), (L("LETTER SA MURDA"), "sa"),
    (L("LETTER SA MAHAPRANA"), "sa"), (L("LETTER PA MURDA"), "pa"),
    (L("LETTER NYA MURDA"), "nya"), (L("LETTER GA MURDA"), "ga"),
    (L("LETTER BA MURDA"), "ba")]
ALL = CONS + MURDA
CL = {c: v for c, v in ALL}

TARUNG = L("VOWEL SIGN TARUNG")
TOLONG = L("VOWEL SIGN TOLONG")
TALING = L("VOWEL SIGN TALING")
PEPET = L("VOWEL SIGN PEPET")
WULU = L("VOWEL SIGN WULU")
SUKU = L("VOWEL SIGN SUKU")
CECAK = L("SIGN CECAK")
WIGNYAN = L("SIGN WIGNYAN")
LAYAR = L("SIGN LAYAR")
DIRGA = L("VOWEL SIGN DIRGA MURE")
PANGKON = L("PANGKON")
TELUN = L("SIGN CECAK TELU")
KERET = L("CONSONANT SIGN KERET")
PENGKAL = L("CONSONANT SIGN PENGKAL")
CAKRA = L("CONSONANT SIGN CAKRA")
AKARA = L("LETTER A")

OSIGN = [(TARUNG, "ā"), (TALING, "e"), (PEPET, E), (WULU, "i"),
         (SUKU, "u"), (TALING + TARUNG, "o")]
OAPP = [(CECAK, "ng"), (WIGNYAN, "h"), (LAYAR, "r")]

REKAN = [(L("LETTER HA"), "h"), (L("LETTER KA"), "kh"),
         (L("LETTER PA"), "f"), (L("LETTER JA"), "z"),
         (L("LETTER GA"), "gh"), (L("LETTER NGA"), AH)]

p0 = [f'    sub "{TOLONG}" "{TARUNG}"']
for sc, _ in OSIGN:
    p0.append(f'    sub "{sc}{DIRGA}" "{sc}"')

p1 = [f'    sub "{L("LETTER NYA")}{PANGKON}{c}" "n{v}"'
      for c, v in [(L("LETTER CA"), "ca"), (L("LETTER JA"), "ja"),
                   (L("LETTER CA MURDA"), "ca")]]

p3 = []
for base, stem in REKAN:
    for sc, sv in OSIGN:
        for ac, av in OAPP:
            p3.append((base + TELUN + sc + ac, stem + sv + av))
    for ac, av in OAPP:
        p3.append((base + TELUN + ac, stem + "a" + av))
    for sc, sv in OSIGN:
        p3.append((base + TELUN + sc, stem + sv))
    p3.append((base + TELUN, stem + "a"))

p5 = []
for c, v in ALL:
    stem = v[:-1]
    for sc, sv in OSIGN:
        for ac, av in OAPP:
            p5.append((c + sc + ac, stem + sv + av))
            p5.append((c + PENGKAL + sc + ac, stem + "y" + sv + av))
            p5.append((c + CAKRA + sc + ac, stem + "r" + sv + av))
    for sc, sv in OSIGN:
        p5.append((c + sc, stem + sv))
        p5.append((c + PENGKAL + sc, stem + "y" + sv))
        p5.append((c + CAKRA + sc, stem + "r" + sv))
    for ac, av in OAPP:
        p5.append((c + ac, v + av))
        p5.append((c + PENGKAL + ac, stem + "ya" + av))
        p5.append((c + CAKRA + ac, stem + "ra" + av))
    p5.append((c + PENGKAL + PANGKON, stem + "y"))
    p5.append((c + CAKRA + PANGKON, stem + "r"))
    p5.append((c + KERET, stem + "r" + E))
    p5.append((c + PENGKAL, stem + "ya"))
    p5.append((c + CAKRA, stem + "ra"))
for base, stem in REKAN:
    p5.append((base + TELUN + PANGKON, stem))
p5.append((AKARA + PANGKON, ""))
for sc, sv in OSIGN:
    p5.append((AKARA + sc, sv))
for ac, av in OAPP:
    p5.append((AKARA + ac, "a" + av))
for sc, sv in OSIGN:
    for ac, av in OAPP:
        p5.append((AKARA + sc + ac, sv + av))
p5.append((AKARA, "a"))

p6a = [f'    sub "{c}{PANGKON}" "{v[:-1]}{PANGKON}"' for c, v in ALL]
p6b = []
for c, v in ALL:
    stem = v[:-1]
    for sc, sv in OSIGN:
        for ac, av in OAPP:
            p6b.append((c + sc + ac, stem + sv + av))
    for sc, sv in OSIGN:
        p6b.append((c + sc, stem + sv))
    for ac, av in OAPP:
        p6b.append((c + ac, v + av))
    p6b.append((c, v))
p6b = [f'    sub "{PANGKON}{k}" "{v}"' for k, v in p6b]
p6c = [f'    sub "{PANGKON}" ""']

p7 = ([f'    sub "{c}" "{v}"' for c, v in ALL] +
      [f'    sub "{AKARA}" "a"'] +
      [f'    sub "{L(n)}" "{v}"' for n, v in [
          ("LETTER I", "i"), ("LETTER II", chr(0x012B)),
          ("LETTER U", "u"), ("LETTER E", "e"), ("LETTER O", "o"),
          ("LETTER I KAWI", "i"), ("LETTER AI", "ai")]] +
      [f'    sub "{chr(0xA9D0 + i)}" "{i}"' for i in range(10)])

def blk(rows):
    return "  parallel {\n" + "\n".join(rows) + "\n  }"

def esc(s):
    return "".join(ch if ord(ch) < 0x2000 else "\\u%04X" % ord(ch)
                   for ch in s)

def W(*cps):
    return "".join(chr(c) for c in cps)

TESTS = [
    ("panca", W(0xA9A5, 0xA99A, 0xA9C0, 0xA995)),               # pa nya-pangkon ca
    ("prenjak", W(0xA9A5, 0xA9C0, 0xA9AB, 0xA9BA, 0xA99A, 0xA9C0, 0xA997, 0xA98F, 0xA9C0)),
    ("angka", W(0xA984, 0xA981, 0xA98F)),
    ("rangga", W(0xA9AB, 0xA981, 0xA992)),
    ("kā", W(0xA98F, 0xA9B4)),
    ("kĕ", W(0xA98F, 0xA9BC)),
    ("ki", W(0xA98F, 0xA9B6)),
    ("ko", W(0xA98F, 0xA9BA, 0xA9B4)),
    ("ku", W(0xA98F, 0xA9B8)),
    ("ke", W(0xA98F, 0xA9BA)),
    ("kang", W(0xA98F, 0xA981)),
    ("kah", W(0xA98F, 0xA983)),
    ("kar", W(0xA98F, 0xA982)),
    ("a", W(0xA984)),
    ("i", W(0xA984, 0xA9B6)),
    ("k", W(0xA98F, 0xA9C0)),
    ("pra", W(0xA9A5, 0xA9C0, 0xA9AB)),
    ("pre", W(0xA9A5, 0xA9C0, 0xA9AB, 0xA9BA)),
    ("kya", W(0xA98F, 0xA9BE)),
    ("kra", W(0xA98F, 0xA9BF)),
    ("krĕ", W(0xA98F, 0xA9BD)),
    ("fa", W(0xA9A5, 0xA9B3)),
    ("kha", W(0xA98F, 0xA9B3)),
    (AH + "a", W(0xA994, 0xA9B3)),
    ("za", W(0xA997, 0xA9B3)),
    ("1", W(0xA9D1)),
    ("naha", W(0xA9A4, 0xA9B2)),
    ("ha", W(0xA9B2)),
]
tests = "tests {\n" + "".join(
    f'   "{esc(inp)}" ->  "{esc(out)}"\n' for out, inp in TESTS) + "}\n"

txt = f'''system "ALA-LC:jav-Java:Latn:2012" {{

metadata {{
  authority_id alalc
  id 2012
  language iso-639-2:jav
  source_script Java
  destination_script Latn
  name "Javanese, Sundanese, and Madurese Romanization Table"
  url https://www.loc.gov/catdir/cpso/romanization/javanese.pdf
  creation_date 2012
  adoption_date
  description {{
    ALA-LC romanization table covering Javanese, Sundanese and
    Madurese (the PDF carries no in-document version date; its
    metadata records conversion to MS Word on 2012-01-10). Twenty
    principal consonants in the hanacaraka order, each with a regular
    and an appended form (Note 1); the aksara murda and aksara rekan
    alternates (Note 4); the vowels and sandangan (taling e, pepet e
    with breve, wulu i, taling plus tarung o, suku u, tarung a-macron)
    with free-standing vowels (Note 5); the other signs wignyan h,
    layar r, cecak ng, pa-cerek re with breve, nga-lelet le with
    breve, pengkal (ya medial) and cakra (ra medial) (Note 5); the
    pangkon vowel suppressor (Note 1); the numerals zero through nine;
    and Notes 1-9. Glyphs corresponded to the Unicode Javanese block
    (the PDF's text layer renders the script in a legacy PUA font).
  }}

  notes {{
    note "Note 1: each consonant has two forms, the regular and the
    appended; the vowel a is implicit after all consonants and
    consonant clusters and should be supplied in transliteration
    unless another vowel is indicated by the appropriate sign or the
    absence of any vowel is indicated by a paten or pangkon sign. The
    appended forms are glyph variants not separately encoded in
    Unicode; this map romanizes them identically through the base
    letters. Note 2: the letter ha often serves as a neutral seat for
    a vowel, in which case the h is not transcribed; generally
    speaking, ha in word-initial or vowel-medial position in a root
    word is romanized without the h, while root word-final ha
    followed by suffixal vowels is always romanized with h; the table
    directs unresolved questions to a standard dictionary of Javanese
    in Latin script (Pigeaud, Poerwodarminto, or Horne). This map
    preserves the h uniformly; the word-initial drop and the
    root-final rule depend on word context and dictionary knowledge
    and are recorded here rather than mechanically guessed. Note 3: the
    letter nya before the letters ja and ca is romanized n, not ny
    (panca, prenjak). Note 4: aksara murda (honorific) default to the
    plain romanization, which is not preserved otherwise; in words of
    Old Javanese origin they represent the parenthetical alternatives
    recorded here: na-murda ṇa (n underdot), ca-murda cha, ka-murda
    kha, ta-murda tha, sa-murda śa (s acute), sa-mahaprana ṣa (s
    underdot), pa-murda pha, nya-murda jña, ga-murda gha, ba-murda
    bha. The aksara rekan mark phonemes alien to Javanese (Arabic and
    Dutch loanwords) and are best romanized per the foreign spelling;
    this map uses the table's values ha kha fa za gha and the glottal
    a-row, encoded as the base letter plus cecak telu (the nukta),
    which is the table's own glyph decomposition."
    note "Note 5: vowels are almost always indicated by agglutinating
    signs (sandangan); free-standing vowels are rare (initial position
    in words of foreign origin); no difference between the two is
    preserved in romanization. Note 6: the dirga marks, which in Old
    Javanese represented long vowels, are colometric devices in New
    Javanese and are not represented in romanization (this map
    deletes them). Note 7: the a-kara is used as a neutral seat that,
    when marked with the appropriate sign, is transliterated i, u,
    etc. Note 8: penultimate o in an open syllable, when the final
    syllable is also open, is romanized a (panca, angka, rangga);
    the rule requires
    word-scoped context and is recorded here rather than mechanically
    guessed. Note 9:
    the ya-pengkal is used in consonant clusters within words;
    clusters between words formed when the second word begins with y
    use the ordinary appended form of ya; the two forms are not
    distinguished in romanization."
  }}
}}

{tests}
stage main {{
{blk(p0)}

{blk(p1)}

{blk([f'    sub "{k}" "{v}"' for k, v in p3])}

{blk([f'    sub "{k}" "{v}"' for k, v in p5])}

{blk(p6a)}

{blk(p6b)}

{blk(p6c)}

{blk(p7)}
}}
}}
'''
Path("maps-staging/alalc-jav-Java-Latn-2012.isc").write_text(
    txt, encoding="utf-8")
n = sum(len(b) for b in (p0, p1, p3, p5, p6a, p6b, p6c, p7))
print("written", n, "rows;", len(TESTS), "tests")
