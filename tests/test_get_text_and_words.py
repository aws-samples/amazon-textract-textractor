import json
import os
import PIL
import unittest
import boto3
import uuid
import logging
from lxml import html
from tests.utils import get_fixture_path

from textractor import Textractor
from textractor.data.constants import TextractFeatures
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.data.html_linearization_config import HTMLLinearizationConfig
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

    def test_table_prefixes_and_suffixes_in_text(self):
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                os.path.join(self.current_directory, "fixtures/single-page-1.png"),
                features=[
                    TextractFeatures.LAYOUT,
                    TextractFeatures.TABLES,
                    TextractFeatures.FORMS,
                    TextractFeatures.SIGNATURES
                ]
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        config = TextLinearizationConfig(
            title_prefix = "<title>",  #: Prefix for title layout elements
            title_suffix = "</title>",  #: Suffix for title layout elements
            table_layout_prefix = "<table_layout>",  #: Prefix for table elements
            table_layout_suffix = "</table_layout>",  #: Suffix for table elements
            table_prefix = "<table>",
            table_suffix = "</table>",
            table_row_prefix = "<tr>",  #: Prefix for table row
            table_row_suffix = "</tr>",  #: Suffix for table row
            table_cell_prefix = "<td>",  #: Prefix for table cell
            table_cell_suffix = "</td>",  #: Suffix for table cell
            table_cell_header_prefix = "<th>",  #: Prefix for header cell
            table_cell_header_suffix = "</th>",  #: Suffix for header cell
            header_prefix = "<header>",  #: Prefix for header layout elements
            header_suffix = "</header>",  #: Suffix for header layout elements
            section_header_prefix = "<section_header>",  #: Prefix for section header layout elements
            section_header_suffix = "</section_header>",  #: Suffix for section header layout elements
            text_prefix = "<text>",  #: Prefix for text layout elements
            text_suffix = "</text>",  #: Suffix for text layout elements
            key_value_layout_prefix = "<kv_layout>",  #: Prefix for key_value layout elements (not for individual key-value elements)
            key_value_layout_suffix = "</kv_layout>",  #: Suffix for key_value layout elements (not for individual key-value elements)
            key_value_prefix = "<kv>",  #: Prefix for key-value elements
            key_value_suffix = "</kv>",  #: Suffix for key-value elements
            key_prefix = "<key>",  #: Prefix for key elements
            key_suffix = "</key>",  #: Suffix for key elements
            value_prefix = "<value>",  #: Prefix for value elements
            value_suffix = "</value>",  #: Suffix for value elements
            add_prefixes_and_suffixes_in_text=True,
            add_prefixes_and_suffixes_as_words=True,
        )

        text, _ = document.get_text_and_words(config)

        for token in [
            "<title>",
            "</title>",
            "<table>",
            "</table>",
            "<table_layout>",
            "</table_layout>",
            "<tr>",
            "</tr>",
            "<td>",
            "</td>",
            # Sample does not have header cells
            #"<th>",
            #"</th>",
            # Sample does not have header
            #"<header>",
            #"</header>",
            "<section_header>",
            "</section_header>",
            # Sample does not have header
            #"<kv_layout>",
            #"</kv_layout>",
            "<kv>",
            "</kv>",
            "<key>",
            "</key>",
            "<value>",
            "</value>",
        ]:
            self.assertTrue(token in text, f"{token} is not in text")

    def test_table_prefixes_and_suffixes_in_words(self):
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                os.path.join(self.current_directory, "fixtures/single-page-1.png"),
                features=[
                    TextractFeatures.LAYOUT,
                    TextractFeatures.TABLES,
                    TextractFeatures.FORMS,
                    TextractFeatures.SIGNATURES
                ]
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        config = TextLinearizationConfig(
            title_prefix = "<title>",  #: Prefix for title layout elements
            title_suffix = "</title>",  #: Suffix for title layout elements
            table_layout_prefix = "<table_layout>",  #: Prefix for table elements
            table_layout_suffix = "</table_layout>",  #: Suffix for table elements
            table_prefix = "<table>",
            table_suffix = "</table>",
            table_row_prefix = "<tr>",  #: Prefix for table row
            table_row_suffix = "</tr>",  #: Suffix for table row
            table_cell_prefix = "<td>",  #: Prefix for table cell
            table_cell_suffix = "</td>",  #: Suffix for table cell
            table_cell_header_prefix = "<th>",  #: Prefix for header cell
            table_cell_header_suffix = "</th>",  #: Suffix for header cell
            header_prefix = "<header>",  #: Prefix for header layout elements
            header_suffix = "</header>",  #: Suffix for header layout elements
            section_header_prefix = "<section_header>",  #: Prefix for section header layout elements
            section_header_suffix = "</section_header>",  #: Suffix for section header layout elements
            text_prefix = "<text>",  #: Prefix for text layout elements
            text_suffix = "</text>",  #: Suffix for text layout elements
            key_value_layout_prefix = "<kv_layout>",  #: Prefix for key_value layout elements (not for individual key-value elements)
            key_value_layout_suffix = "</kv_layout>",  #: Suffix for key_value layout elements (not for individual key-value elements)
            key_value_prefix = "<kv>",  #: Prefix for key-value elements
            key_value_suffix = "</kv>",  #: Suffix for key-value elements
            key_prefix = "<key>",  #: Prefix for key elements
            key_suffix = "</key>",  #: Suffix for key elements
            value_prefix = "<value>",  #: Prefix for value elements
            value_suffix = "</value>",  #: Suffix for value elements
            add_prefixes_and_suffixes_in_text=True,
            add_prefixes_and_suffixes_as_words=True,
        )

        _, words = document.get_text_and_words(config)

        words = [w.text for w in words]

        for token in [
            "<title>",
            "</title>",
            "<table>",
            "</table>",
            "<table_layout>",
            "</table_layout>",
            "<tr>",
            "</tr>",
            "<td>",
            "</td>",
            # Sample does not have header cells
            #"<th>",
            #"</th>",
            # Sample does not have header
            #"<header>",
            #"</header>",
            "<section_header>",
            "</section_header>",
            # Sample does not have header
            #"<kv_layout>",
            #"</kv_layout>",
            "<kv>",
            "</kv>",
            "<key>",
            "</key>",
            "<value>",
            "</value>",
        ]:
            self.assertTrue(token in words, f"{token} is not in text")

    def test_figure_layout_prefixes_and_suffixes_in_text_words(self):
        if os.environ.get("CALL_TEXTRACT"):
            document = self.extractor.analyze_document(
                os.path.join(self.current_directory, "fixtures/matrix.png"),
                features=[
                    TextractFeatures.LAYOUT,
                ]
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        config = TextLinearizationConfig(
            figure_layout_prefix = "<figure>",  #: Prefix for figure elements
            figure_layout_suffix = "</figure>",  #: Suffix for figure elements
            add_prefixes_and_suffixes_in_text=True,
            add_prefixes_and_suffixes_as_words=True,
        )

        text, words = document.get_text_and_words(config)

        for token in [
            "<figure>",
            "</figure>",
        ]:
            self.assertTrue(token in text, f"{token} is not in text")

        words = [w.text for w in words]

        for token in [
            "<figure>",
            "</figure>",
        ]:
            self.assertTrue(token in words, f"{token} is not in words")

    def test_document_to_html(self):
        for asset in ["amzn_q2.png", "fake_id.png", "form_1005.png", "form.png", "in-table-title.png", "matrix.png", "patient_intake_form_sample.png", "paystub_header.png", "paystub_single_table.png", "paystub_tables.png", "reading_order.pdf", "receipt.jpg", "sample-invoice.pdf", "screenshot.png", "single-page-1.png", "single-page-2.png", "test.png", "textractor-singlepage-doc.pdf"]:
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

            
            html_document = document.to_html(HTMLLinearizationConfig(
                figure_layout_prefix="<div><p>",
                figure_layout_suffix="</p></div>",
                footer_layout_prefix="<div><p>",
                footer_layout_suffix="</p></div>",
                key_value_layout_prefix="<div><p>",
                key_value_layout_suffix="</p></div>",
                page_num_prefix="<div><p>",
                page_num_suffix="</p></div>",
            ))
            root = html.fromstring(html_document)
            
            for node in root.getiterator():
                if node.text and node.tag not in ["p", "h1", "h2", "h3", "h4", "h5", "th", "td", "caption"]:
                    raise Exception(f"Tag {node.tag} contains text {node.text}")
                
    def test_document_to_markdown(self):
        for asset in ["amzn_q2.png", "fake_id.png", "form_1005.png", "form.png", "in-table-title.png", "matrix.png", "patient_intake_form_sample.png", "paystub_header.png", "paystub_single_table.png", "paystub_tables.png", "reading_order.pdf", "receipt.jpg", "sample-invoice.pdf", "screenshot.png", "single-page-1.png", "single-page-2.png", "test.png", "textractor-singlepage-doc.pdf"]:
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

            document.to_markdown()

if __name__ == "__main__":
    TestGetTextAndWords().test_document_to_html()