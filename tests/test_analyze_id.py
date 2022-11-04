import json
import os
import PIL
import unittest
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.data.constants import TextractFeatures, AnalyzeIDFields
from textractor.exceptions import InvalidProfileNameError, NoImageException, S3FilePathMissing

from .utils import save_document_to_fixture_path

class TestTextractorAnalyzeID(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.current_directory = os.path.abspath(os.path.dirname(__file__))
        self.image_path = os.path.join(self.current_directory, "fixtures/fake_id.png")
        self.image = PIL.Image.open(os.path.join(self.current_directory, "fixtures/fake_id.png"))

        if self.profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
            )
        if os.environ.get("CALL_TEXTRACT"):
            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )

    def test_analyze_id_from_path(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_id(
                file_source=self.image_path,
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.identity_documents), 1)
        self.assertEqual(len(document.identity_documents[0].fields), 21)
        self.assertEqual(document.identity_documents[0].get(AnalyzeIDFields.FIRST_NAME), "GARCIA")
        self.assertEqual(document.identity_documents[0][AnalyzeIDFields.FIRST_NAME], "GARCIA")
    
    def test_analyze_id_from_image(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_id(
                file_source=self.image,
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.identity_documents), 1)
        self.assertEqual(len(document.identity_documents[0].fields), 21)
        self.assertEqual(document.identity_documents[0].get("FIRST_NAME"), "GARCIA")
        self.assertEqual(document.identity_documents[0]["FIRST_NAME"], "GARCIA")

if __name__ == "__main__":
    test = TestTextractorAnalyzeID()
    test.setUp()
    test.test_analyze_id_from_path()