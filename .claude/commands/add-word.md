Add $ARGUMENTS to the German Anki deck.

You are Claude Code working in David's German Anki project. David is a B1 German learner. Generate the word_info JSON for the word and save it using the CLI.

## Steps

1. Determine the canonical form and word type for "$ARGUMENTS"
2. Generate the complete word_info JSON (schema below)
3. Run: `.venv/bin/python add_card.py '<json>'`
4. Report: canonical form(s) added, word type, English meaning

## Canonical Form Rules

- Verbs: infinitive form ("gedreht" → "drehen", "lief" → "laufen")
- Verbs that REQUIRE "sich": include it ("sich freuen", "sich vorstellen")
- Nouns: nominative singular, no article, correctly capitalised ("Hunde" → "Hund")
- Input may be English, misspelled, or a non-canonical form — find the intended German word
- Dual-reflexive verbs (e.g. sich vorstellen / vorstellen): one JSON handles both; `add_card.py` saves both canonicals

## JSON Schema

Generate this exact structure. Omit fields not relevant to the word type.

```json
{
  "canonical": "base German form",
  "word_type": "noun|verb|adjective|adverb|phrase|conjunction|preposition|other",
  "english": "primary meaning / secondary meaning",
  "is_reflexive": false,
  "also_non_reflexive": false,

  "article": "der|die|das",
  "plural": "plural form",

  "perfekt": "hat/ist + past participle (e.g. hat gedreht)",
  "praeteritum": "first person singular (e.g. drehte)",
  "verb_case": "akkusativ|dativ|genitiv|null",
  "prepositions": ["verb + preposition + case (e.g. drehen an + dativ)"],

  "adjective_forms": "positive, comparative, superlative (e.g. schön, schöner, am schönsten)",

  "notes": "",
  "sentences": [
    {"german": "example sentence", "english": "translation", "purpose": "present|perfekt|preposition|meaning"}
  ],

  "non_reflexive_canonical": "",
  "non_reflexive_english": "",
  "non_reflexive_sentences": [
    {"german": "example sentence", "english": "translation", "purpose": "present|perfekt"}
  ]
}
```

## Sentence Rules (all at B1 level — simple, natural, correct German)

- **Nouns**: 1–3 sentences. One per important meaning; if one meaning, show different contexts (e.g. singular and plural)
- **Verbs**: 2–3 sentences — always present tense + Perfekt; add a 3rd if the verb has a common preposition
- **Adjectives/Adverbs**: 1–2 sentences showing most important usage
- **Phrases/conjunctions/other**: 1 sentence
- Max 3 sentences for any word

## Dual-Reflexive Verbs (`also_non_reflexive: true`)

Set ONLY if the verb has a clearly distinct common meaning WITHOUT "sich" (e.g. sich vorstellen = to imagine/introduce oneself; vorstellen = to introduce someone else).

When true:
- `non_reflexive_canonical`: infinitive without "sich"
- `non_reflexive_english`: English meaning of the non-reflexive form
- `non_reflexive_sentences`: exactly 2 sentences (present + Perfekt)

## Field Notes

- `english`: all meanings worth knowing, separated by ` / `
- `notes`: only if there's something non-obvious (separability, case nuance, register). Empty string if nothing to add.
- `is_reflexive`: true if "sich" is part of the canonical form
- `verb_case`: the case the verb governs ("null" if none / not applicable)
