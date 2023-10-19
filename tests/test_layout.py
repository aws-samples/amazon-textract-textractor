import json
import os
import unittest
import PIL
from tests.utils import get_fixture_path
from textractor import Textractor
from textractor.entities.document import Document
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.page import Page
from textractor.entities.table import Table
from textractor.entities.value import Value
from textractor.data.constants import TableFormat
from textractor.entities.key_value import KeyValue
from textractor.visualizers.entitylist import EntityList
from textractor.exceptions import InvalidProfileNameError
from textractor.entities.selection_element import SelectionElement
from textractor.data.constants import TextTypes, SimilarityMetric, TextractFeatures, Direction, DirectionalFinderType

from .utils import save_document_to_fixture_path

class TestLayout(unittest.TestCase):
    def test_layout(self):
        profile_name = "default"
        current_directory = os.path.abspath(os.path.dirname(__file__))

        if profile_name is None:
            raise InvalidProfileNameError(
                "Textractor could not be initialized. Populate profile_name with a valid input in tests/test_table.py."
            )

        if os.environ.get("CALL_TEXTRACT"):
            extractor = Textractor(profile_name=profile_name, kms_key_id="")
            document = extractor.analyze_document(
                file_source=os.path.join(current_directory, "fixtures/paystub.jpg"),
                features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES, TextractFeatures.FORMS],
            )
            with open(get_fixture_path(), "w") as f:
                json.dump(document.response, f)
        else:
            document = Document.open(get_fixture_path())

        print(document.text)
