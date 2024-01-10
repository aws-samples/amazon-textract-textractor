import json
import os
import PIL
import unittest
import boto3
import uuid
import logging
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.data.constants import TextractFeatures
from textractor.entities.document import Document
from textractor.exceptions import InvalidProfileNameError, S3FilePathMissing
from textractor.utils.s3_utils import upload_to_s3, delete_from_s3

class TestGetTextAndWords(unittest.TestCase):
    """The tests below are smoke tests and are used to assess how a change impacts the output of Textractor.

    :param unittest: _description_
    :type unittest: _type_
    """
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.bucket_name = os.environ.get("S3_BUCKET", "textractor-tests")
        if os.environ.get("CALL_TEXTRACT"):
            self.s3_client = boto3.session.Session(
                profile_name=self.profile_name
            ).client("s3", region_name="us-west-2")

            self.current_directory = os.path.abspath(os.path.dirname(__file__))

            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )
            self.fixture_directory = os.path.join(self.current_directory, "fixtures")

    def test_detect_no_duplicate_words(self):
        for asset in ["amzn_q2.png", "fake_id.png", "form_1005.png", "form.png", "in-table-title.png", "matrix.png", "patient_intake_form_sample.png", "paystub_header.png", "paystub_single_table.png", "paystub_tables.png", "paystub.jpg", "reading_order.pdf", "receipt.jpg", "sample-invoice.pdf", "screenshot.png", "single-page-1.png", "single-page-2.png", "test.png", "textractor-singlepage-doc.pdf", "tutorial.pdf"]:
            # Testing that no asset causes the output to contain duplicate words
            if os.environ.get("CALL_TEXTRACT"):
                document = self.extractor.analyze_document(
                    os.path.join(self.fixture_directory, asset),
                    features=[
                        TextractFeatures.LAYOUT,
                        TextractFeatures.TABLES,
                        TextractFeatures.FORMS,
                        TextractFeatures.SIGNATURES
                    ]
                )
                with open(get_fixture_path()[:-5] + "_" + asset + ".json", "w") as f:
                    json.dump(document.response, f)
            else:
                document = Document.open(get_fixture_path()[:-5] + "_" + asset + ".json")

            _, words = document.get_text_and_words()

            word_ids = set()
            for word in words:
                self.assertNotIn(word.id, word_ids, f"Word {word} ({word.id}) exists twice in the output for asset {asset}")
                word_ids.add(word.id)

    def test_detect_no_missing_words(self):
        # Change the path since we don't want to re-run Textract for all files
        fixture_path = get_fixture_path().replace("test_detect_no_missing_words", "test_detect_no_duplicate_words")
        for asset in ["amzn_q2.png", "fake_id.png", "form_1005.png", "form.png", "in-table-title.png", "matrix.png", "patient_intake_form_sample.png", "paystub_header.png", "paystub_single_table.png", "paystub_tables.png", "paystub.jpg", "reading_order.pdf", "receipt.jpg", "sample-invoice.pdf", "screenshot.png", "single-page-1.png", "single-page-2.png", "test.png", "textractor-singlepage-doc.pdf", "tutorial.pdf"]:
            # Testing that no asset causes the output to contain duplicate words
            if os.environ.get("CALL_TEXTRACT"):
                document = self.extractor.analyze_document(
                    os.path.join(self.fixture_directory, asset),
                    features=[
                        TextractFeatures.LAYOUT,
                        TextractFeatures.TABLES,
                        TextractFeatures.FORMS,
                        TextractFeatures.SIGNATURES
                    ]
                )
                with open(fixture_path[:-5] + "_" + asset + ".json", "w") as f:
                    json.dump(document.response, f)
            else:
                document = Document.open(fixture_path[:-5] + "_" + asset + ".json")

            _, words = document.get_text_and_words()

            original_word_set = set([b["Id"] for b in document.response["Blocks"] if b["BlockType"] == "WORD"])
            word_ids = set([w.id for w in words])

            self.assertTrue(original_word_set.issubset(word_ids))
