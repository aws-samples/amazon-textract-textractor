import json
import os
import PIL
import unittest
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.page import Page
from textractor.entities.table import Table
from textractor.entities.value import Value
from textractor.entities.key_value import KeyValue
from textractor.visualizers.entitylist import EntityList
from textractor.exceptions import InvalidProfileNameError
from textractor.entities.selection_element import SelectionElement
from textractor.data.constants import TextTypes, SimilarityMetric, TextractFeatures, DirectionalFinderType, Direction

try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class TestDocument(unittest.TestCase):
    def test_document_smoke_test(self):
        profile_name = "default"
        current_directory = os.path.abspath(os.path.dirname(__file__))

        if profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_table.py."
            )

        if os.environ.get("CALL_TEXTRACT"):
            extractor = Textractor(profile_name=profile_name, kms_key_id="")
            document = extractor.analyze_document(
                file_source=os.path.join(current_directory, "fixtures/single-page-1.png"),
                features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document.pages, list)
        self.assertIsInstance(document.pages[0], Page)
        self.assertEqual(len(document.pages), 1)

        self.assertIsInstance(document.words, EntityList)
        self.assertIsInstance(document.words[0], Word)
        self.assertEqual(len(document.words), 51)

        self.assertIsInstance(document.lines, EntityList)
        self.assertIsInstance(document.lines[0], Line)
        self.assertEqual(len(document.lines), 24)

        self.assertIsInstance(document.key_values, EntityList)
        self.assertIsInstance(document.key_values[0], KeyValue)
        self.assertIsInstance(document.key_values[0].value, Value)
        self.assertEqual(len(document.key_values), 3)

        self.assertIsInstance(document.checkboxes, EntityList)
        self.assertIsInstance(document.checkboxes[0], KeyValue)
        self.assertIsInstance(document.checkboxes[0].value, Value)
        self.assertIsInstance(document.checkboxes[0].value.children[0], SelectionElement)
        self.assertEqual(len(document.checkboxes), 2)

        self.assertIsInstance(document.tables, EntityList)
        self.assertEqual(len(document.tables), 1)

        self.assertEqual(len(document.keys(include_checkboxes=True)), 5)
        self.assertEqual(len(document.keys(include_checkboxes=False)), 3)

        self.assertEqual(len(document.filter_checkboxes(selected=True, not_selected=True)), 2)
        self.assertEqual(len(document.filter_checkboxes(selected=True, not_selected=False)), 1)
        self.assertEqual(len(document.filter_checkboxes(selected=False, not_selected=True)), 1)
        self.assertEqual(len(document.filter_checkboxes(selected=False, not_selected=False)), 0)

        self.assertIsInstance(document.get_words_by_type(), EntityList)
        self.assertIsInstance(document.get_words_by_type()[0], Word)
        self.assertEqual(len(document.get_words_by_type(TextTypes.PRINTED)), 51)
        self.assertEqual(len(document.get_words_by_type(TextTypes.HANDWRITING)), 0)

        self.assertEqual(document.key_values[0].key.text, "Name of package:")

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.assertIsInstance(
                document.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList
            )
            self.assertIsInstance(
                document.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                Word
            )
            self.assertIsInstance(
                document.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                Word,
            )
            self.assertEqual(
                len(
                    document.search_words(
                        keyword="Table",
                        top_k=5,
                        similarity_metric=SimilarityMetric.COSINE,
                        similarity_threshold=0.6,
                    )
                ),
                1
            )

            self.assertIsInstance(
                document.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList,
            )
            self.assertIsInstance(
                document.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                Line,
            )
            self.assertIsInstance(
                document.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                Line,
            )
            self.assertEqual(
                len(
                    document.search_lines(
                        keyword="Textractor",
                        top_k=5,
                        similarity_metric=SimilarityMetric.COSINE,
                        similarity_threshold=0.6,
                    )
                ),
                2
            )

            self.assertIsInstance(
                document.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList,
            )
            self.assertIsInstance(
                document.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                KeyValue,
            )
            self.assertIsInstance(
                document.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                KeyValue,
            )
            self.assertEqual(len(document.directional_finder(
                    word_1 = "key-values",
                    word_2 = "table 1",
                    page = 1,
                    prefix = "",
                    direction=Direction.BELOW,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )),
                3
            )

            self.assertEqual(len(document.directional_finder(
                    word_1 = "key-values",
                    word_2 = "",
                    page = 1,
                    prefix = "",
                    direction=Direction.RIGHT,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )), 1)

            self.assertEqual(len(document.directional_finder(
                    word_1 = "key-values",
                    word_2 = "",
                    page = 1,
                    prefix = "",
                    direction=Direction.LEFT,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )), 0)
        self.assertIsInstance(
            document.search_words(
                keyword="Table",
                top_k=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=5,
            )[0],
            Word,
        )
        
        self.assertIsInstance(
            document.search_lines(
                keyword="Textractor",
                top_k=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=0.5,
            )[0],
            Line,
        )
        
        self.assertIsInstance(
            document.get(
                key="date",
                top_k_matches=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=0.5,
            )[0],
            KeyValue,
        )

        save_file_path = os.path.join(current_directory, "Key-Values.csv")
        document.export_kv_to_csv(
            include_kv=True, include_checkboxes=True, filepath=save_file_path
        )
        self.assertIn("Key-Values.csv", os.listdir(current_directory))
        os.remove(save_file_path)

        save_file_path = os.path.join(current_directory, "Key-Values.txt")
        document.export_kv_to_txt(
            include_kv=True, include_checkboxes=True, filepath=save_file_path
        )
        self.assertIn("Key-Values.txt", os.listdir(current_directory))
        os.remove(save_file_path)

        save_file_path = os.path.join(current_directory, "Tables.xlsx")
        document.export_tables_to_excel(filepath=save_file_path)
        assert "Tables.xlsx" in os.listdir(current_directory)
        os.remove(save_file_path)

        self.assertEqual(len(document.independent_words()), 10)
        self.assertIsInstance(document.independent_words()[0], Word)

        self.assertIsInstance(document.return_duplicates(), dict)
        self.assertIsInstance(document.return_duplicates()[1], list)
        self.assertIsInstance(document.return_duplicates()[1][0], EntityList)

        for page in document.pages:
            for layout in page.layouts:
                for child in layout.children:
                    self.assertIsNotNone(child.confidence, "Child confidence was None")
