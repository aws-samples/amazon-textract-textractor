"""
Represents a single :class:`SelectionElement`/Checkbox/Clickable Entity within the :class:`Document`.

This class contains the associated metadata with the :class:`SelectionElement` entity including the entity ID, 
bounding box information, selection status, page number, Page ID and confidence of detection.
"""

from typing import List
from textractor.entities.value import Value
from textractor.entities.word import Word
from textractor.entities.bbox import BoundingBox
from textractor.data.constants import SELECTED, NOT_SELECTED, SelectionStatus
from textractor.entities.document_entity import DocumentEntity


class SelectionElement(Value):
    """
    To create a new :class:`SelectionElement` object we need the following:

    :param entity_id: Unique identifier of the SelectionElement entity.
    :type entity_id: str
    :param bbox: Bounding box of the SelectionElement
    :type bbox: BoundingBox
    :param status: SelectionStatus.SELECTED / SelectionStatus.NOT_SELECTED
    :type status: SelectionStatus
    :param confidence: Confidence with which this entity is detected.
    :type confidence: float
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        status: SelectionStatus,
        confidence: float = 0,
    ):

        super().__init__(entity_id, bbox)
        self.key_id = None
        self.value_id = None
        self.status = status
        self.confidence = confidence / 100
        self._page = None
        self._page_id = None

    def is_selected(self) -> bool:
        """
        :return: Returns True / False depending on selection status of the SelectionElement.
        :rtype: bool
        """
        return self.status == SelectionStatus.SELECTED

    @property
    def words(self) -> List[Word]:
        """
        :return: On SelectionElement this should always return an empty list
        :rtype: EntityList[Word]
        """
        return []

    @property
    def page(self):
        """
        :return: Returns the page number of the page the SelectionElement entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the SelectionElement entity.

        :param page_num: Page number where the SelectionElement entity exists.
        :type page_num: int
        """
        self._page = page_num

    @property
    def page_id(self) -> str:
        """
        :return: Returns the Page ID attribute of the page which the entity belongs to.
        :rtype: str
        """
        return self._page_id

    @page_id.setter
    def page_id(self, page_id: str):
        """
        Sets the Page ID of the SelectionElement entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    def __repr__(self) -> str:
        """
        Returns string representation of SelectionElement.
        """
        if self.status == SelectionStatus.SELECTED:
            return "[X]"
        else:
            return "[ ]"
