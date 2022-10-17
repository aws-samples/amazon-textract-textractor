import unittest
import numpy
from textractor.entities.bbox import BoundingBox

class TestBoundingBox(unittest.TestCase):
    def test_bbox(self):
        dims = {"Width": 3, "Height": 4, "Left": 1, "Top": 2}
        bbox = BoundingBox.from_normalized_dict(dims, spatial_object=None)

        self.assertTrue(isinstance(bbox.as_denormalized_numpy(), numpy.ndarray))
        self.assertEqual(bbox.__repr__(), "x: 1, y: 2, width: 3, height: 4")
