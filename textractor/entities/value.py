"""
Represents a single :class:`Value` Entity within the :class:`Document`. 
The Textract API response returns groups of words as KEY_VALUE_SET BlockTypes. These may be of KEY
or VALUE type which is indicated by the EntityType attribute in the JSON response. 

This class contains the associated metadata with the :class:`Value` entity including the entity ID, 
bounding box information, child words, associated key ID, page number, Page ID, confidence of detection
and if it's a checkbox.
"""

from typing import List

from textractor.entities.word import Word
from textractor.exceptions import InputError
from textractor.entities.bbox import BoundingBox
from textractor.entities.document_entity import DocumentEntity
from textractor.data.constants import PRINTED, HANDWRITING, TextTypes
from textractor.visualizers.entitylist import EntityList


class Value(DocumentEntity):
    """
    To create a new :class:`Value` object we need the following:

    :param entity_id: Unique identifier of the Word entity.
    :type entity_id: str
    :param bbox: Bounding box of the Word entity.
    :type bbox: BoundingBox
    :param confidence: value storing the confidence of detection out of 100.
    :type confidence: float
    """

    def __init__(self, entity_id: str, bbox: BoundingBox, confidence: float = 0):
        super().__init__(entity_id, bbox)
        self._words: List[Word] = []
        self._key_id = None
        self._contains_checkbox = False
        self.confidence = confidence / 100
        self._page = None
        self._page_id = None

    @property
    def words(self) -> List[Word]:
        """
        :return: Returns a list of all words in the entity if it exists else returns the
                 checkbox status of the Value entity.
        :rtype: EntityList[Word]
        """
        if not self.contains_checkbox:
            return EntityList(self._words)
        else:
            return self.children[0].words

    @words.setter
    def words(self, words: List[Word]):
        """
        Add Word objects to the Value.

        :param words: List of Word objects, each representing a word within the Value field.
        No specific ordering is assumed as is it is ordered internally.
        :type words: list
        """
        self._words = sorted(words, key=lambda x: x.bbox.x + x.bbox.y)

    @property
    def key_id(self) -> str:
        """
        Returns the associated Key ID for the :class:`Value` entity.

        :return: Returns the associated KeyValue object ID.
        :rtype: str
        """
        return self._key_id

    @key_id.setter
    def key_id(self, key_id: str):
        """
        Sets the :class:`KeyValue` ID to which this Value object is associated.

        :param key_id: Unique identifier for the KeyValue entity to which this Value is associated.
        :type key_id: str
        """
        self._key_id = key_id

    @property
    def contains_checkbox(self) -> bool:
        """
        Returns True if the value associated is a :class:`SelectionElement`.

        :return: Returns True if the value associated is a checkbox/SelectionElement.
        :rtype: bool
        """
        return self._contains_checkbox

    @contains_checkbox.setter
    def contains_checkbox(self, checkbox_present: bool):
        """
        Sets the contains_checkbox field to True/False depending on the presence of a :class:`SelectionElement`.

        :param checkbox_present: True or False depending on checkbox presence.
        :type checkbox_present: bool
        """
        self._contains_checkbox = checkbox_present

    @property
    def page(self):
        """
        :return: Returns the page number of the page the Value entity is present in.
        :rtype: int
        """
        return self._page

    @page.setter
    def page(self, page_num: int):
        """
        Sets the page number attribute of the Value entity.

        :param page_num: Page number where the Value entity exists.
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
        Sets the Page ID of the :class:`Value` entity.

        :param page_id: Page ID of the page the entity belongs to.
        :type page_id: str
        """
        self._page_id = page_id

    def get_words_by_type(self, text_type: str = TextTypes.PRINTED) -> List[Word]:
        """
        Returns list of :class:`Word` entities that match the input text type.

        :param text_type: TextTypes.PRINTED or TextTypes.HANDWRITING
        :type text_type: TextTypes

        :return: Returns list of Word entities that match the input text type.
        :rtype: EntityList[Word]
        """
        if not isinstance(text_type, TextTypes):
            raise InputError(
                "text_type parameter should be of TextTypes type. Find input choices from textractor.data.constants"
            )

        return EntityList([word for word in self.words if word.text_type == text_type])

    def __repr__(self) -> str:
        """
        :return: String representation of the Value entity.
        :rtype: str
        """
        repr_string = ""
        if self.contains_checkbox:
            repr_string += f"{self.children[0].__repr__()}"
        else:
            words = " ".join([word.text for word in self.words])
            repr_string += f"{words}"
        return repr_string
