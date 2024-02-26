"""
Represents a single :class:`TableTitle:class:` object. The `TableCell:class:` object contains information such as:

* The position of the title within the Document
* The words that it contains
* Confidence of entity detection
"""

from typing import List
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.word import Word
from textractor.utils.text_utils import linearize_children
from textractor.visualizers.entitylist import EntityList


class TableTitle(DocumentEntity):
    """
    Represents a title that is either in-table or floating
    """

    def __init__(
        self,
        entity_id: str,
        bbox: BoundingBox,
    ):
        super().__init__(entity_id, bbox)
        self._words: List[Word] = []
        self._is_floating: bool = False
        self._page = None
        self._page_id = None

    @property
    def words(self):
        """
        Returns all the Word objects present in the :class:`TableTitle`.

        :return words: List of Word objects, each representing a word within the TableTitle.
        :rtype: list
        """
        return EntityList(self._words)

    @words.setter
    def words(self, words: List[Word]):
        """
        Add Word objects to the :class:`TableTitle`.

        :param words: List of Word objects, each representing a word within the TableTitle. No specific ordering is assumed as it is ordered internally.
        :type words: list
        """
        self._words = words

    @property
    def text(self) -> str:
        """Returns the text in the title as one space-separated string

        :return: Text in the title
        :rtype: str
        """
        return " ".join([w.text for w in self.words])

    @property
    def page(self):
        """
        :return: Returns the page number of the page the TableTitle entity is present in.
        :rtype: int
        """

        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the TableTitle entity.

        :param page_num: Page number where the TableTitle entity exists.
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
        Sets the Page ID of the TableTitle entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """

        self._page_id = page_id

    @property
    def is_floating(self) -> bool:
        """
        :return: Returns whether the TableTitle entity is floating or not.
        :rtype: bool
        """

        return self._is_floating

    @is_floating.setter
    def is_floating(self, is_floating: bool):
        """
        Sets the is_floating attribute of the TableTitle entity.

        :param is_floating: Whether the title is floating (not in-table) or not (in-table).
        :type is_floating: bool
        """

        self._is_floating = is_floating

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        text, words = linearize_children(self.words, config=config)
        return text, words
