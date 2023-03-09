"""
Represents a single :class:`Word` within the :class:`Document`.
This class contains the associated metadata with the :class:`Word` entity including the text transcription, 
text type, bounding box information, page number, Page ID and confidence of detection.
"""

from textractor.data.constants import TextTypes
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.page import Page


class Word(DocumentEntity):
    """
    To create a new :class:`Word` object we need the following:

    :param entity_id: Unique identifier of the Word entity.
    :type entity_id: str
    :param bbox: Bounding box of the Word entity.
    :type bbox: BoundingBox
    :param text: Transcription of the Word object.
    :type text: str
    :param text_type: Enum value stating the type of text stored in the entity. Takes 2 values - PRINTED and HANDWRITING
    :type text_type: TextTypes
    :param confidence: value storing the confidence of detection out of 100.
    :type confidence: float
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
        page: Page,
        text: str = "",
        text_type: TextTypes = TextTypes.PRINTED,
        confidence: float = 0,
    ):
        super().__init__(entity_id, bbox, page)
        self._text = text
        self._text_type = text_type
        self.confidence = confidence / 100

    @property
    def text(self) -> str:
        """
        :return: Returns the text transcription of the Word entity.
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, text: str):
        """
        Sets the transcription of the :class:`Word` entity.

        :param text: String containing the text transcription of the Word entity.
        :type text: str
        """
        self._text = text

    @property
    def text_type(self) -> TextTypes:
        """
        :return: Returns the property of :class:`Word` class that holds the text type of Word object.
        :rtype: str
        """
        return self._text_type

    @text_type.setter
    def text_type(self, text_type: TextTypes):
        """
        Sets the text type of the :class:`Word` entity.

        :param text_type: Constant containing the type of text
        """
        assert isinstance(text_type, TextTypes)
        self._text_type = text_type

    def __repr__(self) -> str:
        """
        :return: String representation of the Word entity.
        :rtype: str
        """
        return f"{self.text}"
