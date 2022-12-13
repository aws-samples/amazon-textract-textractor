import os
import unittest
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.exceptions import InvalidProfileNameError
from textractor.data.constants import TextractFeatures

from .utils import save_document_to_fixture_path

class TestSignature(unittest.TestCase):
    def test_signature(self):
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
                file_source=os.path.join(current_directory, "fixtures/signature.jpg"),
                features=[TextractFeatures.SIGNATURES],
                save_image=False,
            )
            save_document_to_fixture_path(document)
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(len(document.signatures), 1)
        self.assertEqual(len(document.pages[0].signatures), 1)
