# German Anki Enricher

David is learning German at **B1 level**. This project generates German vocabulary Anki flashcard decks with audio, grammar fields, and example sentences.

Cards are stored as JSON in `card_data/` and exported to `.apkg` files for import into Anki.

## Primary Workflow

The agent generates word_info JSON → `add_card.py` saves it → deck is rebuilt.

```bash
# Add a word (the main workflow — agent generates JSON, CLI saves it)
/add-word drehen

# Or add from JSON directly
.venv/bin/python add_card.py '{"canonical": "drehen", "word_type": "verb", ...}'

# Rebuild deck manually
.venv/bin/python build_deck.py

# Build experimental decks (sentence or cloze mode)
.venv/bin/python build_deck.py --mode sentence --words-file sentence_30.txt --deck-name "German Sentences" --output german_sentences.apkg
.venv/bin/python build_deck.py --mode cloze    --words-file cloze_30.txt    --deck-name "German Cloze"     --output german_cloze.apkg

# Batch-process many words automatically (uses Claude API, requires ANTHROPIC_API_KEY)
.venv/bin/python set_batch.py 40 && .venv/bin/python run_generator.py

# Run tests
.venv/bin/python -m pytest tests/test_generator.py -v
```

## File Structure

```
card_data/              one JSON per word (e.g. drehen.json)
audio/                  generated mp3 files (auto-created, do not edit)
added_words.txt         canonical forms already in the deck (one per line)
german_vocabulary.apkg  main fact deck — import this into Anki
german_sentences.apkg   sentence-mode experiment (30 words)
german_cloze.apkg       cloze-mode experiment (30 words)

german_anki_generator.py  core: Anki model, audio, card creation, API call
build_deck.py             builds .apkg from all card_data/ JSONs
add_card.py               CLI: save one word_info JSON + rebuild deck
run_generator.py          batch processor (calls Claude API for each word)
set_batch.py              writes next N unprocessed words to new_words.txt
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
