#!/usr/bin/env python3
"""Save a single word_info JSON to card_data/ and rebuild the fact deck.

Usage:
  .venv/bin/python add_card.py '{"canonical": "drehen", ...}'
  echo '{"canonical": ...}' | .venv/bin/python add_card.py
  .venv/bin/python add_card.py '...' --no-rebuild
"""
import argparse
import json
import os
import sys

from german_anki_generator import save_word_info

ADDED_WORDS_FILE = 'added_words.txt'
VALID_WORD_TYPES = {'noun', 'verb', 'adjective', 'adverb', 'phrase', 'conjunction', 'preposition', 'other'}


def load_existing_words():
    if not os.path.exists(ADDED_WORDS_FILE):
        return set()
    with open(ADDED_WORDS_FILE, encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip() and not line.startswith('#')}


def main():
    parser = argparse.ArgumentParser(description='Add a word card from JSON.')
    parser.add_argument('json', nargs='?', help='word_info JSON string')
    parser.add_argument('--no-rebuild', action='store_true', help='Skip deck rebuild after saving')
    args = parser.parse_args()

    if args.json:
        text = args.json
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    try:
        word_info = json.loads(text.strip())
    except json.JSONDecodeError as e:
        print(f'Error: invalid JSON — {e}')
        sys.exit(1)

    for field in ('canonical', 'word_type', 'english'):
        if field not in word_info:
            print(f'Error: missing required field "{field}"')
            sys.exit(1)

    if word_info['word_type'] not in VALID_WORD_TYPES:
        print(f'Error: word_type must be one of {sorted(VALID_WORD_TYPES)}')
        sys.exit(1)

    canonical = word_info['canonical']
    existing = load_existing_words()

    if canonical in existing:
        print(f'Already exists: {canonical}')
        return

    save_word_info(word_info)

    canonicals = [canonical]
    nr_canonical = word_info.get('non_reflexive_canonical', '')
    if word_info.get('also_non_reflexive') and nr_canonical and nr_canonical != canonical:
        canonicals.append(nr_canonical)

    with open(ADDED_WORDS_FILE, 'a', encoding='utf-8') as f:
        for c in canonicals:
            if c not in existing:
                f.write(f'{c}\n')

    print(f'Saved: {" + ".join(canonicals)} ({word_info["word_type"]}) — {word_info["english"]}')

    if not args.no_rebuild:
        from build_deck import build_deck
        build_deck()


if __name__ == '__main__':
    main()
