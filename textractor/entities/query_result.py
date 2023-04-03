"""
The :class:`KeyValue` entity is a document entity representing the Forms output. The key in :class:`KeyValue` are typically words 
and the :class:`Value` could be :class:`Word` elements or :class:`SelectionElement` in case of checkboxes.

This class contains the associated metadata with the :class:`KeyValue` entity including the entity ID, 
bounding box information, value, existence of checkbox, page number, Page ID and confidence of detection.
"""

from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.page import Page


class QueryResult(DocumentEntity):
    """
    The QueryResult object represents QUERY_RESULT blocks.
    To create a new :class:`QueryResult` object we require the following:

    :param entity_id: Unique identifier of the Query entity.
    :type entity_id: str
    :param bbox: Bounding box of the QueryResult entity.
    :type bbox: BoundingBox
    :param contains_checkbox: True/False to indicate if the value is a checkbox.
    :type contains_checkbox: bool
    :param value: Value object that maps to the QueryResult entity.
    :type value: Value
    :param confidence: confidence with which the entity was detected.
    :type confidence: float
    """

    def __init__(
        self,
        entity_id: str,
        confidence: float,
        result_bbox: BoundingBox,
        answer: str,
        page: Page,
    ):
        super().__init__(entity_id, result_bbox, page)

        self.answer = answer
        self.confidence = confidence / 100

    def __repr__(self) -> str:
        """
        :return: Returns Query object as a formatted string.
        :rtype: str
        """

        return f"{self.answer}"
