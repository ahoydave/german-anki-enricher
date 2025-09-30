#!/usr/bin/env python3
"""
German Vocabulary Anki Card Generator

This script creates enriched German vocabulary cards for Anki with example sentences 
and audio pronunciations from a text file containing German or English words/phrases.

Usage:
    python german_anki_generator.py input.txt [--output output.apkg]

Features:
- Smart input: Mix German/English words with mistakes - AI detects, corrects, and translates
- Grammatical information: Articles/plurals for nouns, conjugations for verbs, forms for adjectives
- Multiple examples: 3 B1-level example sentences with individual audio playback
- Individual audio: Each example has its own clickable audio button in Anki
- Professional cards: Clean, well-formatted Anki cards ready for studying
- Error correction: Automatically fixes spelling mistakes and provides valid German words
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

import anthropic
import genanki
import gtts
from dotenv import load_dotenv


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with: ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)
    return api_key


def create_anki_model():
    """Create the Anki model for German vocabulary cards"""
    model_id = random.randrange(1 << 30, 1 << 31)
    return genanki.Model(
        model_id,
        'German Vocabulary Model',
        fields=[
            {'name': 'German'},
            {'name': 'English'},
            {'name': 'Examples'},
            {'name': 'Notes'}
        ],
        templates=[
            {
                'name': 'German -> English',
                'qfmt': '<div class="german">{{German}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div class="english">{{English}}</div><br><div class="notes">{{Notes}}</div><br><div class="examples">{{Examples}}</div>',
            },
            {
                'name': 'English -> German',
                'qfmt': '<div class="english">{{English}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer"><div class="german">{{German}}</div><br><div class="notes">{{Notes}}</div><br><div class="examples">{{Examples}}</div>',
            }
        ],
        css='''.card { 
            font-family: arial; 
            font-size: 20px; 
            text-align: center; 
            color: black; 
            background-color: white; 
        }
        .german { 
            font-weight: bold; 
            color: #3399ff; 
        }
        .english { 
            font-style: italic; 
        }
        .examples { 
            text-align: left;
            margin: 15px;
        }'''
    )


def get_word_info_and_examples(word, api_key, max_sentences=3):
    """Get complete word information including language detection, correction, translation, grammar, and examples"""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Analyze the input '{word}' and provide:
1. Detect if this is German or English (even if misspelled)
2. Correct any spelling mistakes and provide the proper German word/phrase
3. English translation
4. Word type (noun, verb, adjective, etc.)
5. Grammar information:
   - If noun: definite article (der/die/das) and plural form
   - If verb: present tense (ich/du/er forms), past tense (ich form), and perfect tense (ich form)
   - If adjective: basic forms and any irregular declensions
6. {max_sentences} B1-level example sentences in German with English translations. Illustrate the various forms, meansing/usage, plural as best you can in simple examples.

IMPORTANT: Always output a valid, commonly used German word/phrase. If the input is unclear, make your best guess at what the user intended.

Return as JSON with this structure:
{{
  "german": "corrected German word/phrase",
  "english": "English translation", 
  "word_type": "noun|verb|adjective|etc",
  "grammar": {{
    "article": "der|die|das (for nouns only)",
    "plural": "plural form (for nouns only)",
    "present": "ich forme, du formst, er formt (for verbs only)",
    "past": "ich formte (for verbs only)", 
    "perfect": "ich habe geformt (for verbs only)",
    "adjective_forms": "basic forms like 'schön, schöner, am schönsten' (for adjectives only)",
  }},
  "sentences": [{{"example": "German text", "translation": "English text"}}]
}}"""
    
    response = client.messages.create(
        model="anthropic.claude-3-7-sonnet-20250219-v1:0",
        max_tokens=1500,
        temperature=0.7,
        system="""You are a helpful German language assistant. You respond only in valid JSON without any additional formatting. Provide accurate grammatical information and natural example sentences.""",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = json.loads(response.content[0].text)
    return result


def generate_audio(text, filename):
    """Generate audio for German text using gTTS"""
    tts = gtts.gTTS(text, lang='de')
    tts.save(filename)
    return filename




def create_card(word, api_key, model, deck, audio_dir):
    """Create an Anki card for a German vocabulary word"""
    # Create audio directory if it doesn't exist
    os.makedirs(audio_dir, exist_ok=True)
    
    # Get complete word information from API (now handles language detection and correction)
    word_info = get_word_info_and_examples(word, api_key)
    
    german = word_info['german']
    english = word_info['english']
    word_type = word_info['word_type']
    grammar = word_info['grammar']
    examples = word_info['sentences']
    
    # Build grammatical notes with enhanced formatting
    grammar_notes = []
    if word_type == 'noun' and grammar.get('article'):
        grammar_notes.append(f"{grammar['article']} {german}")
        if grammar.get('plural'):
            grammar_notes.append(f"Plural: {grammar['plural']}")
    elif word_type == 'verb':
        if grammar.get('present'):
            grammar_notes.append(f"Present: {grammar['present']}")
        if grammar.get('past'):
            grammar_notes.append(f"Past: {grammar['past']}")
        if grammar.get('perfect'):
            grammar_notes.append(f"Perfect: {grammar['perfect']}")
    elif word_type == 'adjective':
        if grammar.get('adjective_forms'):
            grammar_notes.append(f"Forms: {grammar['adjective_forms']}")
    
    # Combine all notes
    all_notes = []
    if grammar_notes:
        all_notes.extend(grammar_notes)
    notes_text = " | ".join(all_notes)
    
    # Format examples with individual audio buttons
    formatted_examples = []
    audio_files = []
    
    for i, example in enumerate(examples, 1):
        # Format each example as: German sentence, English translation
        german_sentence = example['example']
        english_translation = example['translation']
        
        # Generate audio file for this sentence
        audio_filename = os.path.join(audio_dir, f"{german.lower().replace(' ', '_')}_ex{i}.mp3")
        generate_audio(german_sentence, audio_filename)
        audio_files.append(audio_filename)
        
        # Create the formatted example with individual audio button
        audio_tag = f'[sound:{os.path.basename(audio_filename)}]'
        formatted_example = f"""<b>{i}. {german_sentence}</b> {audio_tag}<br>
        <i>{english_translation}</i>"""
        
        formatted_examples.append(formatted_example)
    
    # Join all formatted examples
    all_examples = "<br><br>".join(formatted_examples)
    
    # Create the note for Anki (audio is embedded in examples)
    note = genanki.Note(
        model=model,
        fields=[
            german,
            english,
            all_examples,
            notes_text
        ]
    )
    
    # Add the note to the deck
    deck.add_note(note)
    
    return audio_files, word_info


def read_words_from_file(filename):
    """Read words from a text file, one per line"""
    words = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                word = line.strip()
                if word and not word.startswith('#'):  # Skip empty lines and comments
                    words.append(word)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)
    
    return words


def export_deck(deck, output_filename, audio_dir):
    """Export the deck to an Anki package"""
    # Create media files collection
    media_files = []
    if os.path.exists(audio_dir):
        for file in os.listdir(audio_dir):
            if file.endswith('.mp3'):
                media_files.append(os.path.join(audio_dir, file))
    
    # Create and save the package
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_filename)
    print(f"Deck exported as {output_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate German vocabulary Anki cards from a text file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python german_anki_generator.py words.txt
  python german_anki_generator.py words.txt --output my_deck.apkg

Input file format:
  One word or phrase per line. Lines starting with # are treated as comments.
  Can mix German and English, with or without mistakes - the AI will detect, correct, and translate.
  
  Example words.txt:
    Haus
    lernen
    schön
    # This is a comment
    butterfly
    computer
    hause  # misspelled - will be corrected to "Haus"
    gut    # will show irregular adjective forms
        """
    )
    
    parser.add_argument('input_file', help='Text file containing words (one per line)')
    parser.add_argument('--output', '-o', default='german_vocabulary.apkg', 
                       help='Output Anki deck filename (default: german_vocabulary.apkg)')
    parser.add_argument('--audio-dir', default='audio', 
                       help='Directory for audio files (default: audio)')
    
    args = parser.parse_args()
    
    # Load environment and API key
    api_key = load_environment()
    
    # Read words from file
    print(f"Reading words from {args.input_file}...")
    words = read_words_from_file(args.input_file)
    print(f"Found {len(words)} words to process.")
    
    if not words:
        print("No words found in the input file.")
        sys.exit(1)
    
    # Create Anki model and deck
    model = create_anki_model()
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, 'German Vocabulary')
    
    # Process each word
    successful_cards = 0
    failed_words = []
    
    for i, word in enumerate(words, 1):
        print(f"Processing {i}/{len(words)}: {word}")
        
        try:
            audio_files, word_info = create_card(word, api_key, model, deck, args.audio_dir)
            print(f"  ✓ Created: {word_info['german']} → {word_info['english']} ({word_info['word_type']})")
            successful_cards += 1
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed_words.append(word)
    
    # Export the deck
    print(f"\nExporting deck...")
    export_deck(deck, args.output, args.audio_dir)
    
    # Summary
    print(f"\nSummary:")
    print(f"  Successfully created: {successful_cards} cards")
    if failed_words:
        print(f"  Failed words: {', '.join(failed_words)}")
    print(f"  Deck saved as: {args.output}")
    print(f"  Audio files saved in: {args.audio_dir}/")


if __name__ == "__main__":
    main()
