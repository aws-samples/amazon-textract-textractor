"""Tests for all Word class methods."""

import unittest

from textractor.entities.bbox import BoundingBox
from textractor.data.constants import TextTypes
from textractor.entities.word import Word

class TestWord(unittest.TestCase):
    def setUp(self):
        self.bounding_box = {
            "Width": 0.10809839516878128,
            "Height": 0.01363567914813757,
            "Left": 0.036161474883556366,
            "Top": 0.03439946100115776,
        }


    def test_set_text(self):
        """Test case setter for the text attribute"""
        word = Word(
            entity_id="word-id",
            bbox=BoundingBox.from_normalized_dict(self.bounding_box, spatial_object=None),
        )
        word.text = "word-test"
        self.assertEqual(word.text, "word-test")


    def test_set_text_type(self):
        """Test case setter for the text type attribute"""
        word = Word(
            entity_id="word-id",
            bbox=BoundingBox.from_normalized_dict(self.bounding_box, spatial_object=None),
        )
        word.text_type = TextTypes.HANDWRITING
        self.assertEqual(word.text_type, TextTypes.HANDWRITING)


    def test_set_page(self):
        """Test case setter for the page attribute"""
        word = Word(
            entity_id="word-id",
            bbox=BoundingBox.from_normalized_dict(self.bounding_box, spatial_object=None),
        )
        word.page = 2
        self.assertEqual(word.page, 2)


    def test_set_page_id(self):
        """Test case setter for the page_id attribute"""
        word = Word(
            entity_id="word-id",
            bbox=BoundingBox.from_normalized_dict(self.bounding_box, spatial_object=None),
        )
        word.page_id = "page-id"
        self.assertEqual(word.page_id, "page-id")


    def test_repr(self):
        """Test case setter for the repr function"""
        word = Word(
            entity_id="word-id",
            bbox=BoundingBox.from_normalized_dict(self.bounding_box, spatial_object=None),
        )
        word.text = "word-test"
        self.assertEqual(word.__repr__(), "word-test")
