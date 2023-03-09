"""
Represents a single :class:`Line` Entity within the :class:`Document`. 
The Textract API response returns groups of words as LINE BlockTypes. They contain :class:`Word` entities as children. 

This class contains the associated metadata with the :class:`Line` entity including the entity ID, 
bounding box information, child words, page number, Page ID and confidence of detection.
"""

import logging
from typing import List

from textractor.entities.bbox import BoundingBox
from textractor.entities.page import Page
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
        page: Page,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox, page)
        self.confidence = confidence / 100
