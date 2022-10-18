"""
The :class:`KeyValue` entity is a document entity representing the Forms output. The key in :class:`KeyValue` are typically words 
and the :class:`Value` could be :class:`Word` elements or :class:`SelectionElement` in case of checkboxes.

This class contains the associated metadata with the :class:`KeyValue` entity including the entity ID, 
bounding box information, value, existence of checkbox, page number, Page ID and confidence of detection.
"""

from typing import Optional

from textractor.entities.query_result import QueryResult
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity


class Query(DocumentEntity):
    """
    The Query object merges QUERY and QUERY_RESULT blocks.
    To create a new :class:`Query` object we require the following:

    :param entity_id: Unique identifier of the Query entity.
    :type entity_id: str
    :param bbox: Bounding box of the KeyValue entity.
    :type bbox: BoundingBox
    :param contains_checkbox: True/False to indicate if the value is a checkbox.
    :type contains_checkbox: bool
    :param value: Value object that maps to the KeyValue entity.
    :type value: Value
    :param confidence: confidence with which the entity was detected.
    :type confidence: float
    """

    def __init__(
        self,
        entity_id: str,
        query: str,
        alias: str,
        query_result: Optional[QueryResult],
        result_bbox: Optional[BoundingBox],
    ):
        super().__init__(entity_id, result_bbox)

        self.query = query
        self.alias = alias
        self.result = query_result
        self._page = None
        self._page_id = None

    @property
    def page(self) -> int:
        """
        :return: Returns the page number of the page the :class:`Table` entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`Table` entity.

        :param page_num: Page number where the Table entity exists.
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
        Sets the Page ID of the :class:`Table` entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    @property
    def has_result(self) -> bool:
        """
        :return: Returns whether there was a result associated with the query
        :rtype: bool
        """
        return self.result is not None

    def __repr__(self) -> str:
        """
        :return: Returns Query object as a formatted string.
        :rtype: str
        """

        if self.result:
            return f"{self.query} {self.result.answer}"
        else:
            return f"{self.query}"
