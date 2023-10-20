""":class:`DocumentEntity` is the class that all Document entities such as :class:`Word`, :class:`Line`, :class:`Table` etc. inherit from. This class provides methods 
useful to all such entities."""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from textractor.entities.bbox import BoundingBox
from textractor.visualizers.entitylist import EntityList
from textractor.data.text_linearization_config import TextLinearizationConfig


class DocumentEntity(ABC):
    """
    An interface for all document entities within the document body, composing the
    hierarchy of the document object model.
    The purpose of this class is to define properties common to all document entities
    i.e. unique id and bounding box.
    """

    def __init__(self, entity_id: str, bbox: BoundingBox):
        """
        Initialize the common properties to DocumentEntities. Additionally, it contains information about
        child entities within a document entity.

        :param entity_id: Unique identifier of the document entity.
        :param bbox: Bounding box of the entity
        """
        self.id = entity_id
        self._bbox: BoundingBox = bbox
        self.metadata = {}  # Holds optional information about the entity
        self._children = []
        self._children_type = None
        self._raw_object = None

    def add_children(self, children):
        """
        Adds children to all entities that have parent-child relationships.

        :param children: List of child entities.
        :type children: list
        """
        self._children.extend(children)

    @property
    def raw_object(self) -> Dict:
        """
        :return: Returns the raw dictionary object that was used to create this Python object
        :rtype: Dict
        """
        return self._raw_object

    @raw_object.setter
    def raw_object(self, raw_object: Dict):
        """
        Sets the raw object that was used to create this Python object
        :param raw_object: raw object dictionary from the response
        :type raw_object: Dict
        """
        self._raw_object = raw_object

    @property
    def x(self) -> float:
        """
        :return: Returns x coordinate for bounding box
        :rtype: float
        """
        return self._bbox.x

    @x.setter
    def x(self, x: float):
        """
        Sets x coordinate for bounding box

        :param x: x coordinate of the bounding box
        :type x: float
        """
        self._bbox.x = x

    @property
    def y(self) -> float:
        """
        :return: Returns y coordinate for bounding box
        :rtype: float
        """
        return self._bbox.y

    @y.setter
    def y(self, y: float):
        """
        Sets y coordinate for bounding box.

        :param y: y coordinate of the bounding box
        :type y: float
        """
        self._bbox.y = y

    @property
    def width(self) -> float:
        """
        :return: Returns width for bounding box
        :rtype: float
        """
        return self._bbox.width

    @width.setter
    def width(self, width: float):
        """
        Sets width for bounding box.

        :param width: width of the bounding box
        :type width: float
        """
        self._bbox.width = width

    @property
    def height(self) -> float:
        """
        :return: Returns height for bounding box
        :rtype: float
        """
        return self._bbox.height

    @height.setter
    def height(self, height: float):
        """
        Sets height for bounding box.

        :param height: height of the bounding box
        :type height: float
        """
        self._bbox.height = height

    @property
    def bbox(self) -> BoundingBox:
        """
        :return: Returns entire bounding box of entity
        :rtype: BoundingBox
        """
        return self._bbox

    @bbox.setter
    def bbox(self, bbox: BoundingBox):
        self._bbox = bbox

    @property
    def children(self):
        """
        :return: Returns children of entity
        :rtype: list
        """
        return self._children

    def visualize(self, *args, **kwargs) -> EntityList:
        """
        Returns the object's children in a visualization EntityList object

        :return: Returns an EntityList object
        :rtype: EntityList
        """
        return EntityList(self).visualize(*args, **kwargs)

    @abstractmethod
    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ) -> Tuple[str, List]:
        """
        Used for linearization, returns the linearized text of the entity and the matching words

        :return: Tuple of text and word list
        :rtype: Tuple[str, List[Word]]
        """
        pass
