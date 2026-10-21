"""readability: how hard a text is to read, by the standard formulas.

Reads input.json: {"text": "..."}. Markdown marks (headings, bullets,
emphasis, links, code) are removed first. Sentences end at . ! ? (not
after a common abbreviation or inside a number) and at blank lines and
list items. Syllables are estimated by vowel groups with the usual
adjustments: an estimate, but the same one every time.
"""
import json
import re

ABBREV = {"e.g", "i.e", "etc", "vs", "dr", "mr", "mrs", "ms", "prof", "inc", "ltd", "co", "fig", "no", "approx", "st", "jr", "sr", "u.s", "cf", "al"}
BE = r"(?:am|is|are|was|were|be|been|being)"
IRREGULAR = "known|shown|given|taken|made|done|seen|found|built|sent|held|written|chosen|driven|kept|left|met|paid|put|read|set|told|thought|brought|bought|caught|taught|won|begun|broken|spoken|stolen|frozen|grown|thrown|drawn|worn|torn|hidden|ridden|forgotten|gotten|bound|wound|sold|led|fed|spent|lent|meant|run|cut|hit|shut|split|spread"
PASSIVE = re.compile(rf"\b{BE}\s+(?:\w+ly\s+)?(?:\w+ed|{IRREGULAR})\b", re.IGNORECASE)


def plain(md):
    t = re.sub(r"```.*?```", " ", md, flags=re.S)
    t = re.sub(r"`[^`]*`", " code ", t)
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"https?://\S+", " link ", t)
    t = re.sub(r"^\s{0,3}#{1,6}\s*(.*)$", r"\1.", t, flags=re.M)  # a heading ends a sentence
    t = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$", lambda m: m.group(1) if re.search(r"[.!?]$", m.group(1)) else m.group(1) + ".", t, flags=re.M)
    t = re.sub(r"[*_]{1,3}", "", t)
    t = re.sub(r"\n\s*\n", ". ", t)  # a blank line ends a sentence
    return t


def sentences(text):
    out, start = [], 0
    for m in re.finditer(r"[.!?]+(?=\s|$)", text):
        before = text[start:m.start()].split()
        word = before[-1].lower().rstrip(".") if before else ""
        if m.group() == "." and (word in ABBREV or re.fullmatch(r"[a-z]", word)):
            continue
        s = text[start:m.end()].strip()
        if re.search(r"[A-Za-z0-9]", s):
            out.append(s)
        start = m.end()
    rest = text[start:].strip()
    if re.search(r"[A-Za-z0-9]", rest):
        out.append(rest)
    return out


def words_of(s):
    # Joined by an apostrophe, hyphen, or a dot or comma between characters: "don't", "e.g", "3.5", "1,200".
    return re.findall(r"[A-Za-z0-9]+(?:['’.,-][A-Za-z0-9]+)*", s)


def syllables(word):
    w = word.lower().replace("’", "'")
    if w.isdigit():
        return max(1, len(w))  # read out digit by digit: an estimate
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return 1
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def main():
    d = json.load(open("input.json"))
    text = plain(d.get("text", ""))
    sents = sentences(text)
    per = [words_of(s) for s in sents]
    per = [w for w in per if w]
    words = [w for ws in per for w in ws]
    if not words:
        print(json.dumps({"error": "no words to read"}))
        return
    n_w, n_s = len(words), len(per)
    syl = [syllables(w) for w in words]
    n_syl = sum(syl)
    complex_words = sum(1 for s in syl if s >= 3)
    wps, spw = n_w / n_s, n_syl / n_w
    longest = sorted(range(n_s), key=lambda i: (-len(per[i]), i))[:3]
    print(json.dumps({
        "words": n_w,
        "sentences": n_s,
        "syllables": n_syl,
        "words_per_sentence": round(wps, 1),
        "flesch_reading_ease": round(206.835 - 1.015 * wps - 84.6 * spw, 1),
        "flesch_kincaid_grade": round(0.39 * wps + 11.8 * spw - 15.59, 1),
        "gunning_fog": round(0.4 * (wps + 100 * complex_words / n_w), 1),
        "long_sentences": sum(1 for ws in per if len(ws) > 25),
        "passive_voice": len(PASSIVE.findall(text)),
        "longest": [{"words": len(per[i]), "starts": " ".join(per[i][:10])} for i in longest if len(per[i]) > 0],
    }))


main()
