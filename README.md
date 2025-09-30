# German Anki Card Generator

Creates German vocabulary Anki cards with examples and audio from a text file. Handles both German and English input with automatic correction and translation.

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up API key:**
   Create a `.env` file:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Usage

**Quick start:**
```bash
python run_generator.py
```

This reads `new_words.txt`, generates `generated_deck.apkg`, and appends words to `added_words.txt`.

**Manual usage:**
```bash
uv run python german_anki_generator.py words.txt --output deck.apkg
```

**Input format:** One word per line in `new_words.txt` (can mix German/English with mistakes).
