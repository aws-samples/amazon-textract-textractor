import json
import os
import unittest
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.word import Word
from textractor.entities.table import Table
from textractor.entities.table_cell import TableCell
from textractor.visualizers.entitylist import EntityList
from textractor.exceptions import InvalidProfileNameError
from textractor.data.constants import TextractFeatures, TextTypes, CellTypes

from .utils import save_document_to_fixture_path

try:
    import sentence_transformers
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class TestTable(unittest.TestCase):
    def test_table(self):
        # Insert credentials here to run test
        profile_name = "default"
        current_directory = os.path.abspath(os.path.dirname(__file__))

        if profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_table.py."
            )

        if os.environ.get("CALL_TEXTRACT"):
            extractor = Textractor(
                profile_name=profile_name, kms_key_id=""
            )
            document = extractor.analyze_document(
                file_source=os.path.join(current_directory, "fixtures/single-page-1.png"),
                features=[TextractFeatures.TABLES],
                save_image=False,
            )
        else:
            document = Document.open(get_fixture_path())

        table = document.tables[0]

        self.assertIsInstance(table.words, EntityList)
        self.assertEqual(len(table.words), 28)
        self.assertIsInstance(table.words[0], Word)

        self.assertEqual(table.page, 1)
        self.assertIsInstance(table.page_id, str)

        self.assertEqual(len(table.get_words_by_type(TextTypes.PRINTED)), 28)
        self.assertEqual(len(table.get_words_by_type(TextTypes.HANDWRITING)), 0)

        self.assertEqual(table.get_table_range(), (3, 5))

        new_table = table.strip_headers()
        self.assertEqual(new_table.get_table_range(), (2, 5))

        self.assertEqual(len(table.get_cells_by_type(CellTypes.COLUMN_HEADER).keys()), 4)
        self.assertEqual(table[1:, 1:].get_table_range(), (2, 4))

        table.to_excel(os.path.join(current_directory, "table.xlsx"))
        self.assertIn("table.xlsx", os.listdir(current_directory))
        os.remove(os.path.join(current_directory, "table.xlsx"))

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.assertEqual(table.get_columns_by_name(
                ["Cell 1"], similarity_threshold=0.9
            ).get_table_range(), (3, 1))

        cell = table.table_cells[0]
        self.assertEqual(cell.page, 1)
        self.assertIsInstance(cell.page_id, str)

        self.assertEqual(cell.row_index, 1)
        self.assertEqual(cell.col_index, 1)
        self.assertEqual(cell.row_span, 1)
        self.assertEqual(cell.col_span, 1)

        self.assertIsInstance(cell.words, EntityList)
        self.assertIsInstance(cell.words[0], Word)

        self.assertIsInstance(cell.table_id, str) or cell.table_id is None
        self.assertEqual(len(cell.get_words_by_type(TextTypes.PRINTED)), 2)
        self.assertEqual(len(cell.get_words_by_type(TextTypes.HANDWRITING)), 0)

        self.assertEqual(cell.merge_direction(), (None, "None"))
        self.assertEqual(cell.__repr__(), "<Cell: (1,1), Span: (1, 1), Column Header: True, MergedCell: False>  Cell 1")

    def test_table_with_title_and_footers(self):
        # Insert credentials here to run test
        profile_name = "default"
        current_directory = os.path.abspath(os.path.dirname(__file__))

        if profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_table.py."
            )

        if os.environ.get("CALL_TEXTRACT"):
            extractor = Textractor(
                profile_name=profile_name, kms_key_id=""
            )
            document = extractor.analyze_document(
                file_source=os.path.join(current_directory, "fixtures/paystub.jpg"),
                features=[TextractFeatures.TABLES],
                save_image=False,
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(len(document.tables), 7)
        self.assertNotEqual(document.tables[3].title, None)
        self.assertEqual(len(document.tables[4].footers), 1)

if __name__ == "__main__":
    test = TestTable()
    test.setUp()
    test.test_table()