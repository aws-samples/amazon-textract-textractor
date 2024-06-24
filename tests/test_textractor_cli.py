import os
import PIL
import unittest
import boto3
import uuid
import logging
import subprocess
from typing import List
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.lazy_document import LazyDocument
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, S3FilePathMissing
from textractor.utils.s3_utils import upload_to_s3, delete_from_s3


def run_command(cmds: List):
    output = subprocess.run(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.returncode != 0:
        logging.error(output.stdout)
        logging.error(output.stderr)
        raise Exception(output.stderr)

class TestTextractor(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        #self.profile_name = "default"
        self.bucket_name = os.environ.get("S3_BUCKET", "textractor-tests")
        if os.environ.get("CALL_TEXTRACT"):
            self.s3_client = boto3.session.Session(
                #profile_name=self.profile_name
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

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_detect_document_text(self):
        run_command([
            "textractor",
            "detect-document-text",
            os.path.join(self.current_directory, "fixtures/single-page-1.png"),
            "output.json",
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_detect_document_text_single_page_pdf_input(self):
        run_command([
            "textractor",
            "detect-document-text",
            os.path.join(self.current_directory, "fixtures/textractor-singlepage-doc.pdf"),
            "output.json",
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_textractor_s3_image_input(self):
        run_command([
            "textractor",
            "detect-document-text",
            self.s3_image_file,
            "output.json",
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_textractor_start_document_text_detection(self):
        run_command([
            "textractor",
            "start-document-text-detection",
            os.path.join(self.current_directory, "fixtures/textractor-multipage-doc.pdf"),
            "--s3-upload-path",
            self.s3_upload_path,
            "--s3-output-path",
            self.s3_output_path,
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_textractor_analyze_document(self):
        run_command([
            "textractor",
            "analyze-document",
            os.path.join(self.current_directory, "fixtures/single-page-1.png"),
            "output.json",
            "--features",
            "TABLES",
            "FORMS",
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_textractor_analyze_document_multipage_pdf(self):
        run_command([
            "textractor",
            "start-document-analysis",
            os.path.join(self.current_directory, "fixtures/textractor-multipage-doc.pdf"),
            "--s3-upload-path",
            self.s3_upload_path,
            "--s3-output-path",
            self.s3_output_path,
            "--features",
            "TABLES",
            "FORMS",
        ])

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "CLI tests only work with CALL_TEXTRACT enabled")
    def test_textractor_start_document_analysis_multipage_pdf_s3(self):
        run_command([
            "textractor",
            "start-document-analysis",
            self.s3_multipage_pdf_file,
            "--s3-upload-path",
            self.s3_upload_path,
            "--s3-output-path",
            self.s3_output_path,
            "--features",
            "TABLES",
            "FORMS",
        ])
