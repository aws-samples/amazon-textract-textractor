import os
import unittest
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.exceptions import InputError, InvalidProfileNameError
from textractor.data.constants import TextractFeatures

from .utils import save_document_to_fixture_path

class QueriesTests(unittest.TestCase):
    def test_queries_as_strings(self):
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
                features=[TextractFeatures.QUERIES],
                queries=[
                    "What is the name of the package?",
                    "What is the title of the document?",
                ],
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(len(document.queries), 2)
        self.assertEqual(document.queries[0].result.answer, "Textractor")
        self.assertEqual(document.queries[1].result.answer, "Textractor Test Document")

    def test_bad_queries_as_strings(self):
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
                features=[TextractFeatures.QUERIES],
                queries=[
                    "Lorem ipsum?",
                    "The quick brown fox jumps over the lazy dog?",
                ],
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(len(document.queries), 2)
        self.assertEqual(document.queries[0].result, None)
        self.assertEqual(document.queries[1].result, None)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_query_feature_without_queries(self):
        profile_name = "default"
        current_directory = os.path.abspath(os.path.dirname(__file__))

        if profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_table.py."
            )

        extractor = Textractor(profile_name=profile_name, kms_key_id="")
        with self.assertRaises(InputError):
            document = extractor.analyze_document(
                file_source=os.path.join(current_directory, "fixtures/single-page-1.png"),
                features=[TextractFeatures.TABLES],
                queries=[
                    "Lorem ipsum?",
                    "The quick brown fox jumps over the lazy dog?",
                ],
            )
