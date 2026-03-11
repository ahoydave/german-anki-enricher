import hashlib
import json
import os
import re
import sys

import anthropic
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


def get_word_info(word, client):
    """Call the Claude API once to get all card data. Returns a dict."""
    prompt = f"""Analyze the input '{word}' (may be German or English, may be misspelled or in a non-canonical form) and return a JSON object.

Steps:
1. Determine the word type: noun, verb, adjective, adverb, phrase, conjunction, preposition, or other
2. Find the canonical German form:
   - Verbs: use the infinitive ("gedreht" → "drehen", "lief" → "laufen")
   - Verbs that REQUIRE "sich": include it ("sich freuen", "sich vorstellen")
   - Nouns: nominative singular, no article, correctly capitalised ("Hunde" → "Hund")
   - Phrases: natural base form
   - Others: base form
3. If the input appears to be English or is misspelled, find the intended German word

Return this exact JSON structure (omit fields not relevant to the word type, but always include the core fields):
{{
  "canonical": "base German form",
  "word_type": "noun|verb|adjective|adverb|phrase|conjunction|preposition|other",
  "english": "primary meaning / secondary meaning (include all meanings worth knowing, separated by /)",
  "is_reflexive": false,
  "also_non_reflexive": false,

  "article": "der|die|das",
  "plural": "plural form",

  "perfekt": "hat/ist + past participle (e.g. hat gedreht)",
  "praeteritum": "first person singular (e.g. drehte)",
  "verb_case": "akkusativ|dativ|genitiv|null",
  "prepositions": ["verb + preposition + case (e.g. drehen an + dativ)"],

  "adjective_forms": "positive, comparative, superlative (e.g. schön, schöner, am schönsten)",

  "notes": "",
  "sentences": [
    {{"german": "example sentence", "english": "translation", "purpose": "present|perfekt|preposition|meaning"}}
  ],

  "non_reflexive_canonical": "",
  "non_reflexive_english": "",
  "non_reflexive_sentences": [
    {{"german": "example sentence", "english": "translation", "purpose": "present|perfekt"}}
  ]
}}

Sentence count rules:
- Nouns: 1–3 sentences. One per important meaning; if one meaning, show different contexts (e.g. singular and plural).
- Verbs: usually 3 (present tense, Perfekt, most common preposition). If no common preposition, 2 sentences.
- Adjectives/Adverbs: 1–2 sentences showing the most important usage.
- Phrases/conjunctions/other: 1 sentence.
- Max 3 sentences for any word. All sentences at B1 level.

Set "also_non_reflexive": true ONLY if the verb also has a clearly distinct common meaning used WITHOUT "sich".
When true, populate non_reflexive_canonical, non_reflexive_english, and non_reflexive_sentences (2 sentences: present + Perfekt)."""

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        temperature=0.3,
        system='You are a German language expert. Return ONLY valid JSON, no markdown, no explanation.',
        messages=[{'role': 'user', 'content': prompt}],
    )
    return json.loads(response.content[0].text)


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
        ],
        templates=[{
            'name': 'Cloze',
            'qfmt': '{{cloze:Text}}<div class="hint">{{Hint}}</div>',
            'afmt': '{{cloze:Text}}<br>{{Audio}}<div class="hint">{{Hint}}</div>',
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
            hint = item.get('hint', word_hint)
            clean = _strip_cloze_markers(text)
            h = hashlib.md5(clean.encode()).hexdigest()[:8]
            audio_path = os.path.join(audio_dir, f'cloze_{h}.mp3')
            generate_audio(clean, audio_path)
            all_audio.append(audio_path)
            note = genanki.Note(
                model=model,
                guid=genanki.guid_for(f'cloze:{word_hint}:{clean}'),
                fields=[text, f'[sound:{os.path.basename(audio_path)}]', hint],
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


def get_cloze_data(word_info, client):
    """Call the API to generate cloze sentences. Returns dict with cloze_text (and nr_cloze_text if dual reflexive)."""
    canonical = word_info['canonical']
    word_type = word_info['word_type']
    nr_canonical = word_info.get('non_reflexive_canonical', '')
    is_dual = word_info.get('also_non_reflexive') and nr_canonical and nr_canonical != canonical

    nr_field = ''
    nr_instruction = ''
    if is_dual:
        nr_field = f',\n  "nr_cloze_sentences": [list of sentence objects for the non-reflexive form "{nr_canonical}", same rules]'
        nr_instruction = f'\nAlso generate cloze sentences for the non-reflexive form "{nr_canonical}" using the non_reflexive_* fields.'

    prompt = (
        f'Generate cloze deletion sentences for the German word "{canonical}" ({word_type}).\n\n'
        f'Word data:\n{json.dumps(word_info, ensure_ascii=False, indent=2)}\n\n'
        'Rules:\n'
        '- Wrap each TARGET ANSWER in {{c1::answer}}, {{c2::answer}}, etc. (each sentence gets its own cN starting from c1 — reset numbering per sentence)\n'
        '- ALL other vocabulary must be B1 level or below — simple, common words only\n'
        '- Sentences must be natural, correct German\n'
        '- IMPORTANT: Do NOT place a gender-revealing article (der/die/das/ein/eine etc.) immediately before a blanked noun — restructure the sentence so the article is not adjacent to the blank (e.g. use a preposition, put the noun at the end, use a different sentence structure)\n'
        '- Each sentence object must include a "hint" in English describing exactly what the blank is (see examples below)\n'
        + nr_instruction + '\n\n'
        'Hint examples:\n'
        '- verb present (er form): "turns (he, present)"\n'
        '- verb Perfekt participle: "turned (Perfekt)"\n'
        '- verb Präteritum: "turned (Präteritum)"\n'
        '- verb preposition: "on/an (preposition used with this verb)"\n'
        '- noun article: "the (article — der/die/das?)"\n'
        '- noun itself: "wallet (the word for wallet)"\n'
        '- noun plural: "wallets (plural form)"\n'
        '- adjective: "quiet (predicative form)"\n\n'
        'Required sentences by word type:\n'
        '- verb: 3-4 sentences:\n'
        '  (1) present tense — blank the conjugated form (er/sie form)\n'
        '  (2) Perfekt — blank the past participle\n'
        '  (3) Präteritum — blank the präteritum form\n'
        '  (4) if the verb has a common preposition, one sentence blanking the preposition\n'
        '- noun: 2 sentences:\n'
        '  (1) singular — TWO separate blanks: {{c1::article}} for the article and {{c2::noun}} for the noun; ensure no other gender-revealing word is adjacent to either blank\n'
        '  (2) plural — blank the plural form\n'
        '- adjective/adverb: 1-2 sentences with the target word blanked\n'
        '- phrase/conjunction/preposition/other: 1-2 sentences with the key word(s) blanked\n\n'
        'Return JSON:\n'
        '{\n'
        '  "cloze_sentences": [\n'
        '    {"text": "Er {{c1::dreht}} das Steuer.", "hint": "turns (he, present)"},\n'
        '    ...\n'
        '  ]'
        + nr_field + '\n}'
    )

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1000,
        temperature=0.3,
        system='You are a German language expert. Return ONLY valid JSON, no markdown, no code fences.',
        messages=[{'role': 'user', 'content': prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```.*$', '', text.strip(), flags=re.DOTALL)
    # Extract the first complete JSON object in case of trailing text
    start = text.find('{')
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    text = text[start:i + 1]
                    break
    return json.loads(text)


def ensure_cloze_data(word_info, client, card_data_dir=CARD_DATA_DIR):
    """Generate and cache cloze data if not already present. Returns updated word_info."""
    if 'cloze_sentences' in word_info:
        return word_info
    print(f'  Generating cloze data for {word_info["canonical"]}...')
    cloze_data = get_cloze_data(word_info, client)
    word_info = {**word_info, **cloze_data}
    save_word_info(word_info, card_data_dir)
    return word_info


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
