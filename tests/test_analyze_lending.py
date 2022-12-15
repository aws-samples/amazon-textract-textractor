import json
import os
import PIL
import boto3
import unittest
from textractor import Textractor
from textractor.entities.document import Document
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, NoImageException, S3FilePathMissing
from textractor.utils.s3_utils import upload_to_s3, delete_from_s3

from .utils import get_fixture_path

class TestTextractorAnalyzeLending(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.bucket_name = os.environ.get("S3_BUCKET", "textractor-tests")
        self.current_directory = os.path.abspath(os.path.dirname(__file__))
        self.image_path = os.path.join(self.current_directory, "fixtures/receipt.jpg")
        self.image = PIL.Image.open(self.image_path)

        if self.profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
            )
        if os.environ.get("CALL_TEXTRACT"):
            self.s3_client = boto3.session.Session(
                profile_name=self.profile_name
            ).client("s3", region_name="us-west-2")

            self.current_directory = os.path.abspath(os.path.dirname(__file__))
            for asset in ["single-page-1.png", "textractor-multipage-doc.pdf"]:
                upload_to_s3(self.s3_client, f"s3://{self.bucket_name}/{asset}", os.path.join(self.current_directory, f"fixtures/{asset}"))

            self.s3_image_file = f"s3://{self.bucket_name}/single-page-1.png"
            self.s3_multipage_pdf_file = f"s3://{self.bucket_name}/textractor-multipage-doc.pdf"
            self.s3_output_path = f"s3://{self.bucket_name}/output"
            self.s3_upload_path = f"s3://{self.bucket_name}/upload"
            self.image_1 = PIL.Image.open(os.path.join(self.current_directory, "fixtures/single-page-1.png"))
            self.image_2 = PIL.Image.open(os.path.join(self.current_directory, "fixtures/single-page-2.png"))

            if self.profile_name is None:
                raise InvalidProfileNameError(
                    "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
                )
            self.extractor = Textractor(
                profile_name=self.profile_name, kms_key_id=""
            )

    def test_analyze_lending_from_path(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.start_lending_analysis(file_source=self.s3_image_file)
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)
    
    def test_analyze_lending_from_image(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.start_lending_analysis(file_source=self.s3_multipage_pdf_file)
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)
