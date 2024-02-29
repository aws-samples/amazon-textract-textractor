"""BoundingBox class contains all the co-ordinate information for a :class:`DocumentEntity`. This class is mainly useful to locate the entity
on the image of the document page."""

from abc import ABC
import logging
import math
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
    def from_denormalized_xywh(
        cls,
        x: float,
        y: float,
        width: float,
        height: float,
        spatial_object: SpatialObject = None,
    ):
        """
        Builds an axis aligned bounding box from top-left, width and height properties.
        The coordinates are assumed to be denormalized.
        :param x: Left ~ [0, doc_width]
        :param y: Top  ~ [0, doc_height]
        :param width: Width ~ [0, doc_width]
        :param height: Height  ~ [0, doc_height]
        :param spatial_object: Some object with width and height attributes (i.e: Document, ConvertibleImage).
        :return: BoundingBox object in denormalized coordinates:  ~ [0, doc_height] x [0, doc_width]
        """
        return BoundingBox(x, y, width, height, spatial_object)

    @classmethod
    def from_denormalized_corners(
        cls,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        spatial_object: SpatialObject = None,
    ):
        """
        Builds an axis aligned bounding box from top-left and bottom-right coordinates.
        The coordinates are assumed to be denormalized.
        :param x1: Left  ~ [0, wdoc_idth]
        :param y1: Top ~ [0, doc_height]
        :param x2: Right  ~ [0, doc_width]
        :param y2: Bottom ~ [0, doc_height]
        :param spatial_object: Some object with width and height attributes (i.e: Document, ConvertibleImage).
        :return: BoundingBox object in denormalized coordinates:  ~ [0, doc_height] x [0, doc_width]
        """
        x = x1
        y = y1
        width = x2 - x1
        height = y2 - y1
        return BoundingBox(x, y, width, height, spatial_object=spatial_object)

    @classmethod
    def from_denormalized_borders(
        cls,
        left: float,
        top: float,
        right: float,
        bottom: float,
        spatial_object: SpatialObject = None,
    ):
        """
        Builds an axis aligned bounding box from top-left and bottom-right coordinates.
        The coordinates are assumed to be denormalized.
        If spatial_object is not None, the coordinates will be denormalized according to the spatial object.
        :param left: ~ [0, doc_width]
        :param top: ~ [0, doc_height]
        :param right: ~ [0, doc_width]
        :param bottom: ~ [0, doc_height]
        :param spatial_object: Some object with width and height attributes
        :return: BoundingBox object in denormalized coordinates:  ~ [0, doc_height] x [0, doc_width]
        """
        return cls.from_denormalized_corners(left, top, right, bottom, spatial_object)

    @classmethod
    def from_denormalized_dict(cls, bbox_dict: Dict[str, float]):
        """
        Builds an axis aligned bounding box from a dictionary of:
        {'x': x, 'y': y, 'width': width, 'height': height}
        The coordinates will be denormalized according to the spatial object.
        :param bbox_dict: {'x': x, 'y': y, 'width': width, 'height': height} of [0, doc_height] x [0, doc_width]
        :param spatial_object: Some object with width and height attributes
        :return: BoundingBox object in denormalized coordinates:  ~ [0, doc_height] x [0, doc_width]
        """
        x = bbox_dict["x"]
        y = bbox_dict["y"]
        width = bbox_dict["width"]
        height = bbox_dict["height"]
        return BoundingBox(x, y, width, height)

    @classmethod
    def enclosing_bbox(cls, bboxes, spatial_object: SpatialObject = None):
        """
        :param bboxes [BoundingBox]: list of bounding boxes
        :param spatial_object SpatialObject: spatial object to be added to the returned bbox
        :return:
        """
        bboxes = [bbox for bbox in bboxes if bbox is not None]
        if bboxes and not isinstance(bboxes[0], BoundingBox):
            try:
                bboxes = [bbox.bbox for bbox in bboxes]
            except:
                raise Exception(
                    "bboxes must be of type List[BoundingBox] or of type List[DocumentEntity]"
                )

        x1, y1, x2, y2 = float("inf"), float("inf"), float("-inf"), float("-inf")\
        
        # FIXME: This should not happen
        if not any([bbox is not None for bbox in bboxes]):
            logging.warning("At least one bounding box needs to be non-null")
            return BoundingBox(0, 0, 1, 1, spatial_object=spatial_object)            
        
        if spatial_object is None:
            spatial_object = bboxes[0].spatial_object

        for bbox in bboxes:
            if bbox is not None:
                x1 = min(x1, bbox.x)
                x2 = max(x2, bbox.x + bbox.width)
                y1 = min(y1, bbox.y)
                y2 = max(y2, bbox.y + bbox.height)
        return BoundingBox(x1, y1, x2 - x1, y2 - y1, spatial_object=spatial_object)

    @classmethod
    def is_inside(cls, bbox_a, bbox_b):
        """Returns true if Bounding Box A is within Bounding Box B
        """
        return (
            bbox_a.x >= bbox_b.x and
            (bbox_a.x + bbox_a.width) <= (bbox_b.x + bbox_b.width) and
            bbox_a.y >= bbox_b.y and
            (bbox_a.y + bbox_a.height) <= (bbox_b.y + bbox_b.height)
        )

    @classmethod
    def center_is_inside(cls, bbox_a, bbox_b):
        """Returns true if the center point of Bounding Box A is within Bounding Box B
        """
        return (
            (bbox_a.x + bbox_a.width / 2) >= bbox_b.x and
            (bbox_a.x + bbox_a.width / 2) <= (bbox_b.x + bbox_b.width) and
            (bbox_a.y + bbox_a.height / 2) >= bbox_b.y and
            (bbox_a.y + bbox_a.height / 2) <= (bbox_b.y + bbox_b.height)
        )

    @property
    def area(self):
        """
        Returns the area of the bounding box, handles negative bboxes as 0-area

        :return: Bounding box area
        :rtype: float
        """
        if self.width < 0 or self.height < 0:
            return 0
        else:
            return self.width * self.height

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
        # if spatial_object is not None:
        #    x, y, width, height = cls._denormalize(x, y, width, height, spatial_object)
        # else:
        #    spatial_object = None
        return BoundingBox(x, y, width, height, spatial_object)

    def as_denormalized_numpy(self):
        """
        :return: Returns denormalized co-ordinates x, y and dimensions width, height as numpy array.
        :rtype: numpy.array
        """
        return np.array([self.x, self.y, self.width, self.height])

    def get_intersection(self, bbox):
        """
        Returns the intersection of this object's bbox and another BoundingBox
        :return: a BoundingBox object
        """
        assert isinstance(bbox, BoundingBox)
        x1y1x2y2 = (
            max(self.x, bbox.x),
            max(self.y, bbox.y),
            min(self.x + self.width, bbox.x + bbox.width),
            min(self.y + self.height, bbox.y + bbox.height),
        )
        return BoundingBox.from_denormalized_corners(
            *x1y1x2y2, spatial_object=self.spatial_object
        )

    def get_distance(self, bbox):
        """
        Returns the distance between the center point of the bounding box and another bounding box

        :return: Returns the distance as float
        :rtype: float
        """
        return math.sqrt(
            ((self.x + self.width / 2) - (bbox.x + bbox.width / 2)) ** 2
            + ((self.y + self.height / 2) - (bbox.y + bbox.height / 2)) ** 2
        )

    def __repr__(self):
        return f"x: {self.x}, y: {self.y}, width: {self.width}, height: {self.height}"
