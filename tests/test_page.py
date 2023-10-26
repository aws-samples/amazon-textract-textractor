import json
import os
import unittest
import PIL
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.page import Page
from textractor.entities.table import Table
from textractor.entities.value import Value
from textractor.data.constants import TableFormat
from textractor.entities.key_value import KeyValue
from textractor.visualizers.entitylist import EntityList
from textractor.exceptions import InvalidProfileNameError
from textractor.entities.selection_element import SelectionElement
from textractor.data.constants import TextTypes, SimilarityMetric, TextractFeatures, Direction, DirectionalFinderType

from .utils import save_document_to_fixture_path

try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except:
    SENTENCE_TRANSFORMERS_AVAILABLE = False 

class TestPage(unittest.TestCase):
    def test_page(self):
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

        page = document.page(0)

        self.assertIsInstance(page.words, EntityList)
        self.assertIsInstance(page.words[0], Word)
        self.assertEqual(len(page.words), 51)

        self.assertIsInstance(page.lines, EntityList)
        self.assertIsInstance(page.lines[0], Line)
        self.assertEqual(len(page.lines), 24)

        self.assertIsInstance(page.key_values, EntityList)
        self.assertIsInstance(page.key_values[0], KeyValue)
        self.assertIsInstance(page.key_values[0].value, Value)
        self.assertEqual(len(page.key_values), 3)
        self.assertIsInstance(page.key_values.pretty_print(), str)
        self.assertGreater(len(page.tables.pretty_print(table_format=TableFormat.CSV)), 100)


        self.assertIsInstance(page.checkboxes, EntityList)
        self.assertIsInstance(page.checkboxes[0], KeyValue)
        self.assertIsInstance(page.checkboxes[0].value, Value)
        self.assertEqual(page.checkboxes[0].value.words, [])
        self.assertIsInstance(page.checkboxes[0].value.children[0], SelectionElement)
        self.assertEqual(len(page.checkboxes), 2)

        self.assertIsInstance(page.tables, EntityList)
        self.assertEqual(len(page.tables), 1)
        self.assertIsInstance(page.tables.pretty_print(), str)
        self.assertGreater(len(page.tables.pretty_print()), 100)

        self.assertEqual(
            page.__repr__(),
            "This Page (1) holds the following data:\nWords - 51\nLines - 24\nKey-values - 3\nCheckboxes - 2\nTables - 1\nQueries - 0\nSignatures - 0\nExpense documents - 0\nLayout elements - 11"
        )

        self.assertEqual(len(page.keys(include_checkboxes=True)), 5)
        self.assertEqual(len(page.keys(include_checkboxes=False)), 3)

        self.assertEqual(len(page.filter_checkboxes(selected=True, not_selected=True)), 2)
        self.assertEqual(len(page.filter_checkboxes(selected=True, not_selected=False)), 1)
        self.assertEqual(len(page.filter_checkboxes(selected=False, not_selected=True)), 1)
        self.assertEqual(len(page.filter_checkboxes(selected=False, not_selected=False)), 0)

        self.assertIsInstance(page.get_words_by_type(), EntityList)
        self.assertIsInstance(page.get_words_by_type()[0], Word)
        self.assertEqual(len(page.get_words_by_type(TextTypes.PRINTED)), 51)
        self.assertEqual(len(page.get_words_by_type(TextTypes.HANDWRITING)), 0)

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.assertIsInstance(
                page.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList,
            )
            self.assertIsInstance(
                page.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                Word,
            )
            self.assertIsInstance(
                page.search_words(
                    keyword="Table",
                    top_k=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                Word,
            )
            self.assertEqual(
                len(
                    page.search_words(
                        keyword="Table",
                        top_k=5,
                        similarity_metric=SimilarityMetric.COSINE,
                        similarity_threshold=0.6,
                    )
                ),
                1
            )

            self.assertIsInstance(
                page.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList,
            )
            self.assertIsInstance(
                page.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                Line,
            )
            self.assertIsInstance(
                page.search_lines(
                    keyword="Textractor",
                    top_k=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                Line,
            )
            self.assertEqual(
                len(
                    page.search_lines(
                        keyword="Textractor",
                        top_k=5,
                        similarity_metric=SimilarityMetric.COSINE,
                        similarity_threshold=0.6,
                    )
                ),
                2
            )

            self.assertIsInstance(
                page.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                ),
                EntityList,
            )
            self.assertIsInstance(
                page.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.COSINE,
                    similarity_threshold=0.6,
                )[0],
                KeyValue,
            )
            self.assertIsInstance(
                page.get(
                    key="date",
                    top_k_matches=5,
                    similarity_metric=SimilarityMetric.EUCLIDEAN,
                    similarity_threshold=0.6,
                )[0],
                KeyValue,
            )
            self.assertEqual(
                len(
                    page.get(
                        key="date",
                        top_k_matches=5,
                        similarity_metric=SimilarityMetric.COSINE,
                        similarity_threshold=0.6,
                    )
                ),
                1
            )
            self.assertEqual(
                len(page.directional_finder(
                    word_1 = "key-values",
                    word_2 = "table 1",
                    prefix = "",
                    direction=Direction.BELOW,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )),
                3
            )

            self.assertEqual(len(page.directional_finder(
                    word_1 = "key-values",
                    word_2 = "",
                    prefix = "",
                    direction=Direction.LEFT,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )), 0)

            self.assertEqual(len(page.directional_finder(
                    word_1 = "key-values",
                    word_2 = "",
                    prefix = "",
                    direction=Direction.RIGHT,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )), 3)

            self.assertEqual(len(page.directional_finder(
                    word_1 = "key-values",
                    word_2 = "",
                    prefix = "",
                    direction=Direction.ABOVE,
                    entities=[DirectionalFinderType.KEY_VALUE_SET, DirectionalFinderType.SELECTION_ELEMENT],
                )), 0)

        self.assertIsInstance(
            page.search_words(
                keyword="Table",
                top_k=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=5,
            )[0],
            Word,
        )
        self.assertIsInstance(
            page.get(
                key="date",
                top_k_matches=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=5,
            )[0],
            KeyValue,
        )
        self.assertIsInstance(
            page.search_lines(
                keyword="Textractor",
                top_k=5,
                similarity_metric=SimilarityMetric.LEVENSHTEIN,
                similarity_threshold=5,
            )[0],
            Line,
        )

        save_file_path = os.path.join(current_directory, "Key-Values.csv")
        page.export_kv_to_csv(include_kv=True, include_checkboxes=True, filepath=save_file_path)
        self.assertIn("Key-Values.csv", os.listdir(current_directory))
        os.remove(save_file_path)

        save_file_path = os.path.join(current_directory, "Key-Values.txt")
        page.export_kv_to_txt(include_kv=True, include_checkboxes=True, filepath=save_file_path)
        self.assertIn("Key-Values.txt", os.listdir(current_directory))
        os.remove(save_file_path)

        save_file_path = os.path.join(current_directory, "Tables.xlsx")
        page.export_tables_to_excel(filepath=save_file_path)
        self.assertIn("Tables.xlsx", os.listdir(current_directory))
        os.remove(save_file_path)

        self.assertEqual(len(page.independent_words()), 10)
        self.assertIsInstance(page.independent_words()[0], Word)

        self.assertIsInstance(page.independent_words(), EntityList)
        self.assertIsInstance(page.independent_words()[0], Word)

        self.assertIsInstance(page.return_duplicates(), list)
        self.assertIsInstance(page.return_duplicates()[0], EntityList)
