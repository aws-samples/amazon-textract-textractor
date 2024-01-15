import json
import os
import random
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

class TestParseNoFail(unittest.TestCase):
    """The tests below are fuzzing tests and are disabled in the CI test suite.
    They are meant to generate random permutations of the input JSON response and
    ensure that the parser does not raise any exception. Their results may be flaky
    due to the randomness

    :param unittest: _description_
    :type unittest: _type_
    """
    def setUp(self):
        # insert credentials and filepaths here to run test
        self.profile_name = "default"
        self.current_directory = os.path.abspath(os.path.dirname(__file__))
        self.saved_api_responses_directory = os.path.join(self.current_directory, "fixtures", "saved_api_responses")
        self.deletion_rate = 0.5

    def test_parse_no_fail(self):
        for asset in os.listdir(self.saved_api_responses_directory):
            # Testing that no asset causes the output to contain duplicate words
            with open(os.path.join(self.saved_api_responses_directory, asset)) as f:
                response = json.load(f)

            if not "Blocks" in response:
                continue

            index_to_remove = []
            for i in range(len(response["Blocks"])):
                if response["Blocks"][i]["BlockType"] != "PAGE" and random.random() <= self.deletion_rate:
                    index_to_remove.append(i)

            for i in sorted(index_to_remove, reverse=True):
                response["Blocks"].pop(i)

            document = Document.open(response)
            document.get_text_and_words()
