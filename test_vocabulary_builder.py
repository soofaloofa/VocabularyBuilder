import os
import sys
import unittest

sys.path.insert(0, os.path.join(".", "libs"))


from vocabulary_builder import define  # noqa


class TestParseDefinition(unittest.TestCase):
    """
    Tests for the define method
    """

    def mock_fetch(self, lookup_url):
        return """
            <ul class="Definitions">
                <li class="DivisionDefinition"><span class="indicateurDefinition">Littéraire. </span>Opinion publique&nbsp;: <span class="ExempleDefinition">Avoir une bonne renommée.</span></li>
                <li class="DivisionDefinition">Opinion favorable d'un large public sur quelqu'un, quelque chose&nbsp;: <span class="ExempleDefinition">La renommée des vins de France.</span></li>
                <li class="DivisionDefinition">Avec <span class="Renvois"><a class="lienarticle" href="/dictionnaires/francais/assiduit%C3%A9/5819">assiduité</a></span>.</li>
            </ul>"""  # noqa

    def test_removes_span_tags(self):
        definitions = define("renvoie", fetch_function=self.mock_fetch)
        self.assertEqual(definitions[0], "Opinion publique.")
        self.assertEqual(definitions[1], "Opinion favorable d'un large public sur quelqu'un, quelque chose.")  # noqa
        self.assertEqual(definitions[2], "Avec assiduité.")  # noqa

    def test_handles_no_definitions(self):
        def mock_fetch(lookup_url):
            return "<span>no definitions</span>"

        self.assertListEqual([], define("renvoie", fetch_function=mock_fetch))


if __name__ == '__main__':
    unittest.main()
