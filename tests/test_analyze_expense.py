import json
import os
import PIL
import unittest
from textractor import Textractor
from textractor.entities.document import Document
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, NoImageException, S3FilePathMissing

from .utils import get_fixture_path

class TestTextractorAnalyzeExpense(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.current_directory = os.path.abspath(os.path.dirname(__file__))
        self.image_path = os.path.join(self.current_directory, "fixtures/receipt.jpg")
        self.image = PIL.Image.open(self.image_path)

        if self.profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
            )
        if os.environ.get("CALL_TEXTRACT"):
            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )

    def test_analyze_expense_from_path(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_expense(file_source=self.image_path)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)
        self.assertEqual(document.expense_documents[0].get("TOTAL").text, "$1810.46")
    
    def test_analyze_expense_from_image(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_expense(file_source=self.image)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)
        self.assertEqual(document.expense_documents[0].get("TOTAL").text, "$1810.46")

if __name__ == "__main__":
    test = TestTextractorAnalyzeExpense()
    test.setUp()
    test.test_analyze_expense_from_path()