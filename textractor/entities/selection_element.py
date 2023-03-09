"""
Represents a single :class:`SelectionElement`/Checkbox/Clickable Entity within the :class:`Document`.

This class contains the associated metadata with the :class:`SelectionElement` entity including the entity ID, 
bounding box information, selection status, page number, Page ID and confidence of detection.
"""

from typing import List
from textractor.entities.value import Value
from textractor.entities.word import Word
from textractor.entities.bbox import BoundingBox
from textractor.entities.page import Page
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
        page: Page,
        status: SelectionStatus,
        confidence: float = 0,
    ):

        super().__init__(entity_id, bbox, page)
        self.key_id = None
        self.value_id = None
        self.status = status
        self.confidence = confidence / 100

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

    def __repr__(self) -> str:
        """
        Returns string representation of SelectionElement.
        """
        if self.status == SelectionStatus.SELECTED:
            return "[X]"
        else:
            return "[ ]"
