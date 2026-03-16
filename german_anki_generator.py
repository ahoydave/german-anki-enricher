import hashlib
import json
import os
import re
import sys

import genanki
import gtts

CARD_DATA_DIR = 'card_data'

ANKI_MODEL_ID = 1738291047  # Fixed — Anki uses this to identify the model across imports

_BACK_GRAMMAR_TAIL = (
    '{{#Perfekt}}<div class="grammar">'
    '<b>Perfekt:</b> {{Perfekt}} &nbsp;·&nbsp; <b>Präteritum:</b> {{Praeteritum}}'
    '{{#VerbCase}}<br><b>Case:</b> {{VerbCase}}{{/VerbCase}}'
    '{{#Prepositions}}<br><b>Prepositions:</b> {{Prepositions}}{{/Prepositions}}'
    '</div>{{/Perfekt}}'
    '{{#AdjectiveForms}}<div class="grammar"><b>Forms:</b> {{AdjectiveForms}}</div>{{/AdjectiveForms}}'
    '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}'
    '{{#Examples}}<div class="examples">{{Examples}}</div>{{/Examples}}'
)

_DE_EN_AFMT = (
    '{{FrontSide}}<hr id="answer">'
    '<div class="english">{{English}}</div>'
    '{{#Article}}<div class="grammar-header">{{Article}} {{GermanFront}}'
    '{{#Plural}} &nbsp;·&nbsp; Plural: <i>{{Plural}}</i>{{/Plural}}'
    '</div>{{/Article}}'
) + _BACK_GRAMMAR_TAIL

_EN_DE_AFMT = (
    '{{FrontSide}}<hr id="answer">'
    '<div class="german">{{#Article}}{{Article}} {{/Article}}{{GermanFront}}</div>'
    '{{WordAudio}}'
    '{{#Article}}{{#Plural}}<div class="grammar-header">Plural: <i>{{Plural}}</i></div>{{/Plural}}{{/Article}}'
) + _BACK_GRAMMAR_TAIL

_CSS = '''.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
.german {
    font-weight: bold;
    color: #3399ff;
    font-size: 24px;
}
.english { font-style: italic; }
.grammar-header { color: #555; margin: 8px 0; }
.grammar {
    text-align: left;
    display: inline-block;
    margin: 10px auto;
    padding: 8px 16px;
    background: #f5f5f5;
    border-radius: 4px;
}
.notes { color: #888; font-size: 16px; margin: 8px 0; }
.examples { text-align: left; margin: 15px; }'''


def create_anki_model():
    return genanki.Model(
        ANKI_MODEL_ID,
        'German Vocabulary',
        fields=[
            {'name': 'GermanFront'},
            {'name': 'WordAudio'},
            {'name': 'English'},
            {'name': 'Article'},
            {'name': 'Plural'},
            {'name': 'Perfekt'},
            {'name': 'Praeteritum'},
            {'name': 'VerbCase'},
            {'name': 'Prepositions'},
            {'name': 'AdjectiveForms'},
            {'name': 'Notes'},
            {'name': 'Examples'},
        ],
        templates=[
            {
                'name': 'German -> English',
                'qfmt': '<div class="german">{{GermanFront}}</div>\n{{WordAudio}}',
                'afmt': _DE_EN_AFMT,
            },
            {
                'name': 'English -> German',
                'qfmt': '<div class="english">{{English}}</div>',
                'afmt': _EN_DE_AFMT,
            },
        ],
        css=_CSS,
    )



def generate_audio(text, filename):
    if not os.path.exists(filename):
        tts = gtts.gTTS(text, lang='de')
        tts.save(filename)
    return filename


def _safe_filename(canonical):
    return re.sub(r'[^a-z0-9äöüß]', '_', canonical.lower()) + '.json'


def save_word_info(word_info, card_data_dir=CARD_DATA_DIR):
    os.makedirs(card_data_dir, exist_ok=True)
    path = os.path.join(card_data_dir, _safe_filename(word_info['canonical']))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(word_info, f, ensure_ascii=False, indent=2)


def load_all_word_infos(card_data_dir=CARD_DATA_DIR):
    if not os.path.exists(card_data_dir):
        return []
    infos = []
    for filename in sorted(os.listdir(card_data_dir)):
        if filename.endswith('.json'):
            with open(os.path.join(card_data_dir, filename), encoding='utf-8') as f:
                infos.append(json.load(f))
    return infos


def _build_note(canonical, english, word_info, model, audio_dir, sentences_key='sentences'):
    """Build a single genanki.Note with word audio + example audio. Returns (note, audio_files)."""
    word_type = word_info['word_type']

    audio_text = canonical

    safe_name = canonical.lower().replace(' ', '_')
    word_audio_path = os.path.join(audio_dir, f'{safe_name}_word.mp3')
    generate_audio(audio_text, word_audio_path)
    audio_files = [word_audio_path]

    word_audio_tag = f'[sound:{os.path.basename(word_audio_path)}]'

    sentences = word_info.get(sentences_key, [])
    formatted_examples = []
    for i, sentence in enumerate(sentences, 1):
        ex_path = os.path.join(audio_dir, f'{safe_name}_ex{i}.mp3')
        generate_audio(sentence['german'], ex_path)
        audio_files.append(ex_path)
        audio_tag = f'[sound:{os.path.basename(ex_path)}]'
        formatted_examples.append(
            f'<b>{i}. {sentence["german"]}</b> {audio_tag}<br><i>{sentence["english"]}</i>'
        )
    examples_html = '<br><br>'.join(formatted_examples)

    prepositions = word_info.get('prepositions') or []
    prepositions_str = ' · '.join(prepositions) if isinstance(prepositions, list) else str(prepositions)

    verb_case = word_info.get('verb_case') or ''
    if isinstance(verb_case, str) and verb_case.lower() == 'null':
        verb_case = ''

    note = genanki.Note(
        model=model,
        guid=genanki.guid_for(canonical),
        fields=[
            canonical,
            word_audio_tag,
            english,
            word_info.get('article', '') if word_type == 'noun' else '',
            word_info.get('plural', '') if word_type == 'noun' else '',
            word_info.get('perfekt', '') if word_type == 'verb' else '',
            word_info.get('praeteritum', '') if word_type == 'verb' else '',
            verb_case if word_type == 'verb' else '',
            prepositions_str if word_type == 'verb' else '',
            word_info.get('adjective_forms', '') if word_type in ('adjective', 'adverb') else '',
            word_info.get('notes', ''),
            examples_html,
        ],
    )
    return note, audio_files


def create_cards(word_info, model, deck, audio_dir):
    """Create 1 or 2 notes from word_info (2 for dual reflexive/non-reflexive verbs).

    Returns (audio_files, canonicals).
    """
    os.makedirs(audio_dir, exist_ok=True)

    all_audio = []
    canonicals = []

    note, audio_files = _build_note(
        word_info['canonical'], word_info['english'], word_info, model, audio_dir
    )
    deck.add_note(note)
    all_audio.extend(audio_files)
    canonicals.append(word_info['canonical'])

    nr_canonical = word_info.get('non_reflexive_canonical', '')
    if word_info.get('also_non_reflexive') and nr_canonical and nr_canonical != word_info['canonical']:
        nr_english = word_info['non_reflexive_english']
        nr_info = {**word_info, 'canonical': nr_canonical, 'is_reflexive': False}
        nr_note, nr_audio = _build_note(
            nr_canonical, nr_english, nr_info, model, audio_dir,
            sentences_key='non_reflexive_sentences'
        )
        deck.add_note(nr_note)
        all_audio.extend(nr_audio)
        canonicals.append(nr_canonical)

    return all_audio, canonicals


def read_words_from_file(filename):
    words = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith('#'):
                    words.append(word)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)
    return words


def export_deck(deck, output_filename, audio_dir):
    media_files = []
    if os.path.exists(audio_dir):
        for file in os.listdir(audio_dir):
            if file.endswith('.mp3'):
                media_files.append(os.path.join(audio_dir, file))

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_filename)
    print(f"Deck exported as {output_filename}")


# ---------------------------------------------------------------------------
# Sentence card mode
# ---------------------------------------------------------------------------

SENTENCE_MODEL_ID = 1738291048

_SENTENCE_CSS = _CSS + '\n.hint { color: #999; font-size: 14px; margin-top: 10px; }'


def create_sentence_model():
    return genanki.Model(
        SENTENCE_MODEL_ID,
        'German Sentence',
        fields=[
            {'name': 'English'},
            {'name': 'German'},
            {'name': 'GermanAudio'},
            {'name': 'Hint'},
        ],
        templates=[{
            'name': 'Sentence',
            'qfmt': '<div class="english">{{English}}</div>',
            'afmt': (
                '{{FrontSide}}<hr id="answer">'
                '<div class="german">{{German}}</div>'
                '{{GermanAudio}}'
                '<div class="hint">{{Hint}}</div>'
            ),
        }],
        css=_SENTENCE_CSS,
    )


def create_sentence_cards(word_info, model, deck, audio_dir):
    """One card per example sentence: English front → German back + audio."""
    os.makedirs(audio_dir, exist_ok=True)
    canonical = word_info['canonical']
    all_audio = []

    def _add(sentence, hint):
        german = sentence['german']
        english = sentence['english']
        h = hashlib.md5(german.encode()).hexdigest()[:8]
        audio_path = os.path.join(audio_dir, f'sent_{h}.mp3')
        generate_audio(german, audio_path)
        all_audio.append(audio_path)
        note = genanki.Note(
            model=model,
            guid=genanki.guid_for(f'sent:{german}'),
            fields=[english, german, f'[sound:{os.path.basename(audio_path)}]', hint],
        )
        deck.add_note(note)

    for sentence in word_info.get('sentences', []):
        _add(sentence, canonical)

    nr_canonical = word_info.get('non_reflexive_canonical', '')
    if word_info.get('also_non_reflexive') and nr_canonical and nr_canonical != canonical:
        for sentence in word_info.get('non_reflexive_sentences', []):
            _add(sentence, nr_canonical)

    return all_audio


# ---------------------------------------------------------------------------
# Cloze card mode
# ---------------------------------------------------------------------------

CLOZE_MODEL_ID_CUSTOM = 1738291049


def create_cloze_model():
    return genanki.Model(
        CLOZE_MODEL_ID_CUSTOM,
        'German Cloze',
        fields=[
            {'name': 'Text'},
            {'name': 'Audio'},
            {'name': 'Hint'},
            {'name': 'English'},
        ],
        templates=[{
            'name': 'Cloze',
            'qfmt': '{{cloze:Text}}{{#Hint}}<div class="hint">{{Hint}}</div>{{/Hint}}',
            'afmt': (
                '{{cloze:Text}}<br>{{Audio}}'
                '{{#Hint}}<div class="hint">{{Hint}}</div>{{/Hint}}'
                '<div class="english">{{English}}</div>'
            ),
        }],
        model_type=genanki.Model.CLOZE,
        css=_SENTENCE_CSS,
    )


def _strip_cloze_markers(text):
    """'Er {{c1::dreht}} das Rad.' → 'Er dreht das Rad.'"""
    return re.sub(r'\{\{c\d+::(.*?)\}\}', r'\1', text)


def create_cloze_cards(word_info, model, deck, audio_dir):
    """One Anki cloze note per sentence, each with its own English hint."""
    os.makedirs(audio_dir, exist_ok=True)
    all_audio = []

    def _add_sentences(sentences, word_hint):
        for item in sentences:
            text = item['text']
            hint = item.get('hint', '')
            english = item.get('english', '')
            clean = _strip_cloze_markers(text)
            h = hashlib.md5(clean.encode()).hexdigest()[:8]
            audio_path = os.path.join(audio_dir, f'cloze_{h}.mp3')
            generate_audio(clean, audio_path)
            all_audio.append(audio_path)
            note = genanki.Note(
                model=model,
                guid=genanki.guid_for(f'cloze:{word_hint}:{clean}'),
                fields=[text, f'[sound:{os.path.basename(audio_path)}]', hint, english],
            )
            deck.add_note(note)

    sentences = word_info.get('cloze_sentences', [])
    if sentences:
        _add_sentences(sentences, word_info['canonical'])

    nr_canonical = word_info.get('non_reflexive_canonical', '')
    nr_sentences = word_info.get('nr_cloze_sentences', [])
    if word_info.get('also_non_reflexive') and nr_canonical and nr_canonical != word_info['canonical'] and nr_sentences:
        _add_sentences(nr_sentences, nr_canonical)

    return all_audio


# ---------------------------------------------------------------------------
# Load a specific subset of words
# ---------------------------------------------------------------------------

def load_word_infos_for(words_file, card_data_dir=CARD_DATA_DIR):
    """Load word_info dicts for the canonicals listed in words_file."""
    with open(words_file, encoding='utf-8') as f:
        canonicals = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    infos = []
    for canonical in canonicals:
        path = os.path.join(card_data_dir, _safe_filename(canonical))
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                infos.append(json.load(f))
        else:
            print(f'Warning: no data for "{canonical}", skipping.')
    return infos
