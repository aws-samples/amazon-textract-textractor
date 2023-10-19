"""
Represents a single :class:`TableFooter:class:` object. The `TableCell:class:` object contains information such as:

* The position of the footer within the Document
* The words that it contains
* Confidence of entity detection
"""

from typing import List
from textractor.data.text_linearization_config import TextLinearizationConfig
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.entities.word import Word
from textractor.visualizers.entitylist import EntityList


class TableFooter(DocumentEntity):
    """
    Represents a footer that is either in-table or floating
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
        Returns all the Word objects present in the :class:`TableFooter`.

        :return words: List of Word objects, each representing a word within the TableFooter.
        :rtype: list
        """
        return EntityList(self._words)

    @words.setter
    def words(self, words: List[Word]):
        """
        Add Word objects to the :class:`TableFooter`.

        :param words: List of Word objects, each representing a word within the TableFooter. No specific ordering is assumed as it is ordered internally.
        :type words: list
        """
        self._words = words

    @property
    def text(self) -> str:
        """Returns the text in the footer as one space-separated string

        :return: Text in the footer
        :rtype: str
        """
        return " ".join([w.text for w in self.words])

    @property
    def page(self):
        """
        :return: Returns the page number of the page the TableFooter entity is present in.
        :rtype: int
        """

        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the TableFooter entity.

        :param page_num: Page number where the TableFooter entity exists.
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
        Sets the Page ID of the TableFooter entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """

        self._page_id = page_id

    def get_text_and_words(
        self, config: TextLinearizationConfig = TextLinearizationConfig()
    ):
        return " ".join(self.words), self.words
