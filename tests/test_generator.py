"""Automated tests using a mocked Anthropic client."""

import tempfile
from unittest.mock import patch

import genanki

from german_anki_generator import (
    ANKI_MODEL_ID,
    SENTENCE_MODEL_ID,
    CLOZE_MODEL_ID_CUSTOM,
    create_anki_model,
    create_sentence_model,
    create_cloze_model,
    create_cards,
    create_sentence_cards,
    create_cloze_cards,
    _strip_cloze_markers,
)

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

NOUN_INFO = {
    'canonical': 'Hund',
    'word_type': 'noun',
    'english': 'dog',
    'is_reflexive': False,
    'also_non_reflexive': False,
    'article': 'der',
    'plural': 'Hunde',
    'notes': '',
    'sentences': [
        {'german': 'Der Hund bellt laut.', 'english': 'The dog barks loudly.', 'purpose': 'meaning'},
        {'german': 'Die Hunde spielen im Park.', 'english': 'The dogs play in the park.', 'purpose': 'plural'},
    ],
}

VERB_INFO = {
    'canonical': 'drehen',
    'word_type': 'verb',
    'english': 'to turn / to rotate',
    'is_reflexive': False,
    'also_non_reflexive': False,
    'perfekt': 'hat gedreht',
    'praeteritum': 'drehte',
    'verb_case': 'akkusativ',
    'prepositions': ['drehen an + dativ'],
    'notes': '',
    'sentences': [
        {'german': 'Er dreht das Steuer.', 'english': 'He turns the wheel.', 'purpose': 'present'},
        {'german': 'Sie hat den Schlüssel gedreht.', 'english': 'She turned the key.', 'purpose': 'perfekt'},
        {'german': 'Er dreht an dem Knopf.', 'english': 'He turns the knob.', 'purpose': 'preposition'},
    ],
}

REFLEXIVE_ONLY_INFO = {
    'canonical': 'sich freuen',
    'word_type': 'verb',
    'english': 'to be happy / to look forward to',
    'is_reflexive': True,
    'also_non_reflexive': False,
    'perfekt': 'hat sich gefreut',
    'praeteritum': 'freute sich',
    'verb_case': 'null',
    'prepositions': ['freuen auf + akkusativ', 'freuen über + akkusativ'],
    'notes': '',
    'sentences': [
        {'german': 'Ich freue mich sehr.', 'english': 'I am very happy.', 'purpose': 'present'},
        {'german': 'Er hat sich gefreut.', 'english': 'He was happy.', 'purpose': 'perfekt'},
        {'german': 'Ich freue mich auf den Urlaub.', 'english': "I'm looking forward to the holiday.", 'purpose': 'preposition'},
    ],
}

DUAL_REFLEXIVE_INFO = {
    'canonical': 'sich vorstellen',
    'word_type': 'verb',
    'english': 'to introduce oneself / to imagine',
    'is_reflexive': True,
    'also_non_reflexive': True,
    'perfekt': 'hat sich vorgestellt',
    'praeteritum': 'stellte sich vor',
    'verb_case': 'akkusativ',
    'prepositions': [],
    'notes': '',
    'sentences': [
        {'german': 'Ich stelle mich vor.', 'english': 'I introduce myself.', 'purpose': 'present'},
        {'german': 'Er hat sich vorgestellt.', 'english': 'He introduced himself.', 'purpose': 'perfekt'},
    ],
    'non_reflexive_canonical': 'vorstellen',
    'non_reflexive_english': 'to introduce (someone)',
    'non_reflexive_sentences': [
        {'german': 'Er stellt seinen Freund vor.', 'english': 'He introduces his friend.', 'purpose': 'present'},
        {'german': 'Sie hat ihn vorgestellt.', 'english': 'She introduced him.', 'purpose': 'perfekt'},
    ],
}

ADJECTIVE_INFO = {
    'canonical': 'schön',
    'word_type': 'adjective',
    'english': 'beautiful / nice',
    'is_reflexive': False,
    'also_non_reflexive': False,
    'adjective_forms': 'schön, schöner, am schönsten',
    'notes': '',
    'sentences': [
        {'german': 'Das ist ein schöner Tag.', 'english': 'That is a beautiful day.', 'purpose': 'meaning'},
    ],
}

PHRASE_INFO = {
    'canonical': 'Angst haben',
    'word_type': 'phrase',
    'english': 'to be afraid / to have fear',
    'is_reflexive': False,
    'also_non_reflexive': False,
    'notes': 'Takes vor + dativ for the feared thing',
    'sentences': [
        {'german': 'Ich habe Angst vor Hunden.', 'english': 'I am afraid of dogs.', 'purpose': 'meaning'},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_deck():
    return genanki.Deck(99999, 'Test')


# Field index constants
F_GERMAN_FRONT = 0
F_WORD_AUDIO = 1
F_ENGLISH = 2
F_ARTICLE = 3
F_PLURAL = 4
F_PERFEKT = 5
F_PRAETERITUM = 6
F_VERB_CASE = 7
F_PREPOSITIONS = 8
F_ADJECTIVE_FORMS = 9
F_NOTES = 10
F_EXAMPLES = 11


# ---------------------------------------------------------------------------
# create_cards tests
# ---------------------------------------------------------------------------

class TestCreateCardsNoun:
    @patch('german_anki_generator.generate_audio')
    def test_creates_one_note(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            _, canonicals = create_cards(NOUN_INFO, model, deck, tmpdir)
        assert len(deck.notes) == 1
        assert canonicals == ['Hund']

    @patch('german_anki_generator.generate_audio')
    def test_noun_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(NOUN_INFO, model, deck, tmpdir)
        note = deck.notes[0]
        assert note.fields[F_GERMAN_FRONT] == 'Hund'
        assert note.fields[F_ENGLISH] == 'dog'
        assert note.fields[F_ARTICLE] == 'der'
        assert note.fields[F_PLURAL] == 'Hunde'
        assert note.fields[F_PERFEKT] == ''
        assert note.fields[F_PRAETERITUM] == ''

    @patch('german_anki_generator.generate_audio')
    def test_noun_word_audio_no_article(self, mock_audio):
        """Audio for a noun should say just 'Hund', not 'der Hund' — article would give away the answer."""
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(NOUN_INFO, model, deck, tmpdir)
        first_call_text = mock_audio.call_args_list[0].args[0]
        assert first_call_text == 'Hund'

    @patch('german_anki_generator.generate_audio')
    def test_noun_examples_in_html(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(NOUN_INFO, model, deck, tmpdir)
        examples = deck.notes[0].fields[F_EXAMPLES]
        assert 'Der Hund bellt laut.' in examples
        assert 'The dog barks loudly.' in examples

    @patch('german_anki_generator.generate_audio')
    def test_noun_audio_files_returned(self, mock_audio):
        """Should return 1 word audio + 2 example audios."""
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_files, _ = create_cards(NOUN_INFO, model, deck, tmpdir)
        assert len(audio_files) == 3  # 1 word + 2 examples


class TestCreateCardsVerb:
    @patch('german_anki_generator.generate_audio')
    def test_verb_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(VERB_INFO, model, deck, tmpdir)
        note = deck.notes[0]
        assert note.fields[F_GERMAN_FRONT] == 'drehen'
        assert note.fields[F_ENGLISH] == 'to turn / to rotate'
        assert note.fields[F_ARTICLE] == ''
        assert note.fields[F_PLURAL] == ''
        assert note.fields[F_PERFEKT] == 'hat gedreht'
        assert note.fields[F_PRAETERITUM] == 'drehte'
        assert note.fields[F_VERB_CASE] == 'akkusativ'
        assert note.fields[F_PREPOSITIONS] == 'drehen an + dativ'

    @patch('german_anki_generator.generate_audio')
    def test_verb_word_audio_no_article(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(VERB_INFO, model, deck, tmpdir)
        first_call_text = mock_audio.call_args_list[0].args[0]
        assert first_call_text == 'drehen'

    @patch('german_anki_generator.generate_audio')
    def test_verb_null_case_becomes_empty(self, mock_audio):
        info = {**REFLEXIVE_ONLY_INFO}
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(info, model, deck, tmpdir)
        assert deck.notes[0].fields[F_VERB_CASE] == ''

    @patch('german_anki_generator.generate_audio')
    def test_reflexive_verb_audio_uses_sich(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(REFLEXIVE_ONLY_INFO, model, deck, tmpdir)
        first_call_text = mock_audio.call_args_list[0].args[0]
        assert first_call_text == 'sich freuen'


class TestCreateCardsDualReflexive:
    @patch('german_anki_generator.generate_audio')
    def test_creates_two_notes(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            _, canonicals = create_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        assert len(deck.notes) == 2
        assert canonicals == ['sich vorstellen', 'vorstellen']

    @patch('german_anki_generator.generate_audio')
    def test_reflexive_note_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        note = deck.notes[0]
        assert note.fields[F_GERMAN_FRONT] == 'sich vorstellen'
        assert 'to introduce oneself' in note.fields[F_ENGLISH]

    @patch('german_anki_generator.generate_audio')
    def test_non_reflexive_note_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        note = deck.notes[1]
        assert note.fields[F_GERMAN_FRONT] == 'vorstellen'
        assert note.fields[F_ENGLISH] == 'to introduce (someone)'

    @patch('german_anki_generator.generate_audio')
    def test_non_reflexive_uses_its_own_sentences(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        nr_examples = deck.notes[1].fields[F_EXAMPLES]
        assert 'Er stellt seinen Freund vor.' in nr_examples
        assert 'Ich stelle mich vor.' not in nr_examples

    @patch('german_anki_generator.generate_audio')
    def test_distinct_guids(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        assert deck.notes[0].guid != deck.notes[1].guid

    @patch('german_anki_generator.generate_audio')
    def test_same_canonical_does_not_create_duplicate(self, mock_audio):
        """If API returns also_non_reflexive=True but non_reflexive_canonical == canonical, only one card."""
        bad_info = {**VERB_INFO, 'also_non_reflexive': True, 'non_reflexive_canonical': 'drehen',
                    'non_reflexive_english': 'to turn', 'non_reflexive_sentences': []}
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            _, canonicals = create_cards(bad_info, model, deck, tmpdir)
        assert len(deck.notes) == 1
        assert canonicals == ['drehen']


class TestCreateCardsAdjective:
    @patch('german_anki_generator.generate_audio')
    def test_adjective_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(ADJECTIVE_INFO, model, deck, tmpdir)
        note = deck.notes[0]
        assert note.fields[F_GERMAN_FRONT] == 'schön'
        assert note.fields[F_ADJECTIVE_FORMS] == 'schön, schöner, am schönsten'
        assert note.fields[F_ARTICLE] == ''
        assert note.fields[F_PERFEKT] == ''


class TestCreateCardsPhrase:
    @patch('german_anki_generator.generate_audio')
    def test_phrase_fields(self, mock_audio):
        model = create_anki_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(PHRASE_INFO, model, deck, tmpdir)
        note = deck.notes[0]
        assert note.fields[F_GERMAN_FRONT] == 'Angst haben'
        assert 'to be afraid' in note.fields[F_ENGLISH]
        assert 'vor + dativ' in note.fields[F_NOTES]
        assert note.fields[F_ARTICLE] == ''
        assert note.fields[F_PERFEKT] == ''


# ---------------------------------------------------------------------------
# Stable GUID tests
# ---------------------------------------------------------------------------

class TestStableGuids:
    @patch('german_anki_generator.generate_audio')
    def test_same_canonical_gives_same_guid(self, mock_audio):
        """Importing the same canonical twice should produce the same GUID (for Anki updates)."""
        model = create_anki_model()
        deck1 = make_deck()
        deck2 = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(NOUN_INFO, model, deck1, tmpdir)
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cards(NOUN_INFO, model, deck2, tmpdir)
        assert deck1.notes[0].guid == deck2.notes[0].guid


# ---------------------------------------------------------------------------
# Anki model
# ---------------------------------------------------------------------------

class TestAnkiModel:
    def test_model_id_is_fixed(self):
        m1 = create_anki_model()
        m2 = create_anki_model()
        assert m1.model_id == m2.model_id == ANKI_MODEL_ID

    def test_model_has_two_templates(self):
        model = create_anki_model()
        assert len(model.templates) == 2

    def test_field_names(self):
        model = create_anki_model()
        names = [f['name'] for f in model.fields]
        assert names[F_GERMAN_FRONT] == 'GermanFront'
        assert names[F_ARTICLE] == 'Article'
        assert names[F_PERFEKT] == 'Perfekt'


# ---------------------------------------------------------------------------
# Sentence card mode
# ---------------------------------------------------------------------------

class TestStripClozeMarkers:
    def test_single(self):
        assert _strip_cloze_markers('Er {{c1::dreht}} das Rad.') == 'Er dreht das Rad.'

    def test_multiple(self):
        assert _strip_cloze_markers('Das ist {{c1::ein}} {{c2::Hund}}.') == 'Das ist ein Hund.'

    def test_no_markers(self):
        assert _strip_cloze_markers('Er läuft schnell.') == 'Er läuft schnell.'


class TestCreateSentenceCards:
    @patch('german_anki_generator.generate_audio')
    def test_one_card_per_sentence_noun(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck, tmpdir)
        assert len(deck.notes) == 2  # NOUN_INFO has 2 sentences

    @patch('german_anki_generator.generate_audio')
    def test_front_is_english(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck, tmpdir)
        assert deck.notes[0].fields[0] == 'The dog barks loudly.'

    @patch('german_anki_generator.generate_audio')
    def test_back_contains_german(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck, tmpdir)
        assert deck.notes[0].fields[1] == 'Der Hund bellt laut.'

    @patch('german_anki_generator.generate_audio')
    def test_hint_is_canonical(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck, tmpdir)
        assert deck.notes[0].fields[3] == 'Hund'

    @patch('german_anki_generator.generate_audio')
    def test_dual_reflexive_uses_both_sentence_sets(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        # 2 reflexive sentences + 2 non-reflexive sentences
        assert len(deck.notes) == 4

    @patch('german_anki_generator.generate_audio')
    def test_dual_reflexive_hint_is_nr_canonical(self, mock_audio):
        model = create_sentence_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(DUAL_REFLEXIVE_INFO, model, deck, tmpdir)
        # Last 2 notes are for the non-reflexive form
        assert deck.notes[2].fields[3] == 'vorstellen'

    @patch('german_anki_generator.generate_audio')
    def test_stable_guid_same_sentence(self, mock_audio):
        model = create_sentence_model()
        deck1, deck2 = make_deck(), make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck1, tmpdir)
        with tempfile.TemporaryDirectory() as tmpdir:
            create_sentence_cards(NOUN_INFO, model, deck2, tmpdir)
        assert deck1.notes[0].guid == deck2.notes[0].guid

    @patch('german_anki_generator.generate_audio')
    def test_sentence_model_id_is_fixed(self, mock_audio):
        assert create_sentence_model().model_id == SENTENCE_MODEL_ID


# ---------------------------------------------------------------------------
# Cloze card mode
# ---------------------------------------------------------------------------

VERB_CLOZE_INFO = {
    **VERB_INFO,
    'cloze_sentences': [
        {'text': 'Er {{c1::dreht}} das Steuer.', 'hint': 'turns (he, present)'},
        {'text': 'Er hat das Steuer {{c2::gedreht}}.', 'hint': 'turned (Perfekt)'},
        {'text': 'Er {{c3::drehte}} das Steuer.', 'hint': 'turned (Präteritum)'},
    ],
}

DUAL_REFLEXIVE_CLOZE_INFO = {
    **DUAL_REFLEXIVE_INFO,
    'cloze_sentences': [
        {'text': 'Ich {{c1::stelle}} mich vor.', 'hint': 'introduces (I, present)'},
    ],
    'nr_cloze_sentences': [
        {'text': 'Er {{c1::stellt}} seinen Freund vor.', 'hint': 'introduces (he, present)'},
    ],
}

NOUN_CLOZE_INFO = {
    **NOUN_INFO,
    'cloze_sentences': [
        {'text': 'Ich sehe {{c1::einen}} {{c2::Hund}} im Park.', 'hint': 'article / the word for dog'},
        {'text': 'Auf der Straße laufen viele {{c1::Hunde}}.', 'hint': 'dogs (plural form)'},
    ],
}


class TestCreateClozeCards:
    @patch('german_anki_generator.generate_audio')
    def test_one_note_per_sentence(self, mock_audio):
        """VERB_CLOZE_INFO has 3 sentences → 3 notes (one card each)."""
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(VERB_CLOZE_INFO, model, deck, tmpdir)
        assert len(deck.notes) == 3

    @patch('german_anki_generator.generate_audio')
    def test_each_note_has_only_its_own_blank(self, mock_audio):
        """Each note should only contain the markers for its own sentence."""
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(VERB_CLOZE_INFO, model, deck, tmpdir)
        assert '{{c1::dreht}}' in deck.notes[0].fields[0]
        assert '{{c2::' not in deck.notes[0].fields[0]  # other sentences not present
        assert '{{c2::gedreht}}' in deck.notes[1].fields[0]
        assert '{{c3::drehte}}' in deck.notes[2].fields[0]

    @patch('german_anki_generator.generate_audio')
    def test_hint_field_is_sentence_hint(self, mock_audio):
        """Hint field should be the per-sentence English hint, not just the canonical."""
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(VERB_CLOZE_INFO, model, deck, tmpdir)
        assert deck.notes[0].fields[2] == 'turns (he, present)'
        assert deck.notes[1].fields[2] == 'turned (Perfekt)'
        assert deck.notes[2].fields[2] == 'turned (Präteritum)'

    @patch('german_anki_generator.generate_audio')
    def test_audio_uses_clean_text(self, mock_audio):
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(VERB_CLOZE_INFO, model, deck, tmpdir)
        audio_text = mock_audio.call_args_list[0].args[0]
        assert '{{' not in audio_text
        assert 'dreht' in audio_text

    @patch('german_anki_generator.generate_audio')
    def test_dual_reflexive_creates_notes_for_both_forms(self, mock_audio):
        """1 sentence for reflexive + 1 sentence for non-reflexive = 2 notes."""
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(DUAL_REFLEXIVE_CLOZE_INFO, model, deck, tmpdir)
        assert len(deck.notes) == 2

    @patch('german_anki_generator.generate_audio')
    def test_dual_reflexive_nr_hint(self, mock_audio):
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(DUAL_REFLEXIVE_CLOZE_INFO, model, deck, tmpdir)
        assert deck.notes[1].fields[2] == 'introduces (he, present)'

    @patch('german_anki_generator.generate_audio')
    def test_no_cloze_sentences_creates_no_note(self, mock_audio):
        model = create_cloze_model()
        deck = make_deck()
        with tempfile.TemporaryDirectory() as tmpdir:
            create_cloze_cards(VERB_INFO, model, deck, tmpdir)  # no cloze_sentences
        assert len(deck.notes) == 0

    @patch('german_anki_generator.generate_audio')
    def test_cloze_model_id_is_fixed(self, mock_audio):
        assert create_cloze_model().model_id == CLOZE_MODEL_ID_CUSTOM
