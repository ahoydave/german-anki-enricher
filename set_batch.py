"""Write the next N genuinely remaining words to new_words.txt."""
import sys

BATCH_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 40
STRIP_PREFIXES = ('der ', 'die ', 'das ', 'sich ', 'ein ', 'eine ')


def likely_canonical(word):
    """Best-effort canonical form for pre-filtering (strips common articles)."""
    lower = word.lower()
    for prefix in STRIP_PREFIXES:
        if lower.startswith(prefix):
            return word[len(prefix):]
    return word


with open('new_words_full.txt') as f:
    all_words = [l.strip() for l in f if l.strip() and not l.startswith('#')]

with open('added_words.txt') as f:
    added = {l.strip() for l in f if l.strip() and not l.startswith('#')}

remaining = [
    w for w in all_words
    if w not in added and likely_canonical(w) not in added
]
batch = remaining[:BATCH_SIZE]

with open('new_words.txt', 'w') as f:
    f.write(f'# Next batch ({len(batch)} of {len(remaining)} remaining)\n')
    for w in batch:
        f.write(f'{w}\n')

print(f'Written {len(batch)} words. ~{len(remaining) - len(batch)} will remain after this batch.')
