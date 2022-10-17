import unittest

from textractor.data.constants import TextTypes
from textractor.entities.value import Value
from textractor.entities.word import Word
from textractor.entities.bbox import BoundingBox
from textractor.visualizers.entitylist import EntityList

class TestValue(unittest.TestCase):
    def setUp(self):
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
        self.value_bb = {
            "Width": 0.02524515800178051,
            "Height": 0.01746263913810253,
            "Left": 0.18779051303863525,
            "Top": 0.4229613244533539,
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
            text="WORDS",
            text_type=TextTypes.HANDWRITING,
        )
        self.word_3 = Word(
            entity_id="word-id-3",
            bbox=BoundingBox.from_normalized_dict(self.word_bb_3, spatial_object=None),
            text="ADDED",
            text_type=TextTypes.PRINTED,
        )

        self.value = Value(
            entity_id="value-id",
            bbox=BoundingBox.from_normalized_dict(self.value_bb, spatial_object=None),
        )
        self.word_objs = [self.word_1, self.word_2, self.word_3]
        self.value.words = self.word_objs
        self.value.key_id = "key-id"
        self.value.contains_checkbox = False
        self.value.page = 2
        self.value.page_id = "page-id"


    def test_words(self):
        """Test case to add words to the Value field of a key-value pair"""
        self.assertEqual(self.value.words, EntityList(self.word_objs))
    
    
    def test_key_id(self):
        """Test case to access Key ID of a key-value pair"""
        self.assertEqual(self.value.key_id, "key-id")
    
    
    def test_contains_checkbox(self):
        self.assertFalse(self.value.contains_checkbox)
    

    def test_set_page(self):
        """Test case setter for the page attribute"""
        self.assertEqual(self.value.page, 2)
    
    
    def test_set_page_id(self):
        """Test case setter for the page_id attribute"""
        self.assertEqual(self.value.page_id, "page-id")
    
    
    def test_get_words_by_type(self):
        """Test case to retrieve words of a specific type in the Value field of a key-value pair"""
        self.assertEqual(
            self.value.get_words_by_type(text_type=TextTypes.PRINTED),
            EntityList([self.word_1, self.word_3])
        )
        self.assertEqual(
            self.value.get_words_by_type(text_type=TextTypes.HANDWRITING),
            EntityList([self.word_2])
        )


    def test_repr(self):
        """Test case to retrieve words of the Value field in a key-value pair as text"""
        self.assertEqual(self.value.__repr__(), "TEST WORDS ADDED")
