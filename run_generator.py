#!/usr/bin/env python3
"""
Script to run the German Anki generator on new_words.txt and append to added_words.txt
"""

import os
import random
import sys
from datetime import datetime
import genanki
from dotenv import load_dotenv
from german_anki_generator import read_words_from_file

def load_environment():
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with: ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)
    return api_key

def load_existing_words(added_words_file) -> set[str]:
    existing_words = set()
    if os.path.exists(added_words_file):
        with open(added_words_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_words.add(line)
    return existing_words


def main():
    new_words_file = "new_words.txt"
    added_words_file = "added_words.txt"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"generated_{timestamp}.apkg"
    
    if not os.path.exists(new_words_file):
        print(f"Error: {new_words_file} not found.")
        print(f"Please create {new_words_file} with your German/English words (one per line).")
        sys.exit(1)

    api_key = load_environment()
    
    print(f"Reading words from {new_words_file}...")
    words_to_process = read_words_from_file(new_words_file)
    print(f"Found {len(words_to_process)} words to process.")
    
    if not words_to_process:
        print(f"Error: {new_words_file} is empty or contains no valid words.")
        sys.exit(1)
    
    existing_words = load_existing_words(added_words_file)
    print(f"Found {len(existing_words)} existing words in {added_words_file}")
    
    print(f"\nProcessing words...")
    german_words_to_add = []
    
    from german_anki_generator import get_word_info_and_examples, create_card, create_anki_model, export_deck
    
    model = create_anki_model()
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, 'German Vocabulary')
    
    for i, word in enumerate(words_to_process, 1):
        print(f"\nProcessing {i}/{len(words_to_process)}: {word}")
        
        try:
            print(f"  Getting word info...")
            word_info = get_word_info_and_examples(word, api_key)
            canonical = word_info['german']
            print(f"  ✓ Got: {word_info['german']} → {word_info['english']} ({word_info['word_type']})")
            
            if canonical in existing_words:
                print(f"  - Skipped: already exists")
                continue
            
            print(f"  Creating card...")
            audio_files, _ = create_card(word, api_key, model, deck, 'audio')
            print(f"  ✓ Card created with {len(audio_files)} audio files")
            
            german_words_to_add.append(canonical)
            existing_words.add(canonical)
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            if (i > 1):
                if (len(german_words_to_add) > 0):
                    print(f"Processed {i-1} words before the error. Exporting deck...")
                else:
                    print(f"Processed {i} words before the error. Nothing to export")
            break
    
    
    if german_words_to_add:
        print(f"\nExporting deck...")
        export_deck(deck, output_file, 'audio')

        print(f"Updating {added_words_file}...")
        with open(added_words_file, 'a', encoding='utf-8') as f:
            f.write(f"# {output_file}\n")
            for german_word in german_words_to_add:
                f.write(f"{german_word}\n")
    
    print(f"\nSummary:")
    print(f"  Total words processed: {len(words_to_process)}")
    if (len(german_words_to_add) > 0):
        print(f"  New words added: {len(german_words_to_add)}")
    else:
        print(f"  No new words added")


if __name__ == "__main__":
    main()