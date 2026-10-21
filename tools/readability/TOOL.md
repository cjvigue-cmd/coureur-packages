---
name: readability
description: Measures how hard a text is to read: Flesch reading ease, Flesch-Kincaid grade, Gunning fog, sentence length, long sentences, passive voice and the longest sentences. Use to check prose against a plain-language target (grant sections, public notices, instructions) instead of judging it by eye.
requires: json, re
network: no
---

Input `{"text": string}`; Markdown marks are removed first (headings and list items count as sentences).

Prints `{"words", "sentences", "syllables", "words_per_sentence", "flesch_reading_ease", "flesch_kincaid_grade", "gunning_fog", "long_sentences" (over 25 words), "passive_voice" (a form of *be* followed by a past participle), "longest": [{"words", "starts"}]}`.

The formulas are the published ones (Flesch 1948; Kincaid et al. 1975; Gunning 1952). Syllables are estimated from vowel groups, so scores can differ by a point or so from other tools; the same text always gets the same score, which is what a before/after comparison needs. Common targets: grade 8 or lower for the public, reading ease 60 or more for plain language.
