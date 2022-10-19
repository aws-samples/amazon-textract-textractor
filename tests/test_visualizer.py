import os
import PIL
import unittest
import boto3
import uuid
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.lazy_document import LazyDocument
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, S3FilePathMissing


class TestTextractor(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        if os.environ.get("CALL_TEXTRACT"):
            self.profile_name = "default"
            self.current_directory = os.path.abspath(os.path.dirname(__file__))
            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "This test only work with CALL_TEXTRACT enabled")
    def test_detect_document_text(self):
        # Testing local single image input
        document = self.extractor.detect_document_text(
            file_source=os.path.join(self.current_directory, "fixtures/single-page-1.png"),
        )

        out1 = document.words.visualize()
        out2 = document.words.visualize(with_text=False)
        out3 = (document.words + document.lines).visualize()

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "This test only work with CALL_TEXTRACT enabled")
    def test_textractor_analyze_document(self):
        # Testing analyze_document() with local single image input
        document = self.extractor.analyze_document(
            file_source=os.path.join(self.current_directory, "fixtures/amzn_q2.png"),
            features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
        )

        out1 = document.tables.visualize()
        out2 = document.tables[0].visualize(with_text=False)
        out3 = document.pages[0].visualize()