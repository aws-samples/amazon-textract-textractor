import os
import PIL
import unittest
import boto3
import uuid
import logging
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.lazy_document import LazyDocument
from textractor.data.constants import TextractFeatures
from textractor.exceptions import InvalidProfileNameError, S3FilePathMissing
from textractor.utils.s3_utils import upload_to_s3, delete_from_s3


class TestTextractor(unittest.TestCase):
    def setUp(self):
        # insert credentials and filepaths here to run test
        #self.profile_name = "default"
        self.bucket_name = os.environ.get("S3_BUCKET", "textractor-tests")
        if os.environ.get("CALL_TEXTRACT"):
            self.s3_client = boto3.session.Session(
                #profile_name=self.profile_name
                region_name="us-west-2"
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

            #if self.profile_name is None:
            #    raise InvalidProfileNameError(
            #        "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_textractor.py."
            #    )
            self.extractor = Textractor(
                #profile_name=self.profile_name, kms_key_id=""
                region_name="us-west-2"
            )

    def test_detect_document_text(self):
        # Testing local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.detect_document_text(
                file_source=os.path.join(self.current_directory, "fixtures/single-page-1.png"),
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)

    def test_detect_document_text_single_page_pdf_input(self):
        # Testing single page pdf input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.detect_document_text(
                file_source=os.path.join(self.current_directory, "fixtures/textractor-singlepage-doc.pdf"),
                save_image=False,
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertIs(document.pages[0].image, None)

    def test_detect_document_text_list_PIL_images(self):
        # Testing list of PIL image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.detect_document_text(
                file_source=[self.image_1],
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.pages), 1)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_pil_image_input(self):
        # Test PIL image input
        image_1 = PIL.Image.open(os.path.join(self.current_directory, "fixtures/single-page-1.png"))
        document = self.extractor.detect_document_text(
            file_source=image_1,
        )

    def test_textractor_s3_image_input(self):
        # Test S3 location path input
        if os.environ.get("CALL_TEXTRACT"):
            if self.s3_image_file is None:
                raise S3FilePathMissing(
                    "S3 URI needed to run test. Populate s3_image_file with a valid input in tests/test_textractor.py."
                )
            document = self.extractor.detect_document_text(
                file_source=self.s3_image_file,
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertIsInstance(document, Document)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_start_document_text_detection(self):
        # Testing start_document_text_detection() with local multipage pdf input
        document = self.extractor.start_document_text_detection(
            file_source=os.path.join(self.current_directory, "fixtures/textractor-multipage-doc.pdf"),
            s3_output_path=self.s3_output_path,
            s3_upload_path=self.s3_upload_path,
        )

        self.assertEqual(len(document.pages), 2)
        self.assertIsInstance(document, LazyDocument)

    def test_textractor_analyze_document(self):
        # Testing analyze_document() with local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                file_source=os.path.join(self.current_directory, "fixtures/single-page-1.png"),
                features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            )
        else:
            document = Document.open(get_fixture_path())

        self.assertEqual(len(document.pages), 1)
        self.assertIsInstance(document, Document)

    def test_textractor_analyze_document_local_pillow_image(self):
        # Testing analyze_document() with local PIL image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                file_source=self.image_1,
                features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            )
        else:
            document = Document.open(get_fixture_path())
        
        self.assertEqual(len(document.pages), 1)
        self.assertIsInstance(document, Document)

    def test_textractor_analyze_document_pillow_image_list(self):
        # Testing analyze_document() with local single image input
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                file_source=[self.image_1],
                features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
                save_image=True,
            )
        else:
            document = Document.open(get_fixture_path())
        
        self.assertEqual(len(document.pages), 1)
        self.assertIsInstance(document, Document)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_analyze_document_multipage_pdf(self):
        # Testing start_document_analysis() with local multipage pdf input
        document = self.extractor.start_document_analysis(
            file_source=os.path.join(self.current_directory, "fixtures/textractor-multipage-doc.pdf"),
            features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            s3_output_path=self.s3_output_path,
            s3_upload_path=self.s3_upload_path,
        )
        
        self.assertIsInstance(document, LazyDocument)
        self.assertEqual(len(document.pages), 2)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_start_document_text_detection_multipage_pdf_s3(self):
        # Testing start_document_text_detection() with s3 multipage pdf input
        document = self.extractor.start_document_text_detection(
            file_source=self.s3_multipage_pdf_file,
            s3_output_path=self.s3_output_path,
        )
        
        self.assertEqual(len(document.pages), 2)
        self.assertIsInstance(document, LazyDocument)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_start_document_analysis_multipage_pdf_s3(self):
        # Testing start_document_analysis() with s3 multipage pdf input
        document = self.extractor.start_document_analysis(
            file_source=self.s3_multipage_pdf_file,
            features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            s3_output_path=self.s3_output_path,
        )
        
        self.assertIsInstance(document, LazyDocument)
        self.assertEqual(len(document.pages), 2)

    @unittest.skipIf(not os.environ.get("CALL_TEXTRACT"), "Asynchronous requests can't be processed without calling Textract")
    def test_textractor_start_document_analysis(self):
        # Testing start_document_analysis() with local PIL Image input
        document = self.extractor.start_document_analysis(
            file_source=self.image_1,
            features=[TextractFeatures.TABLES, TextractFeatures.FORMS],
            s3_output_path=self.s3_output_path,
            s3_upload_path=self.s3_upload_path,
        )
        
        self.assertIsInstance(document, LazyDocument)
        self.assertEqual(len(document.pages), 1)
