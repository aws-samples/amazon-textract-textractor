"""
Represents a single :class:`Word` within the :class:`Document`.
This class contains the associated metadata with the :class:`Word` entity including the text transcription, 
text type, bounding box information, page number, Page ID and confidence of detection.
"""

from textractor.data.constants import TextTypes
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity


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
        text: str = "",
        text_type: TextTypes = TextTypes.PRINTED,
        confidence: float = 0,
        is_clickable: bool = False,
        is_structure: bool = False,
    ):
        super().__init__(entity_id, bbox)
        self._text = text
        self._text_type = text_type
        self.confidence = confidence / 100
        self.is_clickable = is_clickable
        self.is_structure = is_structure
        self._page = None
        self._page_id = None
        self.line = None
        self.cell_bbox = None
        self.cell_id = None
        self.row_index = None
        self.col_index = None
        self.row_span = None
        self.col_span = None
        self.key_bbox = None
        self.value_bbox = None
        self.key_id = None
        self.value_id = None
        self.kv_id = None
        self.kv_bbox = None
        self.line_id = None
        self.line_bbox = None
        self.table_id = None
        self.table_bbox = None
        self.layout_id = None
        self.layout_type = None
        self.layout_bbox = None

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

    @property
    def page(self) -> int:
        """
        :return: Returns the page number of the page the Word entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the :class:`Word` entity.

        :param page_num: Page number where the Word entity exists.
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
        Sets the Page ID of the Word entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    @property
    def words(self):
        """Returns itself

        :rtype: Word
        """
        return [self]

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        return self.text, [self]

    def __repr__(self) -> str:
        """
        :return: String representation of the Word entity.
        :rtype: str
        """
        return f"{self.text}"
