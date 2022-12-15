"""
Represents a single :class:`Line` Entity within the :class:`Document`. 
The Textract API response returns groups of words as LINE BlockTypes. They contain :class:`Word` entities as children. 

This class contains the associated metadata with the :class:`Line` entity including the entity ID, 
bounding box information, child words, page number, Page ID and confidence of detection.
"""

import logging
from typing import List

from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity


class Signature(DocumentEntity):
    """
    To create a new :class:`Signature` object we need the following:

    :param entity_id: Unique identifier of the signature entity.
    :type entity_id: str
    :param bbox: Bounding box of the signature entity.
    :type bbox: BoundingBox
    :param words: List of the Word entities present in the signature
    :type words: list, optional
    :param confidence: confidence with which the entity was detected.
    :type confidence: float, optional
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox)
        self.confidence = confidence / 100
        self._page = None
        self._page_id = None

    @property
    def page(self):
        """
        :return: Returns the page number of the page the :class:`Signature` entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the Signature entity.

        :param page_num: Page number where the Signature entity exists.
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
        Sets the Page ID of the :class:`Signature` entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id
