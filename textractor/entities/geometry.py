"""Geometry class contains all the co-ordinate information for a :class:`DocumentEntity`. This class is mainly useful to locate the entity
on the image of the document page."""

import math
from abc import ABC
from typing import Tuple

try:
    import numpy as np
except ImportError:
    # Used in an export_as_numpy function which won't be called if the user doesn't have numpy.
    pass

from typing import List, Dict, Any


class SpatialObject(ABC):
    """
    The :class:`SpatialObject` interface defines an object that has a width and height. This mostly used for :class:`Geometry` \
    reference to be able to provide normalized coordinates.
    """

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height


class Geometry:
    """
    Represents the geometry an object. Supports .as_xywh_bbox(), .as_xyxy_bbox() and .as_polygon() \\
    """

    def __init__(
        self, geometry: Dict[str, Any], spatial_object=None
    ):
        self.spatial_object = spatial_object
        self._geometry = geometry
        self._points = [
            (p["X"], p["Y"])
            for p in self._geometry["Polygon"]
        ]
        self._bbox = (
            self._geometry["BoundingBox"]["Left"],
            self._geometry["BoundingBox"]["Top"],
            self._geometry["BoundingBox"]["Width"],
            self._geometry["BoundingBox"]["Height"],
        )
        
    @property
    def x(self) -> float:
        return self._bbox[0]

    @property
    def y(self) -> float:
        return self._bbox[1]

    @property
    def width(self) -> float:
        return self._bbox[2]

    @property
    def height(self) -> float:
        return self._bbox[3]

    def _angle_between_two_points(self, p1, p2):
        return math.degrees(math.atan2(p2[0] - p1[0], p2[1] - p1[1]))

    def orientation(self) -> float:
        """Returns the estimated orientation from the first two polygon points
        This is NOT something to be relied on for production. It is only used for
        visualizations.

        :return: Angle between the two first points in the polygon
        :rtype: float
        """
        angles = []
        for i in range(0, len(self._points) - 1):
            angles.append(self._angle_between_two_points(self._points[i+1], self._points[i]) % 90)
        angles.append(self._angle_between_two_points(self._points[0], self._points[-1]) % 90)

        return sum(angles) / len(angles)

    def as_xywh_bbox(self):
        """Returns the entity boundaries as an xywh bounding box

        :return: 4-value tuple (x, y, w, h)
        :rtype: Tuple[float]
        """
        return self._bbox

    def as_xyxy_bbox(self):
        """Returns the entity boundaries as an xyxy bounding box

        :return: 4-value tuple (x1, y1, x2, y2)
        :rtype: Tuple[float]
        """
        return (
            self._bbox[0],
            self._bbox[1],
            self._bbox[0] + self._bbox[2],
            self._bbox[1] + self._bbox[3],
        )

    def as_polygon(self):
        """Returns the entity boundaries as a list of points (polygon)

        :return: List of (x, y) tuples 
        :rtype: List[Tuple[float, float]]
        """
        return self._points

    def __repr__(self):
        return f"Entity boundaries {self._points}"
