# German Anki Enricher

Generates German vocabulary Anki decks with audio, grammar fields, and example sentences. Accepts German or English input in any form (misspelled, non-canonical, past participles, etc.) and normalises to the canonical German form.

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```
   > Note: use `.venv/bin/python` directly — `uv run` fails on Python 3.14 due to a pydantic-core/PyO3 incompatibility.

2. **Set up API key** (required for adding new words):
   ```bash
   echo "ANTHROPIC_API_KEY=your-key-here" > .env
   ```

## Adding Words

### Agent workflow (recommended)

Open the project in Claude Code and use the `/add-word` slash command:

```
/add-word drehen
/add-word sich vorstellen
/add-word "Angst haben"
```

The agent generates the word_info JSON and calls `add_card.py`, which saves the card data and rebuilds `german_vocabulary.apkg`.

### Batch workflow

For processing many words at once (uses the Claude API directly):

```bash
# Put words in new_words.txt (one per line), then:
.venv/bin/python run_generator.py

# Or use set_batch.py to pull from a larger list:
.venv/bin/python set_batch.py 40 && .venv/bin/python run_generator.py
```

## Building Decks

```bash
# Fact deck (default — German↔English with grammar)
.venv/bin/python build_deck.py

# Sentence deck (English sentence → German production)
.venv/bin/python build_deck.py --mode sentence --words-file sentence_30.txt \
  --deck-name "German Sentences" --output german_sentences.apkg

# Cloze deck (fill-in-the-blank with English hints)
.venv/bin/python build_deck.py --mode cloze --words-file cloze_30.txt \
  --deck-name "German Cloze" --output german_cloze.apkg
```

## Card Types

| Mode | Front | Back |
|------|-------|------|
| `fact` | German word | English + article/plural/verb forms + examples |
| `sentence` | English sentence | German sentence + audio |
| `cloze` | German sentence with blank + English hint | Full sentence + audio |

## File Structure

```
card_data/              one JSON file per word (the source of truth)
audio/                  generated mp3 files
added_words.txt         canonical forms already in the deck
german_anki_generator.py  core: Anki model, audio generation, card creation
build_deck.py           builds .apkg files from card_data/
add_card.py             CLI: save one word_info JSON + rebuild deck
run_generator.py        batch processor using the Claude API
set_batch.py            writes next N unprocessed words to new_words.txt
```

## Tests

```bash
.venv/bin/python -m pytest tests/test_generator.py -v

# Real API tests (requires ANTHROPIC_API_KEY):
.venv/bin/python -m pytest tests/test_manual.py -m manual -s
```
