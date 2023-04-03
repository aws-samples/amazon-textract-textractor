"""
Represents a single :class:`Line` Entity within the :class:`Document`. 
The Textract API response returns groups of words as LINE BlockTypes. They contain :class:`Word` entities as children. 

This class contains the associated metadata with the :class:`Line` entity including the entity ID, 
bounding box information, child words, page number, Page ID and confidence of detection.
"""

import logging
from typing import List

from textractor.entities.word import Word
from textractor.entities.page import Page
from textractor.data.constants import TextTypes
from textractor.entities.bbox import BoundingBox
from textractor.exceptions import InputError
from textractor.entities.document_entity import DocumentEntity
from textractor.visualizers.entitylist import EntityList


class Line(DocumentEntity):
    """
    To create a new :class:`Line` object we need the following:

    :param entity_id: Unique identifier of the Line entity.
    :type entity_id: str
    :param bbox: Bounding box of the line entity.
    :type bbox: BoundingBox
    :param words: List of the Word entities present in the line
    :type words: list, optional
    :param confidence: confidence with which the entity was detected.
    :type confidence: float, optional
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        page: Page,
        words: List[Word] = None,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox, page)
        if words is not None and len(words) > 0:
            self.words: List[Word] = sorted(words, key=lambda x: x.bbox.y + x.bbox.x)
        else:
            self.words = []

        self.confidence = confidence / 100

    @property
    def text(self):
        """
        :return: Returns the text transcription of the :class:`Line` entity.
        :rtype: str
        """
        return " ".join([word.text for word in self.words])

    def get_words_by_type(self, text_type: TextTypes = TextTypes.PRINTED) -> List[Word]:
        """
        :param text_type: TextTypes.PRINTED or TextTypes.HANDWRITING
        :type text_type: TextTypes
        :return: Returns EntityList of Word entities that match the input text type.
        :rtype: EntityList[Word]
        """
        if not isinstance(text_type, TextTypes):
            raise InputError(
                "text_type parameter should be of TextTypes type. Find input choices from textractor.data.constants"
            )

        if not self.words:
            logging.info("Document contains no word entities.")
            return []
        return EntityList([word for word in self.words if word.text_type == text_type])

    def __repr__(self):
        """
        :return: String representation of the Line entity.
        :rtype: str
        """
        return " ".join([word.text for word in self.words])
