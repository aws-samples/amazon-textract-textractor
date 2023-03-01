"""BoundingBox class contains all the co-ordinate information for a :class:`DocumentEntity`. This class is mainly useful to locate the entity
on the image of the document page."""

from abc import ABC
from typing import Tuple, List

try:
    import numpy as np
except ImportError:
    # Used in an export_as_numpy function which won't be called if the user doesn't have numpy.
    pass

from typing import Dict
from dataclasses import dataclass


class SpatialObject(ABC):
    """
    The :class:`SpatialObject` interface defines an object that has a width and height. This mostly used for :class:`BoundingBox` \
    reference to be able to provide normalized coordinates.
    """

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height


@dataclass
class BoundingBox(SpatialObject):
    """
    Represents the bounding box of an object in the format of a dataclass with (x, y, width, height). \
    By default :class:`BoundingBox` is set to work with denormalized co-ordinates: :math:`x \in [0, docwidth]` and :math:`y \in [0, docheight]`. \
    Use the as_normalized_dict function to obtain BoundingBox with normalized co-ordinates: :math:`x \in [0, 1]` and :math:`y \in [0, 1]`. \\

    Create a BoundingBox like shown below: \\

    * Directly:             :code:`bb = BoundingBox(x, y, width, height)` \\
    * From dict:            :code:`bb = BoundingBox.from_dict(bb_dict)` where :code:`bb_dict = {'x': x, 'y': y, 'width': width, 'height': height}` \\

    Use a BoundingBox like shown below: \\

    * Directly:            :code:`print('The top left is: ' + str(bb.x) + ' ' + str(bb.y))` \\
    * Convert to dict:     :code:`bb_dict = bb.as_dict()` returns :code:`{'x': x, 'y': y, 'width': width, 'height': height}`
    """

    def __init__(
        self, x: float, y: float, width: float, height: float, spatial_object=None
    ):
        super().__init__(width, height)
        self.spatial_object = spatial_object
        self.x = x
        self.y = y

    @classmethod
    def from_normalized_dict(
        cls, bbox_dict: Dict[str, float], spatial_object: SpatialObject = None
    ):
        """
        Builds an axis aligned BoundingBox from a dictionary like :code:`{'x': x, 'y': y, 'width': width, 'height': height}`. \
        The coordinates will be denormalized according to spatial_object.

        :param bbox_dict: Dictionary of normalized co-ordinates.
        :type bbox_dict: dict
        :param spatial_object: Object with width and height attributes.
        :type spatial_object: SpatialObject

        :return: Object with denormalized co-ordinates
        :rtype: BoundingBox
        """
        return cls._from_dict(bbox_dict, spatial_object)

    @staticmethod
    def _denormalize(
        x: float,
        y: float,
        width: float,
        height: float,
        spatial_object: SpatialObject = None,
    ) -> Tuple[float, float, float, float]:
        """
        Denormalizes the coordinates according to spatial_object (used as a calibrator). \
        The SpatialObject is assumed to be a container for the bounding boxes (i.e: Page). \
        Any object with width, height attributes can be used as a SpatialObject.

        :param x: Normalized co-ordinate x
        :type x: float
        :param y: Normalized co-ordinate y
        :type y: float
        :param width: Normalized width of BoundingBox
        :type width: float
        :param height: Normalized height of BoundingBox
        :type height: float
        :param spatial_object: Object with width and height attributes (i.e: Page).
        :type spatial_object: SpatialObject

        :return: Returns x, y, width, height as denormalized co-ordinates.
        :rtype: Tuple[float, float, float, float]
        """

        x = x * spatial_object.width
        y = y * spatial_object.height
        width = width * spatial_object.width
        height = height * spatial_object.height

        return x, y, width, height

    @classmethod
    def enclosing_bbox(cls, bboxes, spatial_object:SpatialObject=None):
        """
        :param bboxes [BoundingBox]: list of bounding boxes
        :param spatial_object SpatialObject: spatial object to be added to the returned bbox
        :return:
        """
        x1, y1, x2, y2 = float('inf'), float('inf'), float('-inf'), float('-inf')
        assert any([bbox is not None for bbox in bboxes]), "At least one bounding box needs to be non-null"
        for bbox in bboxes:
            if bbox is not None:
                x1 = min(x1, bbox.x)
                x2 = max(x2, bbox.x + bbox.width)
                y1 = min(y1, bbox.y)
                y2 = max(y2, bbox.y + bbox.height)
        return BoundingBox(x1, y1, x2-x1, y2-y1, spatial_object=spatial_object)


    @classmethod
    def _from_dict(
        cls, bbox_dict: Dict[str, float], spatial_object: SpatialObject = None
    ):
        """
        Builds an axis aligned BoundingBox from a dictionary like :code:`{'x': x, 'y': y, 'width': width, 'height': height}`. \
        The co-ordinates will be denormalized according to spatial_object.

        :param bbox_dict: Dictionary of normalized co-ordinates.
        :type bbox_dict: dict
        :param spatial_object: Object with width and height attributes.
        :type spatial_object: SpatialObject

        :return: Object with denormalized coordinates
        :rtype: BoundingBox
        """
        x = bbox_dict["Left"]
        y = bbox_dict["Top"]
        width = bbox_dict["Width"]
        height = bbox_dict["Height"]
        if spatial_object is not None:
            x, y, width, height = cls._denormalize(x, y, width, height, spatial_object)
        else:
            spatial_object = None
        return BoundingBox(x, y, width, height, spatial_object)

    def as_denormalized_numpy(self):
        """
        :return: Returns denormalized co-ordinates x, y and dimensions width, height as numpy array.
        :rtype: numpy.array
        """
        return np.array([self.x, self.y, self.width, self.height])

    def __repr__(self):
        return f"x: {self.x}, y: {self.y}, width: {self.width}, height: {self.height}"
