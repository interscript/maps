#!/usr/bin/env python3
"""Generate maps/bsi-kor-Kore-Latn-6505-1982-t8.isc from PD 6505:1982 Table VIII.

Transcribed visually from the scan (interscript-private-references/bsi/
PD-6505-1982.pdf, printed p26 = PDF index 27) at 8-10x.

Table VIII = the Sino-Korean layer: McCune-Reischauer-style values
(o-breve / u-macron), the syllable-final assimilation grid, silent
initial ㅇ, ㅆ ss-, and a hyphen between syllables (the document's own
convention in its bracketed examples).

Mechanics: stage split decomposes each covered Hangul syllable into
conjoining jamo (choseong U+1100.. / jungseong U+1161.. / jongseong
U+11A8.. — disjoint ranges so syllable position is encoded by
construction) plus a syllable-final marker (vowel-final ∨,
consonant-final ×) and a trailing hyphen. Stage main then applies, in
one parallel pass (longest match wins): the assimilation pairs
(jong+marker+hyphen+cho), vowel-final voicing (∨+hyphen+cho), the
plain consonant-final rules, word-final finals, vowels, word-initial
consonants, and marker/hyphen cleanup. Every mid-word hyphen is
consumed inside a longer rule, so the remaining hyphens are exactly
the word-final ones and no context constraints are needed — the map
runs identically on every runtime.
"""

CHO = {  # initial key -> (choseong cp, word-initial form)
    "g": (0x1100, "k"), "n": (0x1102, "n"), "d": (0x1103, "t"),
    "r": (0x1105, "r"), "m": (0x1106, "m"), "b": (0x1107, "p"),
    "s": (0x1109, "s"), "": (0x110B, ""), "j": (0x110C, "ch"),
    "ch": (0x110E, "ch'"), "kk": (0x110F, "k'"), "tt": (0x1110, "t'"),
    "pp": (0x1111, "p'"), "h": (0x1112, "h"), "ss": (0x110A, "ss"),
}
INITIALS = list(CHO.keys())

JUNG = {  # vowel key -> (jungseong cp, Table VIII value)
    "a": (0x1161, "a"), "ae": (0x1162, "ae"), "ya": (0x1163, "ya"),
    "yae": (0x1164, "yae"), "eo": (0x1165, "ŏ"), "e": (0x1166, "e"),
    "yeo": (0x1167, "yŏ"), "ye": (0x1168, "ye"),
    "o": (0x1169, "o"), "wa": (0x116A, "wa"), "wae": (0x116B, "wae"),
    "oe": (0x116C, "oe"), "yo": (0x116D, "yo"),
    "u": (0x116E, "u"), "wo": (0x116F, "wŏ"), "we": (0x1170, "we"),
    "wi": (0x1171, "wi"), "yu": (0x1172, "yu"),
    "eu": (0x1173, "ū"), "yui": (0x1174, "ūi"), "i": (0x1175, "i"),
}

JONG = {  # final key -> (jongseong cp, word-final form)
    "g": (0x11A8, "k"), "n": (0x11AB, "n"), "d": (0x11AE, "t"),
    "l": (0x11AF, "l"), "m": (0x11B7, "m"), "b": (0x11B8, "p"),
    "ng": (0x11BC, "ng"),
}

VOWEL_MARK = "∨"   # syllable ending in a vowel (voicing context)
CONS_MARK = "×"    # syllable ending in a consonant final

# Voicing after a vowel-final syllable (the grid's Vowel row)
VOICED = {"g": "g", "d": "d", "b": "b", "j": "j", "r": "r"}

# Assimilation grid: GRID[final_key][initial_key] = cell body from the
# source (the -XY- notation without its dashes). Renders as
# final-side + '-' + initial-side across the syllable hyphen.
GRID = {
    "g": {"g": "kk", "n": "ngn", "d": "kt", "r": "ngn", "m": "ngm",
          "b": "kp", "s": "ks", "j": "kch", "ch": "kch'", "kk": "kk'",
          "tt": "kt'", "pp": "kp'", "h": "kh"},
    "n": {"g": "ng", "n": "nn", "d": "nd", "r": "ll", "m": "nm",
          "b": "nb", "s": "ns", "j": "nj", "ch": "nch'", "kk": "nk'",
          "tt": "nt'", "pp": "np'", "h": "nh"},
    "l": {"g": "lg", "n": "ll", "d": "lt", "r": "ll", "m": "lm",
          "b": "lb", "s": "ls", "": "r", "j": "lch", "ch": "lch'",
          "kk": "lk'", "tt": "lt'", "pp": "lp'", "h": "rh"},
    "m": {"g": "mg", "n": "mn", "d": "md", "r": "mn", "m": "mm",
          "b": "mb", "s": "ms", "j": "mj", "ch": "mch'", "kk": "mk'",
          "tt": "mt'", "pp": "mp'", "h": "mh"},
    "b": {"g": "pk", "n": "mn", "d": "pt", "r": "mn", "m": "mm",
          "b": "pp", "s": "ps", "j": "pch", "ch": "pch'", "kk": "pk'",
          "tt": "pt'", "pp": "pp'", "h": "ph"},
    "ng": {"g": "ngg", "n": "ngn", "d": "ngd", "r": "ngn", "m": "ngm",
           "b": "ngb", "s": "ngs", "j": "ngj", "ch": "ngch'", "kk": "ngk'",
           "tt": "ngt'", "pp": "ngp'", "h": "ngh"},
}

PLAIN_FINAL = {k: v[1] for k, v in JONG.items()}


def hyphenated(f_key, cell):
    """Split a grid cell into final-side + '-' + initial-side."""
    plain = PLAIN_FINAL[f_key]
    if cell.startswith(plain):
        split = len(plain)
    elif cell.startswith("ng") and plain[0] != "n":
        split = 2
    else:
        split = 1
    return cell[:split] + "-" + cell[split:]


def main():
    L = []
    L.append('system "BSI:kor-Kore:Latn:6505-1982-t8" {')
    L.append("")
    L.append("metadata {")
    L.append("  authority_id bsi")
    L.append("  id 6505-1982-t8")
    L.append("  language iso-639-2:kor")
    L.append("  source_script Kore")
    L.append("  destination_script Latn")
    L.append('  name "PD 6505:1982 Table VIII - The Romanization of All Letters in Sino-Korean Words"')
    L.append('  url ""')
    L.append("  creation_date 1982")
    L.append("  adoption_date")
    L.append("  description {    PD 6505:1982, Guide to the romanization of Korean, Table VIII")
    L.append("    (source p26): the Sino-Korean-specific layer of the guide. Values")
    L.append("    are McCune-Reischauer-style: o-breve for the ㅓ series, u-macron")
    L.append("    for ㅡ, w-compounds, the intervocalic voiced forms -g- -d- -b-")
    L.append("    -j- -r-, the syllable-final assimilation grid (-ngn- -ngm- -kt-")
    L.append("    -ls- -rh-), silent initial ㅇ, ㅆ romanized ss-, and a hyphen")
    L.append("    between syllables (the document's own convention in its")
    L.append("    bracketed examples). Transcribed visually from the scan at 8-10x.")
    L.append("    The guide's mechanical system (Part Four) is a separate map.")
    L.append("  }")
    L.append("")
    L.append("  notes {")
    L.append('    note "VOWELS (read at 10x): a ae ya yae ŏ e yŏ ye o wa wae oe yo')
    L.append('    u wŏ we wi yu ū ūi i. The o-series breve and the u-macron are the')
    L.append('    document\'s own printed diacritics (the u-mark is a straight bar')
    L.append('    in the scan, distinct from the o-breve cups)."')
    L.append('    note "INITIALS: k- n- t- (r-) m- p- s- [ㅇ not romanized initially,')
    L.append('    per the source\'s note under the table] ch- ch\'- k\'- t\'- p\'- h-,')
    L.append('    and ss- (the source states ㅆ also occurs as the initial letter of')
    L.append('    Sino-Korean words). Intervocalic voicing per the grid\'s Vowel')
    L.append('    row: -g- -d- -b- -j- -r-."')
    L.append('    note "ASSIMILATION GRID (syllable-final x next-syllable-initial,')
    L.append('    cells read at 8x; encoded as pair rules spanning the syllable')
    L.append('    hyphen): ㄱ row -kk- -ngn- -kt- -ngn- -ngm- -kp- -ks- / ㄴ row -ng-')
    L.append('    -nn- -nd- -ll- -nm- -nb- -ns- / ㄹ row -lg- -ll- -lt- -ll- -lm-')
    L.append('    -lb- -ls- -r- / ㅁ row -mg- -mn- -md- -mn- -mm- -mb- -ms- / ㅂ row')
    L.append('    -pk- -mn- -pt- -mn- -mm- -pp- -ps- -b- / ㅇ row -ngg- -ngn- -ngd-')
    L.append('    -ngn- -ngm- -ngb- -ngs- -ng- (plus the ch ch\' k\' t\' p\' h columns:')
    L.append('    -kch- -kch\'- -kk\'- -kt\'- -kp\'- -kh- / -nj- -nch\'- -nk\'- -nt\'-')
    L.append('    -np\'- -nh- / -lch- -lch\'- -lk\'- -lt\'- -lp\'- -rh- / -mj- -mch\'-')
    L.append('    -mk\'- -mt\'- -mp\'- -mh- / -pch- -pch\'- -pk\'- -pt\'- -pp\'- -ph- /')
    L.append('    -ngj- -ngch\'- -ngk\'- -ngt\'- -ngp\'- -ngh-). The ㄹ row\'s ㅇ column')
    L.append('    is -r- (ㄹ renders r before a vowel-initial syllable). Finals')
    L.append('    before ㅇ-initial syllables otherwise render plain across the')
    L.append('    hyphen, matching the source\'s own [ki-ŏk] and [kun-ŏ] examples."')
    L.append('    note "SOURCE RULES under the table, quoted: ㅇ is not romanized')
    L.append('    when it is the initial letter of a syllable. If the vowel is i-')
    L.append('    or y-, it may be taken as ni- or ny- after consonants in special')
    L.append('    cases, see ¶.22 (special-case epenthesis: recorded, not')
    L.append('    mechanically encoded). Initial ㄹ r- occurs only in foreign words')
    L.append('    in South Korean, but also in Korean words in the North Korean')
    L.append('    spelling. For -lt- as -ld- and -lch- as -ll- in special cases,')
    L.append('    see ¶.10 (recorded, not encoded; the grid\'s default cells are')
    L.append('    what this map applies)."')
    L.append('    note "COVERAGE: Table VIII covers the 14 basic consonants + ㅆ and')
    L.append('    the 21 simple and compound vowels. Syllables with tense initials')
    L.append('    (ㄲ ㄸ ㅃ ㅉ), cluster finals, or letters outside the table pass')
    L.append('    through unchanged: the source states that letters not in Table')
    L.append('    VIII and all vernacular words are covered in its Parts ii and')
    L.append('    iii. Generated by tools/gen-pd6505-t8.py."')
    L.append("  }")
    L.append("}")
    L.append("")
    L.append("tests {")
    for src, want in [
        ("군어", "kun-ŏ"),
        ("기억", "ki-ŏk"),
        ("한자", "han-ja"),
        ("국민", "kung-min"),
        ("국어", "kuk-ŏ"),
        ("부산", "pu-san"),
        ("조선", "cho-sŏn"),
        ("감사", "kam-sa"),
        ("학교", "hak-kyo"),
        ("가인", "ka-in"),
        ("일년", "il-lyŏn"),
        ("의주", "ūi-ju"),
        ("국물", "kung-mul"),
        ("참외", "ch'am-oe"),
    ]:
        L.append(f'   "{src}" ->  "{want}"')
    L.append("}")
    L.append("")
    L.append("stage split {")
    L.append("  parallel {")
    for i_key in INITIALS:
        cho_cp, i_val = CHO[i_key]
        ci = cho_cp - 0x1100
        for v_key, (jung_cp, _) in JUNG.items():
            ji = jung_cp - 0x1161
            vowel_mark = VOWEL_MARK
            syll_v = chr(0xAC00 + (ci * 21 + ji) * 28)
            L.append(f'    sub "{syll_v}" "{chr(cho_cp)}{chr(jung_cp)}{vowel_mark}-"')
            for f_key, (jong_cp, _) in JONG.items():
                fi = (jong_cp - 0x11A8) + 1  # compact order: no-final = 0
                syll_c = chr(0xAC00 + (ci * 21 + ji) * 28 + fi)
                L.append(f'    sub "{syll_c}" "{chr(cho_cp)}{chr(jung_cp)}{chr(jong_cp)}{CONS_MARK}-"')
    L.append("  }")
    L.append("}")
    L.append("")
    L.append("stage main {")
    L.append("  run stage.split")
    L.append("  parallel {")
    # 1. assimilation pairs: jong + consonant-marker + hyphen + choseong
    for f_key, cells in GRID.items():
        jong = chr(JONG[f_key][0])
        for i_key, cell in sorted(cells.items()):
            cho = chr(CHO[i_key][0])
            L.append(f'    sub "{jong}{CONS_MARK}-{cho}" "{hyphenated(f_key, cell)}"')
    # 2. vowel-final + hyphen + initial (voicing / plain / silent ㅇ)
    for i_key in INITIALS:
        cho = chr(CHO[i_key][0])
        val = VOICED.get(i_key, CHO[i_key][1])
        L.append(f'    sub "{VOWEL_MARK}-{cho}" "-{val}"')
    # 3. consonant-final + hyphen + choseong with no grid pair (ㅇ column, ㅆ)
    L.append(f'    sub "{CONS_MARK}-ᄋ" "-"')
    L.append(f'    sub "{CONS_MARK}-ᄊ" "-ss"')
    # 4. word-final finals
    for f_key, (jong_cp, f_val) in JONG.items():
        L.append(f'    sub "{chr(jong_cp)}" "{f_val}"')
    # 5. vowels
    for v_key, (jung_cp, v_val) in JUNG.items():
        L.append(f'    sub "{chr(jung_cp)}" "{v_val}"')
    # 6. word-initial consonants
    for i_key in INITIALS:
        cho = chr(CHO[i_key][0])
        L.append(f'    sub "{cho}" "{CHO[i_key][1]}"')
    # 7. cleanup: markers, then the remaining (word-final) hyphens
    L.append(f'    sub "{VOWEL_MARK}" ""')
    L.append(f'    sub "{CONS_MARK}" ""')
    L.append('    sub "-" ""')
    L.append("  }")
    L.append("}")
    L.append("}")
    L.append("")
    path = "maps/bsi-kor-Kore-Latn-6505-1982-t8.isc"
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
