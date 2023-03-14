import boto3
import os
import PIL
import unittest
import json
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.lazy_document import LazyDocument
from textractor.visualizers.entitylist import EntityList
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, S3FilePathMissing
from textractor.utils.s3_utils import upload_to_s3, delete_from_s3

class TestWordOrdering(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.bucket_name = os.environ.get("S3_BUCKET", "textractor-tests")
        if os.environ.get("CALL_TEXTRACT"):
            self.s3_client = boto3.session.Session(
                profile_name=self.profile_name
            ).client("s3", region_name="us-west-2")

            if self.profile_name is None:
                raise InvalidProfileNameError(
                    "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
                )
            self.current_directory = os.path.abspath(os.path.dirname(__file__))
            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )

    def test_word_ordering_in_cell(self):
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                file_source=os.path.join(self.current_directory, "fixtures/reading_order.pdf"),
                features=[TextractFeatures.TABLES]
            )
            with open(get_fixture_path(), "w") as fh:
                json.dump(document.response, fh)
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(document.tables[0].table_cells[0].text.strip(), "Are those Words in order?")

