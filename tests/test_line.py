import unittest

from textractor.entities.line import Line
from textractor.entities.word import Word
from textractor.data.constants import TextTypes
from textractor.entities.bbox import BoundingBox
from textractor.visualizers.entitylist import EntityList

class TestLine(unittest.TestCase):
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
        self.line_bb = {
            "Width": 0.3,
            "Height": 0.01742148958146572,
            "Left": 0.036161474883556366,
            "Top": 0.03439946100115776,
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

        self.line = Line(
            "line-id",
            BoundingBox.from_normalized_dict(self.line_bb, spatial_object=None),
            [self.word_1, self.word_2, self.word_3],
        )


    def test_get_words_by_type(self):
        """Test case to filter words of the Line by their type"""
        self.assertEqual(self.line.get_words_by_type(TextTypes.PRINTED), EntityList([self.word_1, self.word_3]))
        self.assertEqual(self.line.get_words_by_type(TextTypes.HANDWRITING), EntityList([self.word_2]))


    def test_get_text(self):
        """Test case setter for the text attribute"""
        self.assertEqual(self.line.text, "TEST WORDS ADDED")


    def test_set_page(self):
        """Test case setter for the page attribute"""
        self.line.page = 2
        self.assertEqual(self.line.page, 2)


    def test_set_page_id(self):
        """Test case setter for the page_id attribute"""
        self.line.page_id = "page-id"
        self.assertEqual(self.line.page_id, "page-id")


    def test_repr(self):
        """Test case setter for the repr function"""
        self.assertEqual(self.line.__repr__(), "TEST WORDS ADDED")
