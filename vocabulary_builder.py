# -*- coding: utf-8 -*-

"""
Add-on package initialization
"""
import genanki
import boto3
import urllib.request
import urllib.parse
import sqlite3
import ssl
from bs4 import BeautifulSoup
from aqt import mw
from aqt.utils import showInfo
from aqt.progress import ProgressManager

from PyQt5.QtWidgets import QAction


__all__ = ['addMenuItem']


DEFAULT_OS_X_DB = "/Volumes/Kindle/system/vocabulary/vocab.db"


# CSS for making the generated cards look nice
# Adapted from https://github.com/NSBum/anki-themes
MODEL_CSS = """
.question { color: #cb4b16; }

.source {
  font-weight: bold;
  font-family: "Futura", arial, "PT Sans";
  color: #586e75;
  font-size: 20px;
}

.target {
  font-family: Georgia, "PT Serif", "Times New Roman", serif;
  font-size: 24px;
}

.cloze {
  font-weight: bold;
  color: #b58900;
}

.extras {
  font-family: "Futura", arial, "PT Sans";
  font-size: 22px;
  color: #839496;
}

h1 {
  position: relative;
  margin-top: 20px;
  color: #839496; }

h1.one {
  margin-top: 0;
  font-size: 14px; }

h1.one:before {
  content: "";
  display: block;
  border-top: solid 1px #93a1a1;
  width: 100%;
  height: 1px;
  position: absolute;
  top: 50%;
  z-index: 1; }

h1.one span {
  color: #93a1a1;
  background: #eee8d5;
  padding: 0 20px;
  position: relative;
  z-index: 5; }

ul li {
  font-family: "Futura", arial, "PT Sans";
  color: #839496;
  text-align: left; }

@media screen and (max-width: 480px) {
  .target {
    font-size: 22px; }

  .source {
    font-size: 18px; }
}

/*
 * === DEFAULT CARD FORMATTING ===
 */
.card {
  font-family: "Futura", arial, "PT Sans";
  font-size: 20px;
  text-align: center;
  color: #073642;
  background: #eee8d5;
}
"""


class VocabNote(genanki.Note):

    @property
    def guid(self):
        return genanki.guid_for(self.fields[0])


vocab_model = genanki.Model(
  1441293701,
  'Vocabulary Builder Model',
  fields=[
    {'name': 'Usage'},
    {'name': 'Translation'},
    {'name': 'Stem'},
    {'name': 'Definition'}
  ],
  templates=[
    {
      'name': 'Vocabulary Builder',
      'qfmt': """
        <p class="target question">{{cloze:Usage}}</p>
        <br />
        <h1 class="one"><span>Definition</span></h1>
        <div class="extras">{{Definition}}</div>
        """,
      'afmt': """
        <p class="target question">{{cloze:Usage}}</p>
        <p class="source">{{Translation}}</p>
        <p>Stem: {{Stem}}</p>
        <br />
        <h1 class="one"><span>Definition</span></h1>
        <div class="extras">{{Definition}}</div>
        """,
    },
  ],
  css=MODEL_CSS)


vocab_deck = genanki.Deck(
  1638698262,
  'Vocabulary Builder')


translate_client = boto3.client('translate', region_name='us-east-1')


def clean_definition(definition):
    """
    Remove unnecessary text from a Definition list item
    """
    try:
        definition.select_one('.indicateurDefinition').decompose()
    except AttributeError:
        pass  # skip if span is missing

    try:
        definition.select_one('.ExempleDefinition').decompose()
    except AttributeError:
        pass  # skip if span is missing

    # cleanup extra : characters when definitions are at the end
    text = definition.text
    if text[len(text)-1] != '.':
        try:
            text, _ = text.split(':')
        except ValueError:
            pass
        text = text.strip()
        text = text + '.'

    return text


def define(word):
    """
    Lookup a word in the Larousse dictionary. Returns a list of definitions.
    """
    larousse_url = 'https://www.larousse.fr/dictionnaires/francais/%s/'
    ssl._create_default_https_context = ssl._create_unverified_context
    lookup_url = larousse_url % urllib.parse.quote(word)

    html = urllib.request.urlopen(lookup_url)
    soup = BeautifulSoup(html, 'html.parser')

    try:
        definitions = soup.find('ul', {"class": "Definitions"}).find_all('li')
        return [clean_definition(d) for d in definitions]
    except AttributeError:
        return []  # no definitions found, return empty list


def translate(phrase, source_language='fr', target_language='en'):
    """
    Translate a phrase from source to target language.
    """
    translation = translate_client.translate_text(
        Text=phrase,
        SourceLanguageCode=source_language,
        TargetLanguageCode=target_language)

    return translation['TranslatedText']


def create_note(word, stem, usage):
    """
    Create an Anki note from the word and usage.
    """
    definitions = define(stem)
    if not definitions:
        return

    translation = translate(usage)

    note = VocabNote(
        model=vocab_model,
        fields=[
            usage.replace(word, "{{c1::" + word + "}}"),
            translation,
            stem,
            "<br/>".join(definitions)])

    vocab_deck.add_note(note)


def import_words():
    """
    Import words from vocab.db into the deck "Vocabulary Builder".
    """
    db = DEFAULT_OS_X_DB
    try:
        vocabdb = sqlite3.connect(db)
    except sqlite3.OperationalError as e:
        showInfo(f"Error connecting to database: {e}")
        return

    cursor = vocabdb.cursor()
    query = '''
        SELECT WORDS.word, WORDS.stem, LOOKUPS.usage
        FROM WORDS
        JOIN LOOKUPS ON WORDS.id = LOOKUPS.word_key
        WHERE WORDS.lang=\'fr\''''
    cursor.execute(query)
    results = cursor.fetchall()

    mw.checkpoint("Importing words from Kindle")

    progress = ProgressManager(mw)
    progress.start(immediate=True)
    # Create an Anki card for each word
    word_num = 0
    total_words = len(results)
    for result in results:
        word_num = word_num + 1
        word = result[0]
        progress.update(f"Importing word {word_num} of {total_words}: {word}")
        stem = result[1]
        usage = result[2]
        create_note(word, stem, usage)

    # Create an Anki package based on the contents
    # vocab_package = genanki.Package(vocab_deck)
    # vocab_package.write_to_file('output.apkg')
    vocab_deck.write_to_collection_from_addon()

    # Reset the word database so new words show up
    progress.finish()
    mw.reset()

    vocabdb.close()


def addMenuItem():
    """
    Adds a menu item to the Tools menu in Anki's main window for
    launching the VocabularyBuilder dialog.
    """
    action = QAction("Import words from Kindle", mw)
    action.triggered.connect(import_words)
    mw.form.menuTools.addAction(action)
