#!/usr/bin/env python3
import os
import sys

import anthropic
from dotenv import load_dotenv

from german_anki_generator import (
    get_word_info,
    read_words_from_file,
    save_word_info,
)
from build_deck import build_deck


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
    new_words_file = 'new_words.txt'
    added_words_file = 'added_words.txt'

    if not os.path.exists(new_words_file):
        print(f'Error: {new_words_file} not found.')
        print(f'Please create {new_words_file} with your German/English words (one per line).')
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print('Error: ANTHROPIC_API_KEY not found in environment variables.')
        print('Please create a .env file with: ANTHROPIC_API_KEY=your-api-key')
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f'Reading words from {new_words_file}...')
    words_to_process = read_words_from_file(new_words_file)
    print(f'Found {len(words_to_process)} words to process.')

    if not words_to_process:
        print(f'Error: {new_words_file} is empty or contains no valid words.')
        sys.exit(1)

    existing_words = load_existing_words(added_words_file)
    print(f'Found {len(existing_words)} existing words in {added_words_file}')

    new_canonicals = []

    for i, word in enumerate(words_to_process, 1):
        print(f'\nProcessing {i}/{len(words_to_process)}: {word}')

        try:
            print('  Getting word info...')
            word_info = get_word_info(word, client)
            canonical = word_info['canonical']
            print(f'  Got: {canonical} → {word_info["english"]} ({word_info["word_type"]})')

            if canonical in existing_words:
                print('  Skipped: already exists')
                continue

            save_word_info(word_info)

            canonicals = [canonical]
            if word_info.get('also_non_reflexive') and word_info.get('non_reflexive_canonical', '') != canonical:
                canonicals.append(word_info['non_reflexive_canonical'])

            for c in canonicals:
                new_canonicals.append(c)
                existing_words.add(c)

            print(f'  Saved: {canonicals}')

        except Exception as e:
            print(f'  Failed: {e}')
            if new_canonicals:
                print(f'Processed {i - 1} words before the error. Rebuilding deck with what we have...')
            else:
                print('No words processed before the error. Nothing to export.')
            break

    if new_canonicals:
        print(f'\nUpdating {added_words_file}...')
        with open(added_words_file, 'a', encoding='utf-8') as f:
            for c in new_canonicals:
                f.write(f'{c}\n')

        print('\nRebuilding deck...')
        build_deck()

    print(f'\nSummary:')
    print(f'  Total words processed: {len(words_to_process)}')
    if new_canonicals:
        print(f'  New words added: {len(new_canonicals)}')
    else:
        print('  No new words added')


if __name__ == '__main__':
    main()
