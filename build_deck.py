#!/usr/bin/env python3
"""
Build an Anki deck from saved card data.

Modes:
  fact     – standard word/grammar cards (default)
  sentence – English sentence → German sentence production
  cloze    – fill-in-the-blank cloze deletion cards

Examples:
  python build_deck.py
  python build_deck.py --mode sentence --words-file sentence_30.txt --deck-name "German Sentences" --output german_sentences.apkg
  python build_deck.py --mode cloze    --words-file cloze_30.txt    --deck-name "German Cloze"     --output german_cloze.apkg
"""
import argparse
import random

import genanki

from german_anki_generator import (
    create_anki_model,
    create_cloze_model,
    create_sentence_model,
    create_cards,
    create_cloze_cards,
    create_sentence_cards,
    export_deck,
    load_all_word_infos,
    load_word_infos_for,
)

AUDIO_DIR = 'audio'


def build_deck(mode='fact', deck_name='German Vocabulary', output_file=None, words_file=None):
    if output_file is None:
        output_file = 'german_vocabulary.apkg' if mode == 'fact' else f'german_{mode}.apkg'

    if words_file:
        word_infos = load_word_infos_for(words_file)
    else:
        word_infos = load_all_word_infos()

    if not word_infos:
        print('No card data found. Run the generator first.')
        return

    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)

    if mode == 'fact':
        model = create_anki_model()
        for word_info in word_infos:
            create_cards(word_info, model, deck, AUDIO_DIR)

    elif mode == 'sentence':
        model = create_sentence_model()
        for word_info in word_infos:
            create_sentence_cards(word_info, model, deck, AUDIO_DIR)

    elif mode == 'cloze':
        model = create_cloze_model()
        for word_info in word_infos:
            if not word_info.get('cloze_sentences'):
                print(f'  Warning: no cloze_sentences for "{word_info["canonical"]}", skipping.')
                continue
            create_cloze_cards(word_info, model, deck, AUDIO_DIR)

    export_deck(deck, output_file, AUDIO_DIR)
    print(f'Built {len(deck.notes)} cards → {output_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a German Anki deck.')
    parser.add_argument('--mode', choices=['fact', 'sentence', 'cloze'], default='fact')
    parser.add_argument('--deck-name', default=None)
    parser.add_argument('--output', default=None)
    parser.add_argument('--words-file', default=None)
    args = parser.parse_args()

    deck_name = args.deck_name or {
        'fact': 'German Vocabulary',
        'sentence': 'German Sentences',
        'cloze': 'German Cloze',
    }[args.mode]

    build_deck(
        mode=args.mode,
        deck_name=deck_name,
        output_file=args.output,
        words_file=args.words_file,
    )
