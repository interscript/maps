"""Generate odni-zho-Hani-Latn-2015.isc — ICS 630-01 Annex D (2015),
Standards for the Transliteration of Chinese Personal Names in Written
Reports and Products.

Source data: tools/ics-630-01-annexd.json (extracted by
tools/extract-ics-630-01-annexd.py from the ICS 630-01 Annex D documents).

The IC standard for Chinese personal names is Hanyu Pinyin with the
annex's modifications. The character-level data of the annex:
  - Appendix C supplies hanzi -> IC transliteration for the common
    surnames (116 printed entries, 115 distinct characters; 范 is
    printed twice).
  - The orthographic modifications of the main text and Appendix A that
    are realizable at character level: the umlaut fold (the standard
    "uses u for the ü character: Lu, Nu"), the apostrophe prohibition
    (criterion f, paragraph 14), and word-initial capitalization
    (criterion b), the latter applied through boundary postrules.
Appendix A (the syllable inventory, 411 cells) and Appendix B (the
cross-system conversion table, 397 rows) are recorded in the map notes
and preserved in full in the JSON artifact; neither adds a character
mapping beyond identity and the fold above.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "ics-630-01-annexd.json").read_text())

entries = data["appendix_c"]["entries"]
assert len(entries) == 116, f"expected 116 printed entries, got {len(entries)}"
chars = [e["char"] for e in entries]
assert len(set(chars)) == 115, "expected 115 distinct surname characters"

# dedupe by character (the duplicated 范 entries share the IC primary "Fan")
by_char = {}
for e in entries:
    if e["char"] in by_char:
        assert by_char[e["char"]]["ic"] == e["ic"], (
            f"conflicting IC primary for {e['char']}: "
            f"{by_char[e['char']]['ic']} vs {e['ic']}"
        )
        continue
    by_char[e["char"]] = e
assert len(by_char) == 115

subs = []
sub_index = {}  # char -> position in subs
for e in entries:
    alt = e["alternates"]
    comment = f"# STC {e['stc']}"
    if alt:
        comment += "; as printed: " + e["ic"] + ", " + ", ".join(alt)
    if e["char"] in sub_index:
        earlier = entries[[x["char"] for x in entries].index(e["char"])]
        merged = (f"# STC {e['stc']}; character printed twice in the list"
                  f" (both STC {earlier['stc']}); first entry as printed: "
                  f"{earlier['ic']}"
                  + (", " + ", ".join(earlier["alternates"])
                     if earlier["alternates"] else "")
                  + f"; second entry as printed: {e['ic']}"
                  + (", " + ", ".join(alt) if alt else ""))
        subs[sub_index[e["char"]]] = f'    sub "{e["char"]}" "{e["ic"]}"  {merged}'
        continue
    sub_index[e["char"]] = len(subs)
    subs.append(f'    sub "{e["char"]}" "{e["ic"]}"  {comment}')

assert len(subs) == 115, f"expected 115 rules, got {len(subs)}"

# orthographic rules: umlaut fold (u for ü), apostrophe prohibition
rule_subs = [
    '    # The umlaut (ü), as in Lü and Nü, should not be used: the standard',
    '    # uses u for the ü character (main text; Appendix A cells Lu, Lue,',
    '    # Nu, Nue).',
    '    sub "ü" "u"',
    '    # No apostrophe (’) should be used between syllables; other',
    '    # forensic information disambiguates instead (criterion f, para 14).',
    '    sub "’" ""',
    '    sub "\'" ""',
]

# document examples (title case per name part; hyphen of the married
# double surname is retained and both surnames capitalized)
tests = []
tests.append(("# Appendix C: List of Common Chinese Surnames — one test per"
              " printed entry, IC primary form.", None))
for e in entries:
    tests.append((None, (e["char"], e["ic"], f"STC {e['stc']}")))

doc_tests = [
    ("lü", "Lu"), ("nü", "Nu"),          # umlaut rule, as printed
    ("lüe", "Lue"), ("nüe", "Nue"),      # Appendix A cells
    ("Lü Lin", "Lu Lin"),
    ("xi’an", "Xian"), ("xi'an", "Xian"),  # para 14 apostrophe prohibition
    # Document examples, romanized input through the orthographic rules:
    # criteria b (title case per name part), e (hyphen only for the
    # married double surname), g (compound surname one capitalized word).
    ("zhang wei", "Zhang Wei"),
    ("hu jintao", "Hu Jintao"),
    ("ouyang xiu", "Ouyang Xiu"),
    ("zhou youguang", "Zhou Youguang"),
    ("ouyang qianqing", "Ouyang Qianqing"),
    ("ma yingjiu", "Ma Yingjiu"),         # printed with STC 7456/5391/0036
    ("luo jiahui", "Luo Jiahui"),         # printed with STC 7482/1367/6540
    ("huang haoran", "Huang Haoran"),     # also seen as Wong Hoi-yin
    ("chen-li meiling", "Chen-Li Meiling"),
]
tests.append(("# Umlaut fold and apostrophe rules (main text; Appendix A).",
              None))
for t in doc_tests[:7]:
    tests.append((None, (t[0], t[1], None)))
tests.append(("# Document examples through the orthographic rules"
              " (criteria b, e, g): Zhang Wei, Hu Jintao, Ouyang Xiu, Zhou"
              " Youguang, Ouyang Qianqing, Ma Yingjiu (STC: 7456/5391/0036),"
              " Luo Jiahui [IC Standard: Luo Jiahui, STC: 7482/1367/6540],"
              " Huang Haoran (also Wong Hoi-yin), Chen-Li Meiling.",
              None))
for t in doc_tests[7:]:
    tests.append((None, (t[0], t[1], None)))

test_lines = []
for comment, pair in tests:
    if pair is None:
        test_lines.append(f"   {comment}")
        continue
    src, out, note = pair
    if note:
        test_lines.append(f'   "{src}" ->  "{out}"  # {note}')
    else:
        test_lines.append(f'   "{src}" ->  "{out}"')
tests_block = "tests {\n" + "\n".join(test_lines) + "\n}\n"

body = "\n".join(subs) + "\n\n" + "\n".join(rule_subs)

postrules = '''  # POSTRULES
  # Capitalize the first letter of each name part (criterion b): the
  # surname and the given-name block are each capitalized, the rest of
  # the letters stay lower case. Word boundaries include the space
  # between surname and given name and the hyphen of the married double
  # surname (both surnames capitalized). The set is spelled out in
  # single characters: only the lower case ASCII letters carry case.
  sub {
    from any("abcdefghijklmnopqrstuvwxyz")
    to upcase
    before boundary
    not_before boundary + any("‘’'")
  }
  sub {
    from any("abcdefghijklmnopqrstuvwxyz")
    to upcase
    before boundary + any("‘’'")
  }
'''

out = f'''system "ODNI:zho-Hani:Latn:2015" {{

metadata {{
  authority_id odni
  id 2015
  language iso-639-2:zho
  source_script Hani
  destination_script Latn
  name ICS-630-01 Romanization of Chinese Personal Names (2015)
  source ICS-630-01 Annex D
  creation_date 2015
  confirmation_date 2015-08
  description {{    This system applies to personal names rendered in Modern Chinese as
    represented in the Hanyu Pinyin Romanization System. It does not
    apply to names that are represented in other systems or in
    Romanization schemes or practices that are used to represent
    personal names in Chinese dialects.

    The Intelligence Community (IC) standard for transliterating Chinese
    personal names into English is the Hanyu Pinyin Romanization System
    (or pinyin), officially known as the Scheme of the Chinese Phonetic
    Alphabet (汉语拼音方案), with several modifications as specified in
    this document (e.g., absence of umlauted ü, title case for
    surnames). In 1982 the International Organization for
    Standardization (ISO) codified the Hanyu Pinyin Romanization System
    as ISO 7098, Information and Documentation – Romanization of Chinese
    (Second Edition, 12-15-1991).

    The primary purpose for designating a singular system is to allow
    for a consistent transcription of names that is specifically
    readable to the English-speaking non-specialist. It is not intended
    to be fully "reversible". Disambiguation should be accomplished by
    providing additional information following best practices of the
    issuing organization: the Unicode-encoded form of the original
    Chinese characters, the original encoding scheme if other than
    Unicode (e.g., Big5 or GB), whether traditional or simplified
    characters were used, and Standard Telegraphic Code (标准电码)
    representations (The Standard Telegraph Codebook, revised edition,
    PRC Ministry of Post and Telecommunications) — e.g., Ma Yingjiu
    (STC: 7456/5391/0036). Use simplified (or short form) characters as
    the default; traditional (or long form) characters may be used for
    non-Mainland persons.

    Personal names in Chinese should be transliterated into the IC
    Standard in accordance with the following criteria:

    a. the surname (family name) should appear first, followed by the
       given name
    b. the surname should be separated from the given name and be
       followed by the given name. The initial letter of each name
       should be capitalized, with the rest in lower case letters
    c. commas should not be placed between the surname and given name
    d. syllables should not be separated in the given name
    e. hyphens should not be used between any syllables (except as
       noted in paragraph 12)
    f. apostrophes should not be used between any syllables (see
       paragraph 14 for details)
    g. compound surnames should be capitalized with no space between
       the characters

    Examples include Zhang Wei, Hu Jintao, Ouyang Xiu, Zhou Youguang,
    and Ouyang Qianqing. If an official spelling of a name differs from
    the IC Standard, it may be used throughout the document, with the
    IC Standard spelling included where capabilities allow.

    When a married woman uses both her surname and her husband's
    surname, both surnames are capitalized, but a hyphen should be used
    to separate the surnames (e.g., Chen-Li Meiling; the first surname
    is the husband's, the second the wife's maiden name).

    The umlaut (ü), as in Lü and Nü, should not be used. The standard
    uses u for the ü character: Lu, Nu. No apostrophe (’) should be
    used between syllables; other forensic information (e.g. original
    Chinese characters, STC codes) should be used where necessary to
    disambiguate syllable combinations. Any additional ambiguity should
    be addressed in a Translator's Comment.
  }}

  notes {{
    # Encoded transformation
    note "This map encodes the character-level data of the annex: the
    surname characters of Appendix C (List of Common Chinese Surnames,
    116 printed entries over 115 distinct characters), the umlaut fold
    (u for ü), the apostrophe prohibition (criterion f, paragraph 14),
    and word-initial capitalization of each name part (criterion b),
    applied through boundary postrules. The name-formation rules
    (criteria a, c, d, g) operate above the character level and are not
    encoded. Given-name characters have no character mapping: the annex
    provides no general hanzi-to-pinyin character table — its hanzi
    data is the surname list of Appendix C only. Given names must
    already be in pinyin orthography (the standard's stated domain) and
    pass through the orthographic rules unchanged apart from the fold,
    the apostrophe removal and the capitalization."
    # Appendix A — IC Transliteration Table (D-4)
    note "Appendix A is the IC syllable inventory: 411 initial-final
    cells over 39 printed final columns and 25 initial rows (the
    zero-initial row and b c ch d f g h j k l m n p q r s sh t w x y z
    zh). Its cells print the IC syllable forms, title-cased; this map
    realizes them through the word-initial capitalization postrule —
    orthographically the cells are standard pinyin except the umlaut
    columns (lü, lüe, nü, nüe printed as Lu, Lue, Nu, Nue) and the
    anomalies recorded here, all as printed and none silently
    corrected: the header prints two adjacent columns both labeled
    'i' — the cells of the z, c, s and y rows (Zi Ci Si Yi) sit under
    the first and those of the zh, ch, sh and r rows (Zhi Chi Shi Ri)
    under the second, distinguishing the two apical vowel readings of
    the letter i; the w- row carries a 'Wong' cell under the ong column
    alongside 'Weng' under eng — wong is not a standard pinyin syllable
    (the dialectal surname form); the k- row carries 'Kei', which the
    standard orthography does not list; the standard syllables wen
    (present in Appendix B), nun, len and nia are absent from the
    table, as are the interjection syllables (m, n, ng, hm, hng, fiao);
    and the two printed columns 'uen' and 'ueng' carry no cells in any
    row. The complete grid is preserved in
    tools/ics-630-01-annexd.json (cells: initial, final, input syllable,
    IC form)."
    # Appendix B — Conversion Table (D-5..D-18)
    note "Appendix B is a Conversion Table of Common Chinese
    Romanization Systems: 397 rows of IC (Based on Pinyin), Wade-Giles,
    Yale and Mandarin Phonetic (Zhuyin) syllable correspondences. It is
    a cross-romanization reference, outside the scope of a
    Hani-to-Latin character map, and is preserved in full in
    tools/ics-630-01-annexd.json. As printed it contradicts the
    normative umlaut rule: its IC column spells lü, lüe, nü, nüe as
    'lyu', 'lue', 'nyu', 'nue' (Wade-Giles lü, lüeh, nü, nüeh), where
    the main text and Appendix A prescribe Lu, Lue, Nu, Nue — the
    normative forms are encoded here. Its bo row prints the Zhuyin cell
    ㄅㄠㄛ where the standard spelling is ㄅㄛ. It additionally
    contains wen and yai rows absent from Appendix A, and omits the
    Appendix A cells chua, dei, den, dia, ei, eng, kei, lia, lo, me, o,
    rua, shei, tei, wong, zhei and the umlaut spellings lü, lüe, nü,
    nüe."
    # Appendix C — anomalies
    note "Appendix C anomalies, as printed: 范 appears twice, both
    times with STC 5400 and the IC primary Fan (the second entry adds
    the alternate Farn); the list prints the traditional forms 呂 (0712
    Lu), 萬 (5502 Wan) and 葉 (5509 Ye) alongside simplified forms,
    although the main text directs to use simplified characters as the
    default — the characters are mapped exactly as printed; the 柯 cell
    prints 'Ke, Ker, and Quah' with a literal 'and', which is preserved
    in the rule comment. Each rule comment carries the entry's Standard
    Telegraphic Code (标准电码) and the non-IC alternate renditions
    printed after the IC form; the alternates are other common
    renditions, not IC Standard outputs, and do not participate in the
    mapping."
    # Main-text rules outside the character mapping
    note "Main-text rules recorded but not encoded: persons who have
    adopted English names give the English name first (David Dai Ho,
    Elaine L. Chao, Gary F. Locke — IC Standard Luo Jiahui, STC
    7482/1367/6540); variant spellings are retained in parentheses
    (Huang Haoran, also seen as Wong Hoi-yin and Raymond Wong); an
    official spelling may override the IC Standard spelling; residual
    ambiguity (nicknames, former married names) is addressed in a
    Translator's Comment."
    # Parent standard memo (ICS 630-01 cover)
    note "The annex is issued under ICS 630-01, Foreign Language
    Transliteration Standards (Intelligence Community Standard
    630-01): transliteration is standardized within the IC on all
    finished analytical reports and products; FLTS for individual
    languages are developed and reviewed by each IC element's Senior
    Language Authority, promulgated as annexes titled Standards for
    the Transliteration of Personal Names in Written Reports and
    Products, issued by the ADNI through the Foreign Language Program
    Office. The standard is effective 10 August 2015, the date of
    signature (Deana A. Krichter, ADNI for Human Capital)."
  }}
}}

{tests_block}
stage main {{
  parallel {{
    # APPENDIX C — List of Common Chinese Surnames (D-19..D-22)
    # Each rule: character -> IC transliteration; comment carries the
    # printed STC code and the non-IC alternate renditions.
{body}
  }}

{postrules}}}
}}
'''

# hard lessons: brace balance, single final newline
assert out.count("{") == out.count("}"), (
    f"brace mismatch: {{={out.count('{')} }}={out.count('}')}"
)
if not out.endswith("\n"):
    out += "\n"
assert out.endswith("\n") and not out.endswith("\n\n"), (
    "map must end with exactly one trailing newline"
)

dest = HERE.parent / "maps" / "odni-zho-Hani-Latn-2015.isc"
dest.write_text(out, encoding="utf-8")
print(f"wrote {dest}")
print(f"rules: {len(subs)} surname + 3 orthographic; tests: "
      f"{sum(1 for c, p in tests if p is not None)}")
