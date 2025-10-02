import json
import os
import random
import sys

import anthropic
import genanki
import gtts


def create_anki_model():
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
        timeout=30.0,
        system="""You are a helpful German language assistant. You respond only in valid JSON without any additional formatting. Provide accurate grammatical information and natural example sentences.""",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = json.loads(response.content[0].text)
    return result


def generate_audio(text, filename):
    tts = gtts.gTTS(text, lang='de')
    tts.save(filename)
    return filename




def create_card(word, api_key, model, deck, audio_dir):
    os.makedirs(audio_dir, exist_ok=True)
    word_info = get_word_info_and_examples(word, api_key)
    
    german = word_info['german']
    english = word_info['english']
    word_type = word_info['word_type']
    grammar = word_info['grammar']
    examples = word_info['sentences']
    
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
    
    all_notes = []
    if grammar_notes:
        all_notes.extend(grammar_notes)
    notes_text = " | ".join(all_notes)
    
    formatted_examples = []
    audio_files = []
    
    for i, example in enumerate(examples, 1):
        german_sentence = example['example']
        english_translation = example['translation']
        
        audio_filename = os.path.join(audio_dir, f"{german.lower().replace(' ', '_')}_ex{i}.mp3")
        generate_audio(german_sentence, audio_filename)
        audio_files.append(audio_filename)
        
        audio_tag = f'[sound:{os.path.basename(audio_filename)}]'
        formatted_example = f"""<b>{i}. {german_sentence}</b> {audio_tag}<br>
        <i>{english_translation}</i>"""
        
        formatted_examples.append(formatted_example)
    
    all_examples = "<br><br>".join(formatted_examples)
    
    note = genanki.Note(
        model=model,
        fields=[
            german,
            english,
            all_examples,
            notes_text
        ]
    )
    
    deck.add_note(note)
    
    return audio_files, word_info


def read_words_from_file(filename):
    words = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
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