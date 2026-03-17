# German Anki Enricher

David is learning German at **B1 level**. This project generates German vocabulary Anki flashcard decks with audio, grammar fields, and example sentences.

Cards are stored as JSON in `card_data/` and exported to `.apkg` files for import into Anki.

## Primary Workflow

**Focus: cloze deck.** The agent generates word_info JSON (including `cloze_sentences`) → `add_card.py` saves it → rebuild the cloze deck.

```bash
# Add a word (the main workflow — agent generates JSON, CLI saves it)
/add-word drehen

# Or add from JSON directly (use --no-rebuild to skip fact deck rebuild)
.venv/bin/python add_card.py --no-rebuild '{"canonical": "drehen", "word_type": "verb", ...}'

# Rebuild the cloze deck (primary output)
.venv/bin/python build_deck.py --mode cloze --deck-name "German Cloze" --output german_cloze.apkg

# Rebuild the fact deck (secondary, not the current focus)
.venv/bin/python build_deck.py

# Run tests
.venv/bin/python -m pytest tests/test_generator.py -v
```

## File Structure

```
card_data/              one JSON per word (e.g. drehen.json)
audio/                  generated mp3 files (auto-created, do not edit)
added_words.txt         canonical forms already in the deck (one per line)
german_vocabulary.apkg  main fact deck — import this into Anki
german_cloze.apkg       cloze deck — import this into Anki

german_anki_generator.py  core: Anki model, audio, card creation
build_deck.py             builds .apkg from all card_data/ JSONs
add_card.py               CLI: save one word_info JSON + rebuild deck
```

## Word Info Schema

All word types need: `canonical`, `word_type`, `english`, `sentences`

```
word_type    noun | verb | adjective | adverb | phrase | conjunction | preposition | other

Nouns:       article (der/die/das), plural
Verbs:       is_reflexive, also_non_reflexive, perfekt, praeteritum, verb_case, prepositions
Adj/Adv:     adjective_forms ("schön, schöner, am schönsten")
All:         notes (optional)
```

Sentence purposes: `present` · `perfekt` · `preposition` · `meaning`

Dual-reflexive verbs (`also_non_reflexive: true`): one JSON covers both forms; add fields `non_reflexive_canonical`, `non_reflexive_english`, `non_reflexive_sentences`.

## Key Facts

- Run with `.venv/bin/python` — `uv run` fails on Python 3.14 (pydantic-core/PyO3 incompatibility)
- `ANKI_MODEL_ID = 1738291047` is fixed — do not change (Anki uses it to match cards on re-import)
- Noun audio says just "Hund" (no article) — article is tested on the card, don't give it away
- `added_words.txt` is the deduplication source — check it before adding anything
