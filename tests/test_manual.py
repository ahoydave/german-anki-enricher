"""Manual tests — make real API calls to verify end-to-end behaviour.

Run with:
    uv run pytest tests/test_manual.py -m manual -s

Requires ANTHROPIC_API_KEY in environment or .env file.
"""

import os

import anthropic
import genanki
import pytest
from dotenv import load_dotenv

from german_anki_generator import (
    create_anki_model,
    create_sentence_model,
    create_cloze_model,
    create_cards,
    create_sentence_cards,
    create_cloze_cards,
    get_word_info,
    get_cloze_data,
)

load_dotenv()


@pytest.fixture(scope='module')
def client():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('ANTHROPIC_API_KEY not set')
    return anthropic.Anthropic(api_key=api_key)


def make_deck():
    return genanki.Deck(11111, 'Manual Test Deck')


@pytest.mark.manual
def test_noun_hund(client, tmp_path):
    info = get_word_info('Hund', client)
    assert info['word_type'] == 'noun'
    assert info['canonical'] == 'Hund'
    assert info['article'] in ('der', 'die', 'das')
    assert info['plural']
    assert len(info['sentences']) >= 1
    print(f"\nHund → {info['english']}, {info['article']} {info['canonical']}, Pl: {info['plural']}")
    print(f"Sentences: {[s['german'] for s in info['sentences']]}")


@pytest.mark.manual
def test_verb_canonical_form_from_participle(client, tmp_path):
    """'gedreht' (past participle) should be resolved to 'drehen' (infinitive)."""
    info = get_word_info('gedreht', client)
    assert info['canonical'] == 'drehen'
    assert info['word_type'] == 'verb'
    assert info['perfekt']
    assert info['praeteritum']
    print(f"\ngedreht → canonical: {info['canonical']}, perfekt: {info['perfekt']}, praeteritum: {info['praeteritum']}")
    print(f"Case: {info.get('verb_case')}, Prepositions: {info.get('prepositions')}")


@pytest.mark.manual
def test_reflexive_verb_sich_freuen(client, tmp_path):
    info = get_word_info('sich freuen', client)
    assert info['word_type'] == 'verb'
    assert info['is_reflexive'] is True
    assert info['also_non_reflexive'] is False
    assert 'sich' in info['canonical']
    print(f"\nsich freuen → {info['english']}, prepositions: {info.get('prepositions')}")


@pytest.mark.manual
def test_dual_reflexive_verb_vorstellen(client, tmp_path):
    """vorstellen can be reflexive (introduce oneself) or not (introduce someone)."""
    info = get_word_info('vorstellen', client)
    assert info['word_type'] == 'verb'
    if info.get('also_non_reflexive'):
        assert info['non_reflexive_canonical']
        assert info['non_reflexive_sentences']
        print(f"\nDual reflexive detected:")
        print(f"  Reflexive: {info['canonical']} → {info['english']}")
        print(f"  Non-reflexive: {info['non_reflexive_canonical']} → {info['non_reflexive_english']}")
    else:
        print(f"\nSingle form: {info['canonical']} → {info['english']}")


@pytest.mark.manual
def test_adjective_schoen(client, tmp_path):
    info = get_word_info('schön', client)
    assert info['word_type'] == 'adjective'
    assert info['adjective_forms']
    print(f"\nschön → {info['english']}, forms: {info['adjective_forms']}")


@pytest.mark.manual
def test_phrase_angst_haben(client, tmp_path):
    info = get_word_info('Angst haben', client)
    assert info['word_type'] == 'phrase'
    assert info['sentences']
    print(f"\nAngst haben → {info['english']}")
    print(f"Notes: {info.get('notes')}")


@pytest.mark.manual
def test_english_input_resolved(client, tmp_path):
    """English input should be converted to the German equivalent."""
    info = get_word_info('dog', client)
    assert info['word_type'] == 'noun'
    assert info['canonical'] == 'Hund'
    print(f"\n'dog' → {info['canonical']}")


@pytest.mark.manual
def test_full_card_creation_noun(client, tmp_path):
    """End-to-end: create a card and verify Anki note structure."""
    model = create_anki_model()
    deck = make_deck()
    info = get_word_info('Katze', client)
    audio_files, canonicals = create_cards(info, model, deck, str(tmp_path))
    assert len(deck.notes) >= 1
    assert canonicals[0] == info['canonical']
    note = deck.notes[0]
    assert note.fields[0]  # GermanFront
    assert note.fields[2]  # English
    print(f"\nKatze card fields:")
    for i, f in enumerate(note.fields):
        if f:
            print(f"  [{i}] {f[:80]}")


@pytest.mark.manual
def test_sentence_cards_verb(client, tmp_path):
    """Sentence mode: English sentence → German sentence card for a verb."""
    info = get_word_info('kaufen', client)
    model = create_sentence_model()
    deck = make_deck()
    create_sentence_cards(info, model, deck, str(tmp_path))
    assert len(deck.notes) >= 1
    note = deck.notes[0]
    english, german, audio, hint = note.fields
    assert english  # front is English sentence
    assert german   # back is German sentence
    assert hint == info['canonical']
    assert '[sound:' in audio
    print(f"\nkaufen sentence cards ({len(deck.notes)} cards):")
    for n in deck.notes:
        print(f"  EN: {n.fields[0]}")
        print(f"  DE: {n.fields[1]}")


@pytest.mark.manual
def test_cloze_data_verb(client, tmp_path):
    """Cloze mode: verify cloze sentences generated for a verb."""
    info = get_word_info('kaufen', client)
    cloze = get_cloze_data(info, client)
    assert 'cloze_text' in cloze
    text = cloze['cloze_text']
    assert '{{c1::' in text
    assert '{{c2::' in text
    assert '{{c3::' in text
    print(f"\nkaufen cloze text:\n{text}")


@pytest.mark.manual
def test_cloze_cards_verb(client, tmp_path):
    """End-to-end: cloze card creation for a verb."""
    info = get_word_info('kaufen', client)
    cloze = get_cloze_data(info, client)
    info = {**info, **cloze}
    model = create_cloze_model()
    deck = make_deck()
    create_cloze_cards(info, model, deck, str(tmp_path))
    assert len(deck.notes) >= 3  # one note per sentence
    for note in deck.notes:
        assert '{{c' in note.fields[0]  # each note has exactly its own blank
        assert note.fields[2] == info['canonical']
    print(f"\nkaufen cloze notes ({len(deck.notes)}):")
    for n in deck.notes:
        print(f"  {n.fields[0]}")


@pytest.mark.manual
def test_cloze_data_noun(client, tmp_path):
    """Cloze mode: verify noun gets article + noun as separate blanks."""
    info = get_word_info('Hund', client)
    cloze = get_cloze_data(info, client)
    text = cloze['cloze_text']
    print(f"\nHund cloze text:\n{text}")
    # Should have at least c1 and c2 (article + noun)
    assert '{{c1::' in text
    assert '{{c2::' in text
