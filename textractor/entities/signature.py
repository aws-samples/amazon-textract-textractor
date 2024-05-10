"""
Represents a single :class:`Signature` Entity within the :class:`Document`. 
The Textract API response returns signatures as SIGNATURE BlockTypes.

This class contains the associated metadata with the :class:`Signature` entity including the entity ID, 
bounding box information, page number, Page ID and confidence of detection.
"""

import logging
from typing import List
import uuid
from textractor.data.text_linearization_config import TextLinearizationConfig

from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.line import Line
from textractor.entities.word import Word


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
        self._confidence = confidence / 100
        self._page = None
        self._page_id = None

    @property
    def page(self):
        """
        :return: Returns the page number of the page the :class:`Signature` entity is present in.
        :rtype: int
        """
        return self._page

    @property
    def words(self):
        """
        :return: Returns an empty list
        :rtype: list
        """
        return []

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`Signature` entity.

        :param page_num: Page number where the :class:`Signature` entity exists.
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

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        w = Word(
            entity_id=str(uuid.uuid4()), bbox=self.bbox, text=config.signature_token
        )
        w.line = Line(entity_id=str(uuid.uuid4()), bbox=self.bbox, words=[w])
        return config.signature_token, [w]
