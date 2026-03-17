---
description: >
  Use this skill whenever the user wants to add German vocabulary to their Anki
  cloze deck — whether that's a single word, a list from a lesson, or words that
  come up naturally in conversation. Also use it when discussing German words,
  checking if something is already in the deck, or generating example sentences.
  The user is David, a B1 German learner. This skill covers the full workflow:
  deciding canonical forms, generating sentences and cloze cards, saving to
  card_data/, and rebuilding german_cloze.apkg.
---

# German Anki Cloze Deck — Add Vocabulary

David is a **B1 German learner**. The goal is to add vocabulary to his cloze
(fill-in-the-blank) Anki deck. Be flexible: sometimes he'll want to discuss
words first; other times just add a batch straight away. Follow his lead.

## Workflow

1. **Check** `added_words.txt` — skip any canonicals already there
2. **Determine** the canonical form(s) for each word (see Canonical Form Rules below)
3. **Discuss** if David wants to — meaning, usage, grammar nuances
4. **Generate** the `word_info` JSON for each word (schema below)
5. **Save**: `.venv/bin/python add_card.py --no-rebuild '<json>'`
6. **Rebuild** the cloze deck once all words are saved:
   `.venv/bin/python build_deck.py --mode cloze --deck-name "German Cloze" --output german_cloze.apkg`

For a single word, steps 5 and 6 can be combined into one `add_card.py` call without `--no-rebuild`.

## Canonical Form Rules

- **Verbs**: infinitive ("gelaufen" → "laufen"; "hat gedreht" → "drehen")
- **Reflexive verbs** that *require* sich: include it ("sich freuen", "sich vorstellen")
- **Nouns**: nominative singular, no article, correctly capitalised ("Hunde" → "Hund")
- Input may be English, misspelled, or inflected — find the intended German word
- **Dual-reflexive verbs**: if a verb has a clearly distinct meaning without "sich"
  (e.g. vorstellen = introduce someone else), set `also_non_reflexive: true` and
  add the non-reflexive fields — `add_card.py` will save both canonicals

## word_info JSON Schema

Omit fields that don't apply to the word type.

```json
{
  "canonical": "base German form",
  "word_type": "noun|verb|adjective|adverb|phrase|conjunction|preposition|other",
  "english": "primary meaning / secondary meaning",

  "article": "der|die|das",
  "plural": "plural form",

  "is_reflexive": false,
  "also_non_reflexive": false,
  "perfekt": "hat/ist + participle  (e.g. hat gedreht)",
  "praeteritum": "1st person singular  (e.g. drehte)",
  "verb_case": "akkusativ|dativ|genitiv|null",
  "prepositions": ["verb + preposition + case  (e.g. denken an + akkusativ)"],

  "adjective_forms": "positive, comparative, superlative  (e.g. schön, schöner, am schönsten)",

  "notes": "non-obvious grammar, register, separability — empty string if nothing to add",

  "sentences": [
    {"german": "...", "english": "...", "purpose": "present|perfekt|preposition|meaning"}
  ],

  "cloze_sentences": [
    {"text": "Er {{c1::dreht}} das Steuer.", "hint": "turns (he, present)", "english": "He turns the steering wheel."}
  ],

  "non_reflexive_canonical": "",
  "non_reflexive_english": "",
  "non_reflexive_sentences": [
    {"german": "...", "english": "...", "purpose": "present|perfekt"}
  ],
  "nr_cloze_sentences": [
    {"text": "Er {{c1::stellt}} seinen Freund vor.", "hint": "introduces (he, present)", "english": "He introduces his friend."}
  ]
}
```

## Sentences (B1 level — simple, natural, correct German)

| Word type | Count | Required purposes |
|-----------|-------|-------------------|
| Verb | 2–3 | present + Perfekt; add 3rd if common preposition |
| Noun | 1–3 | one per distinct meaning; vary singular/plural |
| Adjective / adverb | 1–2 | show most important usage |
| Phrase / other | 1 | |

## Cloze Sentences

Every word needs `cloze_sentences`. Each sentence is a standalone Anki note — always use `{{c1::...}}` (reset to c1 each time).

**What to blank by word type:**

| Word type | Required cloze sentences |
|-----------|--------------------------|
| Verb | 3–4: present (er/sie form) · Perfekt participle · Präteritum · preposition blank if applicable |
| Noun | 2: singular with `{{c1::article}} {{c1::noun}}` blanked together · plural form only |
| Adjective / adverb | 1–2: target word blanked |
| Phrase / other | 1–2: key word(s) blanked |

**Hints** (English only — never include the German word; empty string for preposition blanks):

- Verb present: `"turns (he, present)"`
- Verb Perfekt: `"turned (Perfekt)"`
- Verb Präteritum: `"turned (Präteritum)"`
- Verb preposition blank: `""`
- Noun singular: `"rocket"`
- Noun plural: `"rockets (plural)"`
- Adjective: `"quiet (predicative)"`

**Never give away noun gender** — no article or gendered pronoun adjacent to a blanked noun.
