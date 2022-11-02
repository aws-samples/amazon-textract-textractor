import unittest

from textractor.data.constants import SelectionStatus, SELECTED
from textractor.entities.bbox import BoundingBox
from textractor.entities.selection_element import SelectionElement


class TestSelectionElement(unittest.TestCase):
    def setUp(self):
        self.checkbox_bb = {
            "Width": 0.09679746627807617,
            "Height": 0.008036591112613678,
            "Left": 0.08719838410615921,
            "Top": 0.5354593992233276,
        }


    def test_is_selected(self):
        """Test case to return the selection status of the checkbox"""
        checkbox = SelectionElement(
            entity_id="checkbox-id",
            bbox=BoundingBox.from_normalized_dict(self.checkbox_bb, spatial_object=None),
            status=SelectionStatus.SELECTED,
            confidence=100,
        )
        self.assertTrue(checkbox.is_selected())


    def test_words(self):
        """Test case to return the words of the checkbox"""
        checkbox = SelectionElement(
            entity_id="checkbox-id",
            bbox=BoundingBox.from_normalized_dict(self.checkbox_bb, spatial_object=None),
            status=SelectionStatus.SELECTED,
            confidence=100,
        )
        self.assertEqual(checkbox.words, [])


    def test_repr(self):
        """Test case to return the selection status of the checkbox as string"""
        checkbox = SelectionElement(
            entity_id="checkbox-id",
            bbox=BoundingBox.from_normalized_dict(self.checkbox_bb, spatial_object=None),
            status=SelectionStatus.SELECTED,
            confidence=100,
        )
        self.assertEqual(checkbox.__repr__(), "[X]")


    def test_set_page(self):
        """Test case setter for the page attribute"""
        checkbox = SelectionElement(
            entity_id="checkbox-id",
            bbox=BoundingBox.from_normalized_dict(self.checkbox_bb, spatial_object=None),
            status=SelectionStatus.SELECTED,
            confidence=100,
        )
        checkbox.page = 2
        self.assertEqual(checkbox.page, 2)


    def test_set_page_id(self):
        """Test case setter for the page_id attribute"""
        checkbox = SelectionElement(
            entity_id="checkbox-id",
            bbox=BoundingBox.from_normalized_dict(self.checkbox_bb, spatial_object=None),
            status=SelectionStatus.SELECTED,
            confidence=100,
        )
        checkbox.page_id = "page-id"
        self.assertEqual(checkbox.page_id, "page-id")
