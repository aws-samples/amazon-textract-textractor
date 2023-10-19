"""All test cases for methods in KeyValue class"""

from typing import List
import unittest

from textractor.entities.key_value import KeyValue
from textractor.entities.value import Value
from textractor.entities.word import Word
from textractor.entities.line import Line
from textractor.entities.bbox import BoundingBox
from textractor.data.constants import TextTypes
from textractor.visualizers.entitylist import EntityList

class TestKeyValue(unittest.TestCase):
    def setUp(self):
        # dummy values for bounding boxes
        self.key_bb = {
            "Width": 0.09679746627807617,
            "Height": 0.008036591112613678,
            "Left": 0.08719838410615921,
            "Top": 0.5354593992233276,
        }
        self.value_bb = {
            "Width": 0.02524515800178051,
            "Height": 0.01746263913810253,
            "Left": 0.18779051303863525,
            "Top": 0.4229613244533539,
        }
        self.word_bb_1 = {
            "Width": 0.10809839516878128,
            "Height": 0.01363567914813757,
            "Left": 0.036161474883556366,
            "Top": 0.03439946100115776,
        }
        self.word_bb_2 = {
            "Width": 0.18033172190189362,
            "Height": 0.01742148958146572,
            "Left": 0.22032427787780762,
            "Top": 0.03645794093608856,
        }
        self.word_bb_3 = {
            "Width": 0.03744738921523094,
            "Height": 0.016524378210306168,
            "Left": 0.4087739884853363,
            "Top": 0.0368686243891716,
        }
        self.word_1 = Word(
            entity_id="word-id-1",
            bbox=BoundingBox.from_normalized_dict(self.word_bb_1, spatial_object=None),
            text="TEST",
            text_type=TextTypes.PRINTED,
        )
        self.word_2 = Word(
            entity_id="word-id-2",
            bbox=BoundingBox.from_normalized_dict(self.word_bb_2, spatial_object=None),
            text="KEY",
            text_type=TextTypes.HANDWRITING,
        )
        self.word_3 = Word(
            entity_id="word-id-3",
            bbox=BoundingBox.from_normalized_dict(self.word_bb_3, spatial_object=None),
            text="WORDS",
            text_type=TextTypes.PRINTED,
        )
        self.word_objs = [self.word_1, self.word_2, self.word_3]

        self.value = Value(
            entity_id="value-id",
            bbox=BoundingBox.from_normalized_dict(self.value_bb, spatial_object=None),
        )
        self.value_word = Word(
            entity_id="value-word-id",
            bbox=BoundingBox.from_normalized_dict(self.word_bb_1, spatial_object=None),
            text="TEST VALUE",
            text_type=TextTypes.HANDWRITING,
        )
        self.value.words = [self.value_word]

        self.kv = KeyValue(
            entity_id="kv-id",
            bbox=BoundingBox.from_normalized_dict(self.key_bb, spatial_object=None),
            contains_checkbox=False,
            value=None,
        )
        self.kv.page_id = "page-id"
        self.kv.key = self.word_objs
        self.kv.page = 2
        self.kv.value = self.value

    def test_key(self):
        """Test case to set Key field to a key-value pair"""
        self.assertIsInstance(self.kv.key, List)


    def test_value(self):
        """Test case to set Value field to a key-value pair"""
        self.assertEqual(self.kv.value, self.value)


    def test_words(self):
        """Test case to get words of a key-value pair"""
        self.assertEqual(set(self.kv.words), set(EntityList(self.word_objs + [self.value_word])))


    def test_set_page(self):
        """Test case setter for the page attribute"""
        self.assertEqual(self.kv.page, 2)


    def test_set_page_id(self):
        """Test case setter for the page_id attribute"""
        self.assertEqual(self.kv.page_id, "page-id")


    def test_get_words_by_type(self):
        """Test case to retrieve words of specified text_type in key-value pair"""
        # asserting on set because ordering in returned word lists isn't important
        self.assertEqual(
            set(self.kv.get_words_by_type(text_type=TextTypes.PRINTED)),
            set(EntityList([self.word_1, self.word_3])
        ))
        self.assertEqual(
            set(self.kv.get_words_by_type(text_type=TextTypes.HANDWRITING)),
            set(EntityList([self.word_2, self.value_word])
        ))


    def test_repr(self):
        """Test case to retrieve KeyValue representation"""
        self.assertEqual(self.kv.__repr__(), "TEST KEY WORDS : TEST VALUE")
